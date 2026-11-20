"""Phase 3 domain rule and integration smoke tests."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from ecowatch.core.errors import DomainError, ErrorCode
from ecowatch.modules import phase3Contracts as contracts
from ecowatch.modules.audit.models import AuditEvent
from ecowatch.modules.catalogue import rules as catalogueRules
from ecowatch.modules.catalogue.models import Dataset, DatasetVersion
from ecowatch.modules.catalogue.service import CatalogueService
from ecowatch.modules.identity.permissions import Permission, Principal, Role
from ecowatch.modules.intelligence import enums as intelligenceEnums
from ecowatch.modules.intelligence import rules as intelligenceRules
from ecowatch.modules.intelligence.models import (
    AnalysisOutput,
    AnalysisRun,
    EnvironmentalEntity,
    EnvironmentalRelationship,
)
from ecowatch.modules.interventions import enums as interventionEnums
from ecowatch.modules.interventions import rules as interventionRules
from ecowatch.modules.interventions.models import Intervention, InterventionMilestone
from ecowatch.modules.prioritisation import rules as prioritisationRules
from ecowatch.modules.prioritisation.models import PrioritisationAssessment
from ecowatch.modules.verification import enums as verificationEnums
from ecowatch.modules.verification import rules as verificationRules
from ecowatch.modules.verification.models import (
    IndicatorDefinition,
    IndicatorMeasurement,
    Publication,
    VerificationAssessment,
)
from tests.conftest import create_temp_org, create_temp_user

now = datetime(2026, 11, 18, 9, 0, tzinfo=UTC)


def principalFor(orgId: uuid.UUID, role: Role) -> Principal:
    return Principal(
        userId=uuid.uuid4(),
        memberships=((orgId, role),),
        isAuthenticated=True,
    )


def testCatalogueRequiresRightsAndValidCoverage() -> None:
    with pytest.raises(DomainError) as error:
        catalogueRules.assert_dataset_version_complete(
            licence="",
            attribution="Attribution",
            permittedUse="Monitoring",
            sourceAcquisitionAt=now,
            coverageStartAt=now,
            coverageEndAt=now + timedelta(days=1),
            crs="EPSG:4326",
            resolution="10m",
            method="Classification",
        )
    assert error.value.code is ErrorCode.VALIDATION_ERROR
    assert error.value.field == "licence"

    with pytest.raises(DomainError) as error:
        catalogueRules.assert_dataset_version_complete(
            licence="CC-BY-4.0",
            attribution="Attribution",
            permittedUse="Monitoring",
            sourceAcquisitionAt=now,
            coverageStartAt=now + timedelta(days=2),
            coverageEndAt=now,
            crs="EPSG:4326",
            resolution="10m",
            method="Classification",
        )
    assert error.value.field == "coverageEndAt"


def testEnvironmentalRelationshipRequiresExactlyOneEndpointPerSide() -> None:
    base = dict(
        relationshipType=intelligenceEnums.EnvironmentalRelationshipType.UPSTREAM_DOWNSTREAM,
        evidenceSummary="Sediment observations follow the upstream disturbance.",
        uncertainty=intelligenceEnums.UncertaintyLevel.MEDIUM,
        uncertaintyNote="Flow direction inferred from a coarse catchment model.",
        alternativeExplanations="A separate construction site may contribute.",
        methodName="CatchmentPathway",
        methodVersion="1.0",
    )
    intelligenceRules.assert_environmental_relationship_valid(
        fromEntityId=uuid.uuid4(),
        fromObservationId=None,
        toEntityId=None,
        toObservationId=uuid.uuid4(),
        **base,
    )
    with pytest.raises(DomainError):
        intelligenceRules.assert_environmental_relationship_valid(
            fromEntityId=uuid.uuid4(),
            fromObservationId=uuid.uuid4(),
            toEntityId=None,
            toObservationId=uuid.uuid4(),
            **base,
        )


def testEnvironmentalRelationshipRejectsMissingExplanation() -> None:
    with pytest.raises(DomainError) as error:
        intelligenceRules.assert_environmental_relationship_valid(
            relationshipType=(
                intelligenceEnums.EnvironmentalRelationshipType.SOURCE_PATHWAY_RECEPTOR
            ),
            fromEntityId=uuid.uuid4(),
            fromObservationId=None,
            toEntityId=uuid.uuid4(),
            toObservationId=None,
            evidenceSummary="",
            uncertainty=intelligenceEnums.UncertaintyLevel.HIGH,
            uncertaintyNote="Unknown pathway.",
            alternativeExplanations="None identified.",
            methodName="PathwayReview",
            methodVersion="0.3",
        )
    assert error.value.field == "evidenceSummary"


def testAnalysisRunAndPredictionGates() -> None:
    with pytest.raises(DomainError) as error:
        intelligenceRules.assert_analysis_run_reproducible(
            question="Did bare soil increase?",
            analysisType=intelligenceEnums.AnalysisType.LAND_COVER_CHANGE,
            methodName="NDVIThreshold",
            methodVersion="1.0",
            inputDatasetVersionIds=[],
            crs="EPSG:4326",
            parameters={"threshold": 0.2},
            limitations="Cloud cover in one month.",
        )
    assert error.value.field == "inputDatasetVersionIds"

    with pytest.raises(DomainError) as error:
        intelligenceRules.assert_prediction_allowed(
            modelName=None,
            modelVersion=None,
            validationReportRef=None,
            representativeDataRef=None,
            targetDefined=False,
        )
    assert error.value.code is ErrorCode.PREDICTION_BLOCKED


def testPrioritisationFactorViewNeverImputes() -> None:
    view = prioritisationRules.build_factor_view(
        {"magnitude": "large", "extent": None, "evidenceQuality": "weak", "dataGaps": []}
    )
    assert view["present"] == ["magnitude", "evidenceQuality"]
    assert "extent" in view["missing"]
    assert "dataGaps" in view["missing"]
    assert view["values"] == {"magnitude": "large", "evidenceQuality": "weak"}

    with pytest.raises(DomainError):
        prioritisationRules.build_factor_view({"madeUpFactor": 1})


def testPrioritisationRejectsUnexplainedCompositeRank() -> None:
    with pytest.raises(DomainError) as error:
        prioritisationRules.assert_assessment_honest(
            factors={"magnitude": "large"},
            compositeRank=1.0,
            rankingMethodRef=None,
            rankIsNotSeverity=None,
            decision=None,
            rationale=None,
            decidedByUserId=None,
        )
    assert error.value.field == "rankingMethodRef"

    with pytest.raises(DomainError) as error:
        prioritisationRules.assert_assessment_honest(
            factors={"magnitude": "large"},
            compositeRank=1.0,
            rankingMethodRef="docs/prioritisation-method.md",
            rankIsNotSeverity=False,
            decision=None,
            rationale=None,
            decidedByUserId=None,
        )
    assert error.value.field == "rankIsNotSeverity"


def testPrioritisationDecisionRequiresRationaleAndUser() -> None:
    with pytest.raises(DomainError) as error:
        prioritisationRules.assert_assessment_honest(
            factors={"magnitude": "large"},
            compositeRank=None,
            rankingMethodRef=None,
            rankIsNotSeverity=None,
            decision="priority_set",
            rationale="",
            decidedByUserId=None,
        )
    assert error.value.field == "decidedByUserId"


def testInterventionTransitionsAndActivityDerivation() -> None:
    interventionRules.assert_transition(
        interventionEnums.InterventionStatus.IN_PROGRESS,
        interventionEnums.InterventionStatus.ACTIVITY_COMPLETED,
    )
    with pytest.raises(DomainError) as error:
        interventionRules.assert_transition(
            interventionEnums.InterventionStatus.PROPOSED,
            interventionEnums.InterventionStatus.OUTCOME_MONITORING,
        )
    assert error.value.code is ErrorCode.INVALID_STATUS_TRANSITION
    with pytest.raises(DomainError) as error:
        interventionRules.assert_transition(
            interventionEnums.InterventionStatus.OUTCOME_MONITORING,
            interventionEnums.InterventionStatus.RECOVERY_VERIFIED,
        )
    assert error.value.code is ErrorCode.RECOVERY_NOT_VERIFIABLE

    assert (
        interventionRules.derive_activity_status(
            [
                interventionEnums.MilestoneStatus.COMPLETED,
                interventionEnums.MilestoneStatus.COMPLETED,
            ]
        )
        is interventionEnums.InterventionStatus.ACTIVITY_COMPLETED
    )
    assert (
        interventionRules.derive_activity_status(
            [
                interventionEnums.MilestoneStatus.COMPLETED,
                interventionEnums.MilestoneStatus.IN_PROGRESS,
            ]
        )
        is interventionEnums.InterventionStatus.IN_PROGRESS
    )


def testEvidenceLevelsCannotBeConflated() -> None:
    with pytest.raises(DomainError):
        interventionRules.assert_evidence_level_ordering(
            activityCompleted=False,
            outputDelivered=True,
            environmentalOutcome=True,
            recoveryVerified=True,
        )
    with pytest.raises(DomainError):
        verificationRules.assert_outcome_separation(
            activityCompleted=True,
            outputDelivered=True,
            environmentalOutcome=False,
            recoveryVerified=True,
        )


def testMeasurementQualifierRules() -> None:
    base = dict(
        unitId=uuid.uuid4(),
        methodName="LabTurbidity",
        methodVersion="2.1",
        measuredAt=now,
    )
    verificationRules.assert_measurement_valid(
        value=12.5,
        qualifier=verificationEnums.MeasurementQualifier.EXACT,
        detectionLimit=None,
        **base,
    )
    verificationRules.assert_measurement_valid(
        value=None,
        qualifier=verificationEnums.MeasurementQualifier.NOT_DETECTED,
        detectionLimit=0.1,
        **base,
    )
    with pytest.raises(DomainError):
        verificationRules.assert_measurement_valid(
            value=0.0,
            qualifier=verificationEnums.MeasurementQualifier.NOT_DETECTED,
            detectionLimit=0.1,
            **base,
        )
    with pytest.raises(DomainError):
        verificationRules.assert_measurement_valid(
            value=5.0,
            qualifier=verificationEnums.MeasurementQualifier.LESS_THAN,
            detectionLimit=1.0,
            **base,
        )
    with pytest.raises(DomainError):
        verificationRules.assert_measurement_valid(
            value=None,
            qualifier=verificationEnums.MeasurementQualifier.LESS_THAN,
            detectionLimit=None,
            **base,
        )


def testObservedChangeNeverClaimsRecovery() -> None:
    assert (
        verificationRules.assess_observed_change(
            baselineValues=[10.0, 11.0],
            followUpValues=[4.0, 5.0],
            direction=verificationEnums.ExpectedDirection.DECREASE,
            minimumDetectableChange=1.0,
            uncertainty=0.5,
        )
        is verificationEnums.OutcomeConclusion.IMPROVEMENT
    )
    assert (
        verificationRules.assess_observed_change(
            baselineValues=[10.0],
            followUpValues=[14.0],
            direction=verificationEnums.ExpectedDirection.DECREASE,
            minimumDetectableChange=1.0,
        )
        is verificationEnums.OutcomeConclusion.DETERIORATION
    )
    assert (
        verificationRules.assess_observed_change(
            baselineValues=[10.0],
            followUpValues=[10.2],
            direction=verificationEnums.ExpectedDirection.DECREASE,
            minimumDetectableChange=1.0,
        )
        is verificationEnums.OutcomeConclusion.INCONCLUSIVE
    )
    assert (
        verificationRules.assess_observed_change(
            baselineValues=[],
            followUpValues=[10.2],
            direction=verificationEnums.ExpectedDirection.DECREASE,
        )
        is verificationEnums.OutcomeConclusion.INCONCLUSIVE
    )


def _twoKeyArgs() -> dict[str, object]:
    return {
        "specialistApproverUserId": uuid.uuid4(),
        "authorityApproverUserId": uuid.uuid4(),
        "actorUserId": None,
        "specialistRoles": frozenset({Role.ENVIRONMENTAL_SPECIALIST}),
        "authorityRoles": frozenset({Role.ORGANISATION_ADMIN}),
        "interventionOwnerUserIds": frozenset(),
    }


def testRecoveryVerificationRequiresApprovedCriteriaAndTwoKeys() -> None:
    keys = _twoKeyArgs()
    keys["actorUserId"] = keys["specialistApproverUserId"]
    base = {
        **keys,
        "baselineMeasurementIds": ["a"],
        "followUpMeasurementIds": ["b"],
        "comparisonMethod": "Matched site comparison",
        "uncertaintyDocumented": "95% interval recorded.",
        "confoundersDocumented": "Rainfall considered.",
        "seasonalContextDocumented": "Dry season matched.",
    }

    with pytest.raises(DomainError) as error:
        verificationRules.assert_recovery_verification_allowed(
            **{**base, "criteriaVersion": None, "criteriaApproved": False}
        )
    assert error.value.code is ErrorCode.RECOVERY_NOT_VERIFIABLE

    with pytest.raises(DomainError) as error:
        verificationRules.assert_recovery_verification_allowed(
            **{**base, "criteriaVersion": "criteria-2026-01", "criteriaApproved": True,
               "authorityApproverUserId": keys["specialistApproverUserId"]}
        )
    assert error.value.field == "approverUserIds"

    with pytest.raises(DomainError) as error:
        verificationRules.assert_recovery_verification_allowed(
            **{**base, "criteriaVersion": "criteria-2026-01", "criteriaApproved": True,
               "actorUserId": uuid.uuid4()}
        )
    assert error.value.code is ErrorCode.FORBIDDEN

    with pytest.raises(DomainError) as error:
        verificationRules.assert_recovery_verification_allowed(
            **{**base, "criteriaVersion": "criteria-2026-01", "criteriaApproved": True,
               "interventionOwnerUserIds": frozenset({keys["specialistApproverUserId"]})}
        )
    assert error.value.code is ErrorCode.RECOVERY_NOT_VERIFIABLE

    verificationRules.assert_recovery_verification_allowed(
        **{**base, "criteriaVersion": "criteria-2026-01", "criteriaApproved": True}
    )


def testPublicationRequiresTwoKeyApproval() -> None:
    keys = _twoKeyArgs()
    keys["actorUserId"] = keys["authorityApproverUserId"]
    base = {
        **keys,
        "publishedText": "Turbidity improved at the monitored site.",
        "approvedByUserId": uuid.uuid4(),
        "approvedRole": Role.REGISTERED_CONTRIBUTOR,
        "approvedAt": now,
    }
    with pytest.raises(DomainError) as error:
        verificationRules.assert_publication_allowed(**base)
    assert error.value.field == "approvedRole"

    with pytest.raises(DomainError) as error:
        verificationRules.assert_publication_allowed(
            **{**base, "approvedRole": Role.SYSTEM_ADMIN}
        )
    assert error.value.field == "approvedRole"

    with pytest.raises(DomainError) as error:
        verificationRules.assert_publication_allowed(
            **{
                **base,
                "approvedRole": Role.ORGANISATION_ADMIN,
                "specialistRoles": frozenset({Role.INVESTIGATOR}),
            }
        )
    assert error.value.field == "specialistApproverUserId"

    verificationRules.assert_publication_allowed(
        **{**base, "approvedRole": Role.ORGANISATION_ADMIN}
    )


def testPermissionGuardHidesOtherOrganisationAndRejectsMissingPermission() -> None:
    organisationA = uuid.uuid4()
    organisationB = uuid.uuid4()
    specialist = principalFor(organisationA, Role.ENVIRONMENTAL_SPECIALIST)
    contracts.require_permission(
        specialist, Permission.CATALOGUE_WRITE, organisationA
    )
    with pytest.raises(DomainError) as error:
        contracts.require_permission(
            specialist, Permission.CATALOGUE_WRITE, organisationB
        )
    assert error.value.code is ErrorCode.NOT_FOUND

    contributor = principalFor(organisationA, Role.REGISTERED_CONTRIBUTOR)
    with pytest.raises(DomainError) as error:
        contracts.require_permission(
            contributor, Permission.CATALOGUE_WRITE, organisationA
        )
    assert error.value.code is ErrorCode.FORBIDDEN


def testPhase3TablesRegisterOnSqlite(dbSession) -> None:
    """All Phase 3 tables must be creatable alongside Phase 1 on SQLite."""
    tableNames = {
        Dataset.__tablename__,
        DatasetVersion.__tablename__,
        EnvironmentalEntity.__tablename__,
        EnvironmentalRelationship.__tablename__,
        AnalysisRun.__tablename__,
        AnalysisOutput.__tablename__,
        PrioritisationAssessment.__tablename__,
        Intervention.__tablename__,
        InterventionMilestone.__tablename__,
        IndicatorDefinition.__tablename__,
        IndicatorMeasurement.__tablename__,
        VerificationAssessment.__tablename__,
        Publication.__tablename__,
    }
    assert tableNames <= set(Dataset.metadata.tables)


def testCatalogueServiceWritesDatasetAndAuditEvent(dbSession) -> None:
    org = create_temp_org(dbSession)
    user = create_temp_user(
        dbSession, memberships=[(org.id, Role.ENVIRONMENTAL_SPECIALIST)]
    )
    principal = Principal(
        userId=user.id,
        memberships=((org.id, Role.ENVIRONMENTAL_SPECIALIST),),
        isAuthenticated=True,
    )
    record = CatalogueService(dbSession).create_dataset(
        principal,
        organisationId=org.id,
        name="River turbidity baseline",
        owner="EcoWatch",
        licence="CC-BY-4.0",
        attribution="EcoWatch field team",
        permittedUse="Environmental monitoring",
        crs="EPSG:4326",
    )
    assert record.id is not None
    assert record.organisationId == org.id
    event = dbSession.scalars(
        select(AuditEvent).where(AuditEvent.targetId == record.id)
    ).one()
    assert event.action == "catalogue.dataset.created"
    assert event.actorRole == Role.ENVIRONMENTAL_SPECIALIST.value
