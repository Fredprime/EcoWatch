"""Domain rules for qualified measurements, verification, and publication."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from statistics import fmean

from ecowatch.core.errors import DomainError, ErrorCode
from ecowatch.modules.identity.permissions import Role
from ecowatch.modules.verification import enums


def require_enum(
    enumClass: type[StrEnum],
    value: str | StrEnum | None,
    fieldName: str,
) -> StrEnum:
    """Resolve a value against an enumeration or raise a field-level error."""
    if value is None:
        raise DomainError(
            ErrorCode.VALIDATION_ERROR, f"{fieldName} is required.", field=fieldName
        )
    try:
        return enumClass(value)
    except ValueError as error:
        raise DomainError(
            ErrorCode.VALIDATION_ERROR,
            f"{fieldName} has an unsupported value.",
            field=fieldName,
        ) from error


def assert_measurement_valid(
    *,
    value: float | None,
    qualifier: str | enums.MeasurementQualifier | None,
    detectionLimit: float | None,
    unitId: object | None,
    methodName: str | None,
    methodVersion: str | None,
    measuredAt: datetime | None,
) -> None:
    """Require a resolved unit, method, time, and qualifier-consistent value."""
    qualifierValue = require_enum(enums.MeasurementQualifier, qualifier, "qualifier")
    if unitId is None:
        raise DomainError(
            ErrorCode.VALIDATION_ERROR,
            "A resolved unit is required for a measurement.",
            field="unitId",
        )
    for fieldName, valueText in {
        "methodName": methodName,
        "methodVersion": methodVersion,
    }.items():
        if valueText is None or not valueText.strip():
            raise DomainError(
                ErrorCode.VALIDATION_ERROR,
                f"{fieldName} is required.",
                field=fieldName,
            )
    if measuredAt is None:
        raise DomainError(
            ErrorCode.VALIDATION_ERROR, "measuredAt is required.", field="measuredAt"
        )
    if detectionLimit is not None and detectionLimit < 0:
        raise DomainError(
            ErrorCode.VALIDATION_ERROR,
            "detectionLimit cannot be negative.",
            field="detectionLimit",
        )

    if qualifierValue is enums.MeasurementQualifier.EXACT:
        if value is None:
            raise DomainError(
                ErrorCode.VALIDATION_ERROR,
                "An exact measurement requires a value.",
                field="value",
            )
        return

    if qualifierValue is enums.MeasurementQualifier.NOT_DETECTED:
        if value is not None:
            raise DomainError(
                ErrorCode.VALIDATION_ERROR,
                "A not-detected measurement cannot carry a numeric value.",
                field="value",
            )
        if detectionLimit is None:
            raise DomainError(
                ErrorCode.VALIDATION_ERROR,
                "A not-detected measurement requires a detection limit.",
                field="detectionLimit",
            )
        return

    if detectionLimit is None:
        raise DomainError(
            ErrorCode.VALIDATION_ERROR,
            "A bounded measurement requires a detection limit.",
            field="detectionLimit",
        )
    if value is not None and value > detectionLimit:
        raise DomainError(
            ErrorCode.VALIDATION_ERROR,
            "A bounded measurement value cannot exceed its detection limit.",
            field="value",
        )


def assert_outcome_separation(
    *,
    activityCompleted: bool,
    outputDelivered: bool,
    environmentalOutcome: bool,
    recoveryVerified: bool,
) -> None:
    """Keep activity, output, outcome, and recovery strictly ordered."""
    if outputDelivered and not activityCompleted:
        raise DomainError(
            ErrorCode.VALIDATION_ERROR,
            "Output delivery requires completed activity.",
            field="activityCompleted",
        )
    if environmentalOutcome and not outputDelivered:
        raise DomainError(
            ErrorCode.VALIDATION_ERROR,
            "An environmental outcome requires a delivered output.",
            field="outputDelivered",
        )
    if recoveryVerified and not environmentalOutcome:
        raise DomainError(
            ErrorCode.VALIDATION_ERROR,
            "Recovery verification requires a recorded environmental outcome.",
            field="environmentalOutcome",
        )


def assert_two_key_pair(
    *,
    specialistApproverUserId: object | None,
    authorityApproverUserId: object | None,
    actorUserId: object | None,
    specialistRoles: frozenset[Role],
    authorityRoles: frozenset[Role],
    interventionOwnerUserIds: frozenset[object],
    errorCode: ErrorCode,
) -> None:
    """Require two distinct role-qualified approvers, one of them the actor.

    Recovery verification and publication are two-key conclusions. The specialist
    key must hold environmental_specialist and the authority key must hold
    organisation_admin. Neither key may be the intervention owner, and the acting
    caller must supply one of the two keys rather than nominating two other people.
    """
    if specialistApproverUserId is None or authorityApproverUserId is None:
        raise DomainError(
            errorCode,
            "Two approvers are required: an environmental specialist and an "
            "organisation authority.",
            field="approverUserIds",
        )
    if specialistApproverUserId == authorityApproverUserId:
        raise DomainError(
            errorCode,
            "The two approvers must be different users.",
            field="approverUserIds",
        )
    if actorUserId is None or actorUserId not in {
        specialistApproverUserId,
        authorityApproverUserId,
    }:
        raise DomainError(
            ErrorCode.FORBIDDEN,
            "The acting caller must be one of the two recorded approvers.",
            statusCode=403,
            field="approverUserIds",
        )
    if Role.ENVIRONMENTAL_SPECIALIST not in specialistRoles:
        raise DomainError(
            errorCode,
            "The specialist approver must hold environmental_specialist in this organisation.",
            field="specialistApproverUserId",
        )
    if Role.ORGANISATION_ADMIN not in authorityRoles:
        raise DomainError(
            errorCode,
            "The authority approver must hold organisation_admin in this organisation.",
            field="authorityApproverUserId",
        )
    if (
        specialistApproverUserId in interventionOwnerUserIds
        or authorityApproverUserId in interventionOwnerUserIds
    ):
        raise DomainError(
            errorCode,
            "The intervention owner cannot approve a conclusion about that intervention.",
            field="approverUserIds",
        )


def assert_recovery_verification_allowed(
    *,
    criteriaVersion: str | None,
    criteriaApproved: bool,
    specialistApproverUserId: object | None,
    authorityApproverUserId: object | None,
    actorUserId: object | None,
    specialistRoles: frozenset[Role],
    authorityRoles: frozenset[Role],
    interventionOwnerUserIds: frozenset[object],
    baselineMeasurementIds: list[str] | None,
    followUpMeasurementIds: list[str] | None,
    comparisonMethod: str | None,
    uncertaintyDocumented: str | None,
    confoundersDocumented: str | None,
    seasonalContextDocumented: str | None,
) -> None:
    """Gate recovery verification behind approved criteria and two distinct keys."""
    if criteriaVersion is None or not criteriaVersion.strip():
        raise DomainError(
            ErrorCode.RECOVERY_NOT_VERIFIABLE,
            "No approved recovery criteria version is available; recovery cannot be verified.",
            field="criteriaVersion",
        )
    if not criteriaApproved:
        raise DomainError(
            ErrorCode.RECOVERY_NOT_VERIFIABLE,
            "Recovery criteria are not approved; recovery cannot be verified.",
            field="criteriaApproved",
        )
    assert_two_key_pair(
        specialistApproverUserId=specialistApproverUserId,
        authorityApproverUserId=authorityApproverUserId,
        actorUserId=actorUserId,
        specialistRoles=specialistRoles,
        authorityRoles=authorityRoles,
        interventionOwnerUserIds=interventionOwnerUserIds,
        errorCode=ErrorCode.RECOVERY_NOT_VERIFIABLE,
    )
    if not baselineMeasurementIds:
        raise DomainError(
            ErrorCode.RECOVERY_NOT_VERIFIABLE,
            "A baseline measurement is required.",
            field="baselineMeasurementIds",
        )
    if not followUpMeasurementIds:
        raise DomainError(
            ErrorCode.RECOVERY_NOT_VERIFIABLE,
            "A follow-up measurement is required.",
            field="followUpMeasurementIds",
        )
    for fieldName, value in {
        "comparisonMethod": comparisonMethod,
        "uncertaintyDocumented": uncertaintyDocumented,
        "confoundersDocumented": confoundersDocumented,
        "seasonalContextDocumented": seasonalContextDocumented,
    }.items():
        if value is None or not value.strip():
            raise DomainError(
                ErrorCode.RECOVERY_NOT_VERIFIABLE,
                f"{fieldName} is required before recovery can be verified.",
                field=fieldName,
            )


def assess_observed_change(
    *,
    baselineValues: list[float],
    followUpValues: list[float],
    direction: str | enums.ExpectedDirection,
    minimumDetectableChange: float | None = None,
    uncertainty: float | None = None,
) -> enums.OutcomeConclusion:
    """Classify observed change without ever claiming recovery."""
    directionValue = require_enum(enums.ExpectedDirection, direction, "direction")
    if not baselineValues or not followUpValues:
        return enums.OutcomeConclusion.INCONCLUSIVE
    if minimumDetectableChange is not None and minimumDetectableChange < 0:
        raise DomainError(
            ErrorCode.VALIDATION_ERROR,
            "minimumDetectableChange cannot be negative.",
            field="minimumDetectableChange",
        )
    if uncertainty is not None and uncertainty < 0:
        raise DomainError(
            ErrorCode.VALIDATION_ERROR,
            "uncertainty cannot be negative.",
            field="uncertainty",
        )

    threshold = max(minimumDetectableChange or 0.0, uncertainty or 0.0)
    change = fmean(followUpValues) - fmean(baselineValues)
    if abs(change) <= threshold:
        return enums.OutcomeConclusion.INCONCLUSIVE

    if directionValue is enums.ExpectedDirection.INCREASE:
        return (
            enums.OutcomeConclusion.IMPROVEMENT
            if change > 0
            else enums.OutcomeConclusion.DETERIORATION
        )
    if directionValue is enums.ExpectedDirection.DECREASE:
        return (
            enums.OutcomeConclusion.IMPROVEMENT
            if change < 0
            else enums.OutcomeConclusion.DETERIORATION
        )
    return enums.OutcomeConclusion.IMPROVEMENT


def assert_publication_allowed(
    *,
    publishedText: str | None,
    approvedByUserId: object | None,
    approvedRole: str | Role | None,
    approvedAt: datetime | None,
    specialistApproverUserId: object | None,
    authorityApproverUserId: object | None,
    actorUserId: object | None,
    specialistRoles: frozenset[Role],
    authorityRoles: frozenset[Role],
    interventionOwnerUserIds: frozenset[object],
) -> None:
    """Require two-key human approval before publishing a public summary."""
    if publishedText is None or not publishedText.strip():
        raise DomainError(
            ErrorCode.VALIDATION_ERROR,
            "publishedText is required.",
            field="publishedText",
        )
    if approvedByUserId is None:
        raise DomainError(
            ErrorCode.VALIDATION_ERROR,
            "A publication requires an approving user.",
            field="approvedByUserId",
        )
    approvedRoleValue = require_enum(Role, approvedRole, "approvedRole")
    allowed = {
        Role.ENVIRONMENTAL_SPECIALIST,
        Role.ORGANISATION_ADMIN,
    }
    if approvedRoleValue not in allowed:
        raise DomainError(
            ErrorCode.VALIDATION_ERROR,
            "This role cannot approve a public summary.",
            field="approvedRole",
        )
    if approvedAt is None:
        raise DomainError(
            ErrorCode.VALIDATION_ERROR,
            "A publication requires an approval timestamp.",
            field="approvedAt",
        )
    assert_two_key_pair(
        specialistApproverUserId=specialistApproverUserId,
        authorityApproverUserId=authorityApproverUserId,
        actorUserId=actorUserId,
        specialistRoles=specialistRoles,
        authorityRoles=authorityRoles,
        interventionOwnerUserIds=interventionOwnerUserIds,
        errorCode=ErrorCode.VALIDATION_ERROR,
    )


def assert_criteria_documented(criteriaVersion: str | None) -> None:
    """Require an approved criteria version before final verification."""
    if criteriaVersion is None or not criteriaVersion.strip():
        raise DomainError(
            ErrorCode.RECOVERY_NOT_VERIFIABLE,
            "An approved criteria version is required for a final verification assessment.",
            field="criteriaVersion",
        )
