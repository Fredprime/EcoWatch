"""Integration tests for two-key governance gates and admin account lifecycle.

All records are temporary, created inside the isolated test database, and removed
by fixture teardown. No product seed data is used.
"""

import uuid
from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ecowatch.core.security import LocalTokenAuthProvider
from ecowatch.modules.identity.permissions import Role, SystemRole
from ecowatch.modules.interventions.enums import InterventionStatus
from ecowatch.modules.interventions.models import Intervention
from ecowatch.modules.verification.enums import AssessmentStatus, OutcomeConclusion
from ecowatch.modules.verification.models import VerificationAssessment
from tests.conftest import auth_headers, create_temp_org, create_temp_user

NOW = datetime(2026, 11, 20, 9, 0, tzinfo=UTC)


def _principal(
    dbSession: Session,
    authProvider: LocalTokenAuthProvider,
    orgId: uuid.UUID,
    role: Role,
):
    """Create a temporary role holder in one organisation."""
    user = create_temp_user(dbSession, memberships=[(orgId, role)])
    return user, auth_headers(authProvider, user)


def _intervention(
    dbSession: Session,
    orgId: uuid.UUID,
    *,
    leadUserId: uuid.UUID,
    proposerUserId: uuid.UUID,
    status: InterventionStatus = InterventionStatus.PROPOSED,
) -> Intervention:
    """Create a temporary intervention directly in the isolated database."""
    record = Intervention(
        organisationId=orgId,
        caseId=uuid.uuid4(),
        objective="Restore the monitored reach.",
        responsibleOrganisationId=orgId,
        authorisedLeadUserId=leadUserId,
        proposedByUserId=proposerUserId,
        status=status.value,
    )
    dbSession.add(record)
    dbSession.commit()
    return record


def _assessment(
    dbSession: Session,
    orgId: uuid.UUID,
    interventionId: uuid.UUID,
    *,
    conclusion: OutcomeConclusion = OutcomeConclusion.IMPROVEMENT,
    status: AssessmentStatus = AssessmentStatus.FINAL,
    twoKey: bool = True,
) -> VerificationAssessment:
    """Create a temporary assessment with an explicit approval state."""
    evaluationBy = uuid.uuid4() if twoKey else None
    record = VerificationAssessment(
        organisationId=orgId,
        interventionId=interventionId,
        baselineMeasurementIds=[str(uuid.uuid4())],
        followUpMeasurementIds=[str(uuid.uuid4())],
        comparisonMethod="Matched site comparison",
        conclusion=conclusion.value,
        criteriaVersion="criteria-2026-01",
        status=status.value,
        specialistApproverUserId=evaluationBy,
        authorityApproverUserId=uuid.uuid4() if twoKey else None,
    )
    dbSession.add(record)
    dbSession.commit()
    return record


def test_recovery_verification_requires_two_role_qualified_distinct_keys(
    client: TestClient,
    dbSession: Session,
    authProvider: LocalTokenAuthProvider,
) -> None:
    orgId = create_temp_org(dbSession).id
    specialist, specialistHeaders = _principal(
        dbSession, authProvider, orgId, Role.ENVIRONMENTAL_SPECIALIST
    )
    authority, _ = _principal(dbSession, authProvider, orgId, Role.ORGANISATION_ADMIN)
    owner, ownerHeaders = _principal(
        dbSession, authProvider, orgId, Role.ENVIRONMENTAL_SPECIALIST
    )
    intervention = _intervention(
        dbSession, orgId, leadUserId=owner.id, proposerUserId=uuid.uuid4()
    )
    assessment = _assessment(dbSession, orgId, intervention.id)
    path = f"/api/v1/verification/assessments/{assessment.id}/recovery"

    def payload(**overrides: object) -> dict[str, object]:
        return {
            "organisationId": str(orgId),
            "specialistApproverUserId": str(specialist.id),
            "authorityApproverUserId": str(authority.id),
            "criteriaVersion": "criteria-2026-01",
            "criteriaApproved": True,
            "comparisonMethod": "Matched site comparison",
            "uncertaintyDocumented": "95% interval recorded.",
            "confoundersDocumented": "Rainfall considered.",
            "seasonalContextDocumented": "Dry season matched.",
            **overrides,
        }

    sameUser = client.post(path, headers=specialistHeaders, json=payload(
        authorityApproverUserId=str(specialist.id)
    ))
    assert sameUser.status_code == 400, sameUser.text
    assert sameUser.json()["code"] == "RECOVERY_NOT_VERIFIABLE"

    selfNominating = client.post(
        path,
        headers=specialistHeaders,
        json=payload(
            specialistApproverUserId=str(uuid.uuid4()),
            authorityApproverUserId=str(uuid.uuid4()),
        ),
    )
    assert selfNominating.status_code == 403, selfNominating.text
    assert selfNominating.json()["code"] == "FORBIDDEN"

    ownedIntervention = client.post(path, headers=ownerHeaders, json=payload(
        specialistApproverUserId=str(owner.id)
    ))
    assert ownedIntervention.status_code == 400, ownedIntervention.text
    assert ownedIntervention.json()["field"] == "approverUserIds"

    wrongAuthority = client.post(path, headers=specialistHeaders, json=payload(
        authorityApproverUserId=str(specialist.id),
        specialistApproverUserId=str(specialist.id),
    ))
    assert wrongAuthority.status_code == 400, wrongAuthority.text

    accepted = client.post(path, headers=specialistHeaders, json=payload())
    assert accepted.status_code == 200, accepted.text
    body = accepted.json()
    assert body["conclusion"] == "recovery_verified"
    assert body["specialistApproverUserId"] == str(specialist.id)
    assert body["authorityApproverUserId"] == str(authority.id)
    assert body["twoKeyApprovedAt"] is not None


