"""Phase 2 correlation: scanning, review decisions, and the boundaries between them."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ecowatch.modules.audit.models import AuditEvent
from ecowatch.modules.correlation.models import (
    CorrelationTask,
    EvidenceRelationship,
    RelationshipStatus,
)
from ecowatch.modules.correlation.service import CorrelationService
from ecowatch.modules.identity.models import Organisation, User
from ecowatch.modules.identity.permissions import Principal, Role
from ecowatch.modules.jobs.models import ProcessingJob
from ecowatch.modules.jobs.worker import run_once
from ecowatch.modules.observations.models import Observation
from tests.conftest import auth_headers, create_temp_org, create_temp_user


def make_observation(
    dbSession: Session,
    org: Organisation,
    *,
    observationType: str = "water_pollution",
    description: str = "chemical spill at the weir",
    observedAt: datetime | None = None,
    lat: float | None = 6.6885,
    lon: float | None = -1.6244,
    sourceRef: str | None = None,
    submittedBy: User | None = None,
) -> Observation:
    """Temporary observation with only the fields correlation reads set explicitly."""
    from ecowatch.core.spatial import format_point_wkt

    observation = Observation(
        organisationId=org.id,
        idempotencyKey=uuid.uuid4(),
        payloadHash="0" * 64,
        observationType=observationType,
        sourceType="community_registered",
        description=description,
        sourceRef=sourceRef,
        observedAt=observedAt or datetime.now(UTC) - timedelta(hours=2),
        receivedAt=datetime.now(UTC),
        timePrecision="exact",
        location=(
            format_point_wkt(lon, lat) if lat is not None and lon is not None else None
        ),
        locationPrecision="exact" if lat is not None else "unknown",
        qualityFlags=[],
        accessClass="internal",
        currentVersion=1,
        submittedByUserId=submittedBy.id if submittedBy else None,
    )
    dbSession.add(observation)
    dbSession.commit()
    return observation


def reviewer_principal(user: User, org: Organisation, *, role: Role = Role.REVIEWER) -> Principal:
    return Principal(userId=user.id, memberships=((org.id, role),), isAuthenticated=True)


def test_scan_creates_one_suggestion_and_repeated_scans_do_not_duplicate(
    dbSession: Session,
) -> None:
    org = create_temp_org(dbSession)
    first = make_observation(dbSession, org, description="dead fish at the river bend")
    second = make_observation(dbSession, org, description="dead fish at the river bend")

    service = CorrelationService(dbSession)
    assert service.scan_observation(first.id) == 1
    assert service.scan_observation(first.id) == 1

    rows = dbSession.query(EvidenceRelationship).all()
    assert len(rows) == 1
    suggestion = rows[0]
    assert {suggestion.observationAId, suggestion.observationBId} == {first.id, second.id}
    # canonical ordering: the stored pair is independent of which end was scanned
    assert suggestion.observationAId < suggestion.observationBId
    assert suggestion.status == RelationshipStatus.SUGGESTED.value
    # Identical wording is now classified as a duplicate rather than a vague
    # "same event"; the point of this test is the canonical pair and idempotency.
    assert suggestion.task == CorrelationTask.DUPLICATE.value
    assert suggestion.reasons


def test_time_window_comes_from_the_category(dbSession: Session) -> None:
    """A noise complaint 15h old must not match one a week old; a dump can."""
    org = create_temp_org(dbSession)
    now = datetime.now(UTC)

    noiseRecent = make_observation(
        dbSession, org, observationType="noise", description="generator running all night",
        observedAt=now - timedelta(hours=1),
    )
    make_observation(
        dbSession, org, observationType="noise", description="generator running all night",
        observedAt=now - timedelta(hours=15),
    )
    # noise window is 12h, so the 15h-old neighbour is outside it
    assert CorrelationService(dbSession).scan_observation(noiseRecent.id) == 0

    # A separate organisation, so the noise reports above cannot be candidates
    # here: this half is about the waste window, not about scope.
    wasteOrg = create_temp_org(dbSession, name="Waste Org")
    wasteOld = make_observation(
        dbSession, wasteOrg, observationType="waste",
        description="dumped drums behind the clinic",
        observedAt=now - timedelta(hours=100),
    )
    make_observation(
        dbSession, wasteOrg, observationType="waste",
        description="dumped drums behind the clinic",
        observedAt=now - timedelta(hours=60),
    )
    # waste window is a week, so a 40h gap is still a candidate
    assert CorrelationService(dbSession).scan_observation(wasteOld.id) == 1


def test_a_report_without_a_location_is_still_scanned(dbSession: Session) -> None:
    """No point means no distance test, not a skipped comparison."""
    org = create_temp_org(dbSession)
    now = datetime.now(UTC)
    first = make_observation(
        dbSession, org, description="smoke from the tyre dump", observedAt=now - timedelta(hours=1),
        lat=None, lon=None,
    )
    make_observation(
        dbSession, org, description="smoke from the tyre dump", observedAt=now - timedelta(hours=2),
        lat=None, lon=None,
    )

    assert CorrelationService(dbSession).scan_observation(first.id) == 1
    suggestion = dbSession.query(EvidenceRelationship).one()
    assert any("no location" in signal for signal in suggestion.missingSignals)
    assert "spatial_proximity" not in suggestion.components


def test_candidates_never_cross_organisation_boundaries(dbSession: Session) -> None:
    ours = create_temp_org(dbSession, name="Our Org")
    theirs = create_temp_org(dbSession, name="Their Org")
    subject = make_observation(dbSession, ours, description="dead fish at the river bend")
    make_observation(dbSession, theirs, description="dead fish at the river bend")

    assert CorrelationService(dbSession).scan_observation(subject.id) == 0
    assert dbSession.query(EvidenceRelationship).count() == 0


def test_rejected_pair_is_not_suggested_again(dbSession: Session) -> None:
    org = create_temp_org(dbSession)
    viewer = create_temp_user(dbSession, memberships=[(org.id, Role.REVIEWER)])
    first = make_observation(dbSession, org, description="dead fish at the river bend")
    make_observation(dbSession, org, description="dead fish at the river bend")

    service = CorrelationService(dbSession)
    service.scan_observation(first.id)
    suggestion = dbSession.query(EvidenceRelationship).one()

    service.decide(
        reviewer_principal(viewer, org),
        suggestion.id,
        RelationshipStatus.REJECTED,
        reason="different stretch of river",
    )

    # A rejected pair is a human decision; rescanning must not resurrect it.
    assert service.scan_observation(first.id) == 0
    assert dbSession.query(EvidenceRelationship).count() == 1


def test_decision_is_audited_and_cannot_be_overwritten(dbSession: Session) -> None:
    org = create_temp_org(dbSession)
    viewer = create_temp_user(dbSession, memberships=[(org.id, Role.REVIEWER)])
    first = make_observation(dbSession, org, description="dead fish at the river bend")
    make_observation(dbSession, org, description="dead fish at the river bend")

    service = CorrelationService(dbSession)
    service.scan_observation(first.id)
    suggestion = dbSession.query(EvidenceRelationship).one()
    principal = reviewer_principal(viewer, org)

    decided = service.decide(
        principal, suggestion.id, RelationshipStatus.ACCEPTED, reason="same outfall"
    )
    assert decided.status == RelationshipStatus.ACCEPTED.value
    assert decided.decidedByUserId == viewer.id
    assert decided.decidedAt is not None

    event = dbSession.query(AuditEvent).filter_by(action="correlation.accepted").one()
    assert event.actorUserId == viewer.id
    assert event.targetId == suggestion.id
    assert event.organisationId == org.id

    from ecowatch.core.errors import DomainError

    with pytest.raises(DomainError):
        service.decide(principal, suggestion.id, RelationshipStatus.REJECTED)
    assert dbSession.get(EvidenceRelationship, suggestion.id).status == "accepted"


def test_reviewer_cannot_decide_on_their_own_submission(dbSession: Session) -> None:
    org = create_temp_org(dbSession)
    author = create_temp_user(dbSession, memberships=[(org.id, Role.REVIEWER)])
    first = make_observation(
        dbSession, org, description="dead fish at the river bend", submittedBy=author
    )
    make_observation(dbSession, org, description="dead fish at the river bend")

    service = CorrelationService(dbSession)
    service.scan_observation(first.id)
    suggestion = dbSession.query(EvidenceRelationship).one()

    from ecowatch.core.errors import DomainError, ErrorCode

    with pytest.raises(DomainError) as raised:
        service.decide(
            reviewer_principal(author, org), suggestion.id, RelationshipStatus.ACCEPTED
        )
    assert raised.value.code is ErrorCode.SELF_REVIEW_FORBIDDEN
    assert dbSession.get(EvidenceRelationship, suggestion.id).status == "suggested"


def test_repost_from_the_same_source_is_flagged_as_not_independent(
    dbSession: Session,
) -> None:
    org = create_temp_org(dbSession)
    first = make_observation(
        dbSession, org, description="dead fish at the river bend", sourceRef="post-42"
    )
    make_observation(
        dbSession, org, description="dead fish at the river bend", sourceRef="post-42"
    )

    CorrelationService(dbSession).scan_observation(first.id)
    suggestion = dbSession.query(EvidenceRelationship).one()

    assert suggestion.sourceIndependent is False
    assert any("not independent" in reason for reason in suggestion.reasons)


def test_repost_is_stored_as_source_dependency_not_a_second_witness(
    dbSession: Session,
) -> None:
    org = create_temp_org(dbSession)
    first = make_observation(
        dbSession, org, description="dead fish at the river bend", sourceRef="post-42"
    )
    make_observation(
        dbSession, org, description="dead fish at the river bend", sourceRef="post-42"
    )

    CorrelationService(dbSession).scan_observation(first.id)
    suggestion = dbSession.query(EvidenceRelationship).one()
    assert suggestion.task == CorrelationTask.SOURCE_DEPENDENCY.value
    assert suggestion.sourceIndependent is False
    assert "one account, not two" in suggestion.reasons[0]


def test_near_identical_wording_is_stored_as_a_duplicate(dbSession: Session) -> None:
    org = create_temp_org(dbSession)
    first = make_observation(
        dbSession, org, description="truck dumping waste into the drain at Avenor"
    )
    make_observation(
        dbSession, org, description="truck dumping waste into the drain at Avenor again"
    )

    CorrelationService(dbSession).scan_observation(first.id)
    suggestion = dbSession.query(EvidenceRelationship).one()
    assert suggestion.task == CorrelationTask.DUPLICATE.value
    assert suggestion.sourceIndependent is True
    assert "submitted twice" in suggestion.reasons[0]


def test_unrelated_report_is_not_suggested(dbSession: Session) -> None:
    """Below the review threshold nothing is written, so the queue stays useful."""
    org = create_temp_org(dbSession)
    first = make_observation(dbSession, org, description="loud generator at the market")
    make_observation(
        dbSession, org, description="blocked storm drain on the coast road",
        observationType="flooding", lat=6.9, lon=-1.9,
    )

    assert CorrelationService(dbSession).scan_observation(first.id) == 0
    assert dbSession.query(EvidenceRelationship).count() == 0


def test_scan_endpoint_queues_a_job_and_scoring_is_never_inline(
    dbSession: Session,
    client: TestClient,
    authProvider,
    storageProvider,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    org = create_temp_org(dbSession)
    reviewer = create_temp_user(dbSession, memberships=[(org.id, Role.REVIEWER)])
    first = make_observation(dbSession, org, description="dead fish at the river bend")
    make_observation(dbSession, org, description="dead fish at the river bend")

    # If scoring ran inside the request, this would explode. Intake must not care.
    def boom(*_args, **_kwargs):
        raise AssertionError("scoring ran in the request path; NFR-001 is violated")

    monkeypatch.setattr("ecowatch.modules.correlation.service.rank", boom)

    response = client.post(
        f"/api/v1/correlation/observations/{first.id}/scan",
        headers=auth_headers(authProvider, reviewer),
    )
    assert response.status_code == 202
    jobId = uuid.UUID(response.json()["jobId"])

    job = dbSession.get(ProcessingJob, jobId)
    assert job is not None
    assert job.jobType == "correlation.scan"

    # The queued job is what actually scores, and it does so later.
    monkeypatch.undo()
    assert run_once(dbSession, storageProvider) == 1
    assert dbSession.query(EvidenceRelationship).count() == 1


def test_suggestion_listing_requires_authentication(client: TestClient) -> None:
    assert client.get("/api/v1/correlation/suggestions").status_code == 401


def test_decisions_are_not_visible_across_organisations(dbSession: Session) -> None:
    ours = create_temp_org(dbSession, name="Our Org")
    theirs = create_temp_org(dbSession, name="Their Org")
    outsider = create_temp_user(dbSession, memberships=[(theirs.id, Role.REVIEWER)])
    first = make_observation(dbSession, ours, description="dead fish at the river bend")
    make_observation(dbSession, ours, description="dead fish at the river bend")

    service = CorrelationService(dbSession)
    service.scan_observation(first.id)
    suggestion = dbSession.query(EvidenceRelationship).one()

    from ecowatch.core.errors import DomainError, ErrorCode

    with pytest.raises(DomainError) as raised:
        service.decide(
            reviewer_principal(outsider, theirs),
            suggestion.id,
            RelationshipStatus.REJECTED,
        )
    # 404 rather than 403: existence must not leak across tenants.
    assert raised.value.code is ErrorCode.NOT_FOUND
    assert raised.value.statusCode == 404
