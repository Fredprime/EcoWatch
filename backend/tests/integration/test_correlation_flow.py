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


def test_a_pair_that_changes_task_stays_one_suggestion(dbSession: Session) -> None:
    """A source reference arriving later reclassifies the row, not adds a second."""
    org = create_temp_org(dbSession)
    first = make_observation(dbSession, org, description="dead fish at the river bend")
    second = make_observation(dbSession, org, description="dead fish at the river bend")

    service = CorrelationService(dbSession)
    assert service.scan_observation(first.id) == 1
    assert dbSession.query(EvidenceRelationship).one().task == CorrelationTask.DUPLICATE.value

    first.sourceRef = "post-42"
    second.sourceRef = "post-42"
    dbSession.commit()

    assert service.scan_observation(first.id) == 1
    rows = dbSession.query(EvidenceRelationship).all()
    assert len(rows) == 1
    assert rows[0].task == CorrelationTask.SOURCE_DEPENDENCY.value
    assert rows[0].sourceIndependent is False


def test_a_decided_pair_is_never_reclassified_by_a_rescan(dbSession: Session) -> None:
    """Reclassification is for open suggestions; a decision stays as recorded."""
    org = create_temp_org(dbSession)
    reviewer = create_temp_user(dbSession, memberships=[(org.id, Role.REVIEWER)])
    first = make_observation(dbSession, org, description="dead fish at the river bend")
    second = make_observation(dbSession, org, description="dead fish at the river bend")

    service = CorrelationService(dbSession)
    service.scan_observation(first.id)
    suggestion = dbSession.query(EvidenceRelationship).one()
    service.decide(
        reviewer_principal(reviewer, org), suggestion.id,
        RelationshipStatus.REJECTED, reason="different river",
    )

    first.sourceRef = "post-42"
    second.sourceRef = "post-42"
    dbSession.commit()
    service.scan_observation(first.id)

    rows = dbSession.query(EvidenceRelationship).all()
    assert len(rows) == 1
    assert rows[0].task == CorrelationTask.DUPLICATE.value
    assert rows[0].status == RelationshipStatus.REJECTED.value


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


def test_reopening_returns_a_decided_pair_to_the_queue(dbSession: Session) -> None:
    org = create_temp_org(dbSession)
    viewer = create_temp_user(dbSession, memberships=[(org.id, Role.REVIEWER)])
    first = make_observation(dbSession, org, description="dead fish at the river bend")
    make_observation(dbSession, org, description="dead fish at the river bend")

    service = CorrelationService(dbSession)
    service.scan_observation(first.id)
    suggestion = dbSession.query(EvidenceRelationship).one()
    principal = reviewer_principal(viewer, org)

    service.decide(principal, suggestion.id, RelationshipStatus.REJECTED, reason="other river")
    assert dbSession.get(EvidenceRelationship, suggestion.id).status == "rejected"

    reopened = service.reopen(principal, suggestion.id, reason="wrong stretch identified")
    assert reopened.status == RelationshipStatus.SUGGESTED.value
    assert reopened.decidedByUserId is None
    assert reopened.decidedAt is None
    assert reopened.decisionReason is None

    # The previous decision is not lost: it is in the append-only audit trail.
    actions = [event.action for event in dbSession.query(AuditEvent).all()]
    assert "correlation.rejected" in actions
    assert "correlation.reopened" in actions

    # And the pair is decidable again, which is the whole point.
    service.decide(principal, suggestion.id, RelationshipStatus.ACCEPTED, reason="same outfall")
    assert dbSession.get(EvidenceRelationship, suggestion.id).status == "accepted"


def test_a_submitter_cannot_reopen_a_decision_on_their_own_report(dbSession: Session) -> None:
    """Separation of duties applies to undoing a decision, not just making one."""
    from ecowatch.core.errors import DomainError, ErrorCode

    org = create_temp_org(dbSession)
    submitter = create_temp_user(dbSession, memberships=[(org.id, Role.REVIEWER)])
    other = create_temp_user(dbSession, memberships=[(org.id, Role.REVIEWER)])
    mine = make_observation(
        dbSession, org, description="dead fish at the river bend", submittedBy=submitter
    )
    make_observation(dbSession, org, description="dead fish at the river bend")

    service = CorrelationService(dbSession)
    service.scan_observation(mine.id)
    suggestion = dbSession.query(EvidenceRelationship).one()
    service.decide(
        reviewer_principal(other, org), suggestion.id,
        RelationshipStatus.REJECTED, reason="different river",
    )

    with pytest.raises(DomainError) as raised:
        service.reopen(
            reviewer_principal(submitter, org), suggestion.id, reason="want another look"
        )
    assert raised.value.code is ErrorCode.SELF_REVIEW_FORBIDDEN
    assert dbSession.get(EvidenceRelationship, suggestion.id).status == "rejected"
    # The refused action wrote no audit event.
    assert [event.action for event in dbSession.query(AuditEvent).all()] == [
        "correlation.rejected"
    ]