def test_publication_requires_two_distinct_role_qualified_approvers(
    client: TestClient,
    dbSession: Session,
    authProvider: LocalTokenAuthProvider,
) -> None:
    orgId = create_temp_org(dbSession).id
    specialist, specialistHeaders = _principal(
        dbSession, authProvider, orgId, Role.ENVIRONMENTAL_SPECIALIST
    )
    authority, authorityHeaders = _principal(
        dbSession, authProvider, orgId, Role.ORGANISATION_ADMIN
    )
    path = "/api/v1/verification/publications"

    def payload(**overrides: object) -> dict[str, object]:
        return {
            "organisationId": str(orgId),
            "specialistApproverUserId": str(specialist.id),
            "authorityApproverUserId": str(authority.id),
            "publishedText": "Turbidity improved at the monitored site.",
            **overrides,
        }

    sameUser = client.post(path, headers=specialistHeaders, json=payload(
        authorityApproverUserId=str(specialist.id)
    ))
    assert sameUser.status_code == 400, sameUser.text

    wrongRoles = client.post(path, headers=specialistHeaders, json=payload(
        specialistApproverUserId=str(authority.id),
        authorityApproverUserId=str(specialist.id),
    ))
    assert wrongRoles.status_code == 400, wrongRoles.text

    accepted = client.post(path, headers=authorityHeaders, json=payload())
    assert accepted.status_code == 201, accepted.text
    body = accepted.json()
    assert body["approvedByUserId"] == str(authority.id)
    assert body["approvedRole"] == "organisation_admin"
    assert body["specialistApproverUserId"] == str(specialist.id)
    assert body["authorityApproverUserId"] == str(authority.id)


def test_intervention_approval_requires_uninvolved_organisation_authority(
    client: TestClient,
    dbSession: Session,
    authProvider: LocalTokenAuthProvider,
) -> None:
    orgId = create_temp_org(dbSession).id
    proposer, proposerHeaders = _principal(
        dbSession, authProvider, orgId, Role.ENVIRONMENTAL_SPECIALIST
    )
    otherSpecialist, otherHeaders = _principal(
        dbSession, authProvider, orgId, Role.ENVIRONMENTAL_SPECIALIST
    )
    authority, authorityHeaders = _principal(
        dbSession, authProvider, orgId, Role.ORGANISATION_ADMIN
    )
    path = "/api/v1/interventions/interventions"

    def create(headers: dict[str, str]) -> str:
        response = client.post(
            path,
            headers=headers,
            json={
                "organisationId": str(orgId),
                "caseId": str(uuid.uuid4()),
                "objective": "Reduce sediment entering the catchment.",
                "responsibleOrganisationId": str(orgId),
                "authorisedLeadUserId": str(uuid.uuid4()),
            },
        )
        assert response.status_code == 201, response.text
        assert response.json()["proposedByUserId"] is not None
        return response.json()["id"]

    def approve(interventionId: str, headers: dict[str, str]):
        return client.post(
            f"{path}/{interventionId}/transition",
            headers=headers,
            json={
                "organisationId": str(orgId),
                "targetStatus": "approved",
                "rationale": "Budget and mandate confirmed.",
            },
        )

    interventionId = create(proposerHeaders)
    wrongRole = approve(interventionId, proposerHeaders)
    assert wrongRole.status_code == 403, wrongRole.text
    assert wrongRole.json()["code"] == "FORBIDDEN"
    assert approve(interventionId, otherHeaders).status_code == 403
    approved = approve(interventionId, authorityHeaders)
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "approved"

    ownProposal = create(authorityHeaders)
    selfApproval = approve(ownProposal, authorityHeaders)
    assert selfApproval.status_code == 403, selfApproval.text
    assert selfApproval.json()["code"] == "SELF_REVIEW_FORBIDDEN"


def test_recovery_transition_refuses_assessment_without_two_keys(
    client: TestClient,
    dbSession: Session,
    authProvider: LocalTokenAuthProvider,
) -> None:
    orgId = create_temp_org(dbSession).id
    specialist, specialistHeaders = _principal(
        dbSession, authProvider, orgId, Role.ENVIRONMENTAL_SPECIALIST
    )
    intervention = _intervention(
        dbSession,
        orgId,
        leadUserId=uuid.uuid4(),
        proposerUserId=uuid.uuid4(),
        status=InterventionStatus.OUTCOME_MONITORING,
    )
    assessment = _assessment(
        dbSession,
        orgId,
        intervention.id,
        conclusion=OutcomeConclusion.RECOVERY_VERIFIED,
        twoKey=False,
    )
    response = client.post(
        f"/api/v1/interventions/interventions/{intervention.id}/transition",
        headers=specialistHeaders,
        json={
            "organisationId": str(orgId),
            "targetStatus": "recovery_verified",
            "rationale": "Monitoring complete.",
            "verificationAssessmentRef": str(assessment.id),
        },
    )
    assert response.status_code == 400, response.text
    assert response.json()["code"] == "RECOVERY_NOT_VERIFIABLE"


def test_admin_can_list_and_deactivate_users_and_organisations(
    client: TestClient,
    dbSession: Session,
    authProvider: LocalTokenAuthProvider,
) -> None:
    orgId = create_temp_org(dbSession).id
    admin, adminHeaders = _principal(
        dbSession, authProvider, orgId, Role.ORGANISATION_ADMIN
    )
    admin.systemRole = SystemRole.SYSTEM_ADMIN.value
    dbSession.commit()
    adminHeaders = auth_headers(authProvider, admin)
    target, _ = _principal(dbSession, authProvider, orgId, Role.REVIEWER)

    listed = client.get("/api/v1/users", headers=adminHeaders)
    assert listed.status_code == 200, listed.text
    ids = {item["id"] for item in listed.json()["items"]}
    assert {str(admin.id), str(target.id)} <= ids
    assert all("passwordHash" not in item for item in listed.json()["items"])

    denied = client.get("/api/v1/users", headers=auth_headers(
        authProvider, create_temp_user(dbSession, memberships=[(orgId, Role.REVIEWER)])
    ))
    assert denied.status_code == 403, denied.text

    deactivated = client.patch(
        f"/api/v1/users/{target.id}",
        headers=adminHeaders,
        json={"isActive": False, "displayName": "Deactivated reviewer"},
    )
    assert deactivated.status_code == 200, deactivated.text
    assert deactivated.json()["isActive"] is False
    login = client.post(
        "/api/v1/auth/login",
        json={"email": target.email, "password": "Passw0rd!Test"},
    )
    assert login.status_code == 401, login.text

    selfLockout = client.patch(
        f"/api/v1/users/{admin.id}",
        headers=adminHeaders,
        json={"isActive": False},
    )
    assert selfLockout.status_code == 400, selfLockout.text

    orgUpdate = client.patch(
        f"/api/v1/organisations/{orgId}",
        headers=adminHeaders,
        json={"orgType": "regulator", "isActive": False},
    )
    assert orgUpdate.status_code == 200, orgUpdate.text
    assert orgUpdate.json()["isActive"] is False
    assert orgUpdate.json()["orgType"] == "regulator"