def test_reopening_an_open_suggestion_is_refused(dbSession: Session) -> None:
    org = create_temp_org(dbSession)
    viewer = create_temp_user(dbSession, memberships=[(org.id, Role.REVIEWER)])
    first = make_observation(dbSession, org, description="dead fish at the river bend")
    make_observation(dbSession, org, description="dead fish at the river bend")
    CorrelationService(dbSession).scan_observation(first.id)
    suggestion = dbSession.query(EvidenceRelationship).one()

    from ecowatch.core.errors import DomainError, ErrorCode

    with pytest.raises(DomainError) as raised:
        CorrelationService(dbSession).reopen(
            reviewer_principal(viewer, org), suggestion.id, reason="no decision yet"
        )
    assert raised.value.code is ErrorCode.INVALID_STATUS_TRANSITION
    assert raised.value.statusCode == 409


def test_reopen_requires_a_reason_and_permission(
    dbSession: Session, client: TestClient, authProvider
) -> None:
    org = create_temp_org(dbSession)
    reviewer = create_temp_user(dbSession, memberships=[(org.id, Role.REVIEWER)])
    otherOrg = create_temp_org(dbSession, name="Other Org")
    outsider = create_temp_user(dbSession, memberships=[(otherOrg.id, Role.REVIEWER)])
    first = make_observation(dbSession, org, description="dead fish at the river bend")
    make_observation(dbSession, org, description="dead fish at the river bend")

    service = CorrelationService(dbSession)
    service.scan_observation(first.id)
    suggestion = dbSession.query(EvidenceRelationship).one()
    service.decide(
        reviewer_principal(reviewer, org), suggestion.id, RelationshipStatus.REJECTED,
        reason="other river",
    )

    url = f"/api/v1/correlation/suggestions/{suggestion.id}/reopen"
    assert client.post(
        url, json={}, headers=auth_headers(authProvider, reviewer)
    ).status_code == 422
    assert client.post(
        url, json={"reason": "wrong stretch"}, headers=auth_headers(authProvider, outsider)
    ).status_code == 404
    assert client.post(
        url, json={"reason": "wrong stretch"}, headers=auth_headers(authProvider, reviewer)
    ).status_code == 200


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


def test_reports_get_their_own_cluster_and_are_never_auto_merged(
    dbSession: Session,
) -> None:
    """A~B and B~C must not quietly become one cluster of three."""
    org = create_temp_org(dbSession)
    first = make_observation(dbSession, org, description="dead fish at the river bend")
    second = make_observation(dbSession, org, description="dead fish at the river bend")

    service = CorrelationService(dbSession)
    service.scan_observation(first.id)
    service.scan_observation(second.id)

    # They are related by a suggestion, but membership only grows by a human
    # accepting it, so each report still has its own provisional home.
    clusters = service.list_clusters(reviewer_principal(
        create_temp_user(dbSession, memberships=[(org.id, Role.REVIEWER)]), org
    ))
    assert len(clusters) == 2
    assert all(len(observationIds) == 1 for _, observationIds in clusters)


def test_a_report_with_no_match_still_has_a_cluster(dbSession: Session) -> None:
    org = create_temp_org(dbSession)
    only = make_observation(dbSession, org, description="loud generator at the market")

    service = CorrelationService(dbSession)
    assert service.scan_observation(only.id) == 0
    viewer = create_temp_user(dbSession, memberships=[(org.id, Role.REVIEWER)])
    clusters = service.list_clusters(reviewer_principal(viewer, org))
    assert [observationIds for _, observationIds in clusters] == [[only.id]]


def test_a_tie_is_marked_ambiguous_instead_of_silently_ordered(
    dbSession: Session,
) -> None:
    org = create_temp_org(dbSession)
    now = datetime.now(UTC)
    subject = make_observation(dbSession, org, description="brown foam at the weir",
                               observedAt=now - timedelta(hours=1))
    for _ in range(2):
        make_observation(dbSession, org, description="brown foam at the weir",
                         observedAt=now - timedelta(hours=1))

    CorrelationService(dbSession).scan_observation(subject.id)
    rows = dbSession.query(EvidenceRelationship).all()
    assert len(rows) == 2
    assert all(row.ambiguous for row in rows)


def test_clusters_require_authentication_and_stay_in_the_organisation(
    dbSession: Session, client: TestClient, authProvider
) -> None:
    ours = create_temp_org(dbSession, name="Our Org")
    theirs = create_temp_org(dbSession, name="Their Org")
    oursUser = create_temp_user(dbSession, memberships=[(ours.id, Role.REVIEWER)])
    theirsUser = create_temp_user(dbSession, memberships=[(theirs.id, Role.REVIEWER)])
    oursObs = make_observation(dbSession, ours, description="dead fish at the river bend")
    theirsObs = make_observation(dbSession, theirs, description="dead fish at the river bend")
    service = CorrelationService(dbSession)
    service.scan_observation(oursObs.id)
    service.scan_observation(theirsObs.id)

    assert client.get("/api/v1/correlation/clusters").status_code == 401

    for user, expected in ((oursUser, 1), (theirsUser, 1)):
        response = client.get(
            "/api/v1/correlation/clusters", headers=auth_headers(authProvider, user)
        )
        assert response.status_code == 200
        clusters = response.json()
        assert len(clusters) == expected
        assert all(len(item["observationIds"]) == 1 for item in clusters)


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
