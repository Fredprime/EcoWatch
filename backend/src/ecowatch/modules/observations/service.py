"""Business logic for observations, corrections, quality flags, sources, and vocabularies."""

import uuid
from datetime import datetime
from typing import Any

from fastapi import status
from sqlalchemy.orm import Session

from ecowatch.core.errors import DomainError, ErrorCode
from ecowatch.core.schemas import CursorPage
from ecowatch.core.spatial import format_point_wkt
from ecowatch.modules.audit.service import record_audit_event
from ecowatch.modules.identity.permissions import Permission, Principal, Role
from ecowatch.modules.observations.models import AccessClass, LocationPrecision, Observation
from ecowatch.modules.observations.repository import ObservationRepository
from ecowatch.modules.observations.schemas import (
    CreateCorrectionRequest,
    CreateMethodRequest,
    CreateUnitRequest,
    MethodResponse,
    ObservationPublicSummaryResponse,
    ObservationRestrictedResponse,
    ObservationSourceResponse,
    ObservationVersionResponse,
    UnitResponse,
    UpdateQualityFlagsRequest,
    coarsen_point,
    normalize_utc,
)


def _serialize_json_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, uuid.UUID):
        return str(value)
    return value


def _require_user_id(principal: Principal) -> uuid.UUID:
    if not principal.isAuthenticated or principal.userId is None:
        raise DomainError(
            ErrorCode.UNAUTHORIZED,
            "Authentication required",
            statusCode=status.HTTP_401_UNAUTHORIZED,
        )
    return principal.userId


def _ensure_specialist_or_admin(principal: Principal) -> None:
    if principal.is_system_admin or any(
        role == Role.ENVIRONMENTAL_SPECIALIST for _, role in principal.memberships
    ):
        return
    raise DomainError(
        ErrorCode.FORBIDDEN,
        "Only environmental_specialist or system_admin may manage methods and units",
        statusCode=status.HTTP_403_FORBIDDEN,
    )


def _ensure_obs_permission(principal: Principal, perm: Permission, obs: Observation) -> None:
    if not principal.is_system_admin and not principal.has_permission(perm, obs.organisationId):
        raise DomainError(
            ErrorCode.NOT_FOUND,
            "Observation not found",
            statusCode=status.HTTP_404_NOT_FOUND,
        )


class ObservationService:
    """Service layer for reading, correcting, and classifying observations."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._repo = ObservationRepository(session)

    def _get_visible_observation(
        self, principal: Principal, observationId: uuid.UUID
    ) -> Observation:
        obs = self._repo.get_by_id(observationId)
        if obs is None or (obs.isHidden and not principal.is_system_admin):
            raise DomainError(
                ErrorCode.NOT_FOUND,
                "Observation not found",
                statusCode=status.HTTP_404_NOT_FOUND,
            )
        return obs

    def list_observations(
        self,
        principal: Principal,
        *,
        organisationId: uuid.UUID | None = None,
        observationType: str | None = None,
        sourceType: str | None = None,
        cursor: str | None = None,
        limit: int = 50,
    ) -> CursorPage[ObservationPublicSummaryResponse]:
        """List redacted observations scoped to accessible organisations or own submissions."""
        userId = _require_user_id(principal)

        if principal.is_system_admin:
            allowedOrgIds = None
            ownUserId = None
            includeHidden = True
        else:
            allowedOrgIds = principal.accessible_org_ids(Permission.OBS_READ_REDACTED)
            ownUserId = userId
            includeHidden = False

        items, nextCursor, hasMore = self._repo.list_observations(
            organisationIds=allowedOrgIds,
            ownUserId=ownUserId,
            organisationId=organisationId,
            observationType=observationType,
            sourceType=sourceType,
            includeHidden=includeHidden,
            cursor=cursor,
            limit=limit,
        )
        return CursorPage[ObservationPublicSummaryResponse](
            items=[ObservationPublicSummaryResponse.from_orm_record(obs) for obs in items],
            nextCursor=nextCursor,
            hasMore=hasMore,
        )

    def get_observation(
        self, principal: Principal, observationId: uuid.UUID
    ) -> ObservationRestrictedResponse | ObservationPublicSummaryResponse:
        """Return org-scoped observation detail; 404 on cross-organisation access."""
        userId = _require_user_id(principal)
        obs = self._get_visible_observation(principal, observationId)

        canRestricted = principal.is_system_admin or principal.has_permission(
            Permission.OBS_READ_RESTRICTED, obs.organisationId
        )
        canRedacted = principal.has_permission(Permission.OBS_READ_REDACTED, obs.organisationId)
        isOwn = obs.submittedByUserId is not None and obs.submittedByUserId == userId

        if not (canRestricted or canRedacted or isOwn):
            raise DomainError(
                ErrorCode.NOT_FOUND,
                "Observation not found",
                statusCode=status.HTTP_404_NOT_FOUND,
            )

        if canRestricted or isOwn:
            return ObservationRestrictedResponse.from_orm_record(obs)
        return ObservationPublicSummaryResponse.from_orm_record(obs)

    def list_versions(
        self, principal: Principal, observationId: uuid.UUID
    ) -> list[ObservationVersionResponse]:
        """List append-only version history for an org-scoped observation."""
        obs = self._get_visible_observation(principal, observationId)
        _ensure_obs_permission(principal, Permission.OBS_READ_REDACTED, obs)
        return [
            ObservationVersionResponse.model_validate(v)
            for v in self._repo.list_versions(obs.id)
        ]

    def correct_observation(
        self,
        principal: Principal,
        observationId: uuid.UUID,
        payload: CreateCorrectionRequest,
        *,
        requestId: str | None = None,
    ) -> ObservationRestrictedResponse:
        """Apply a controlled correction, append ObservationVersion, and audit."""
        userId = _require_user_id(principal)
        obs = self._get_visible_observation(principal, observationId)

        orgRoles = principal.roles_for_org(obs.organisationId)
        isStaffCorrector = principal.is_system_admin or bool(
            orgRoles & {Role.REVIEWER, Role.INVESTIGATOR}
        )
        isOwn = obs.submittedByUserId is not None and obs.submittedByUserId == userId
        if not isStaffCorrector and not isOwn:
            raise DomainError(
                ErrorCode.NOT_FOUND,
                "Observation not found",
                statusCode=status.HTTP_404_NOT_FOUND,
            )
        if (
            not isStaffCorrector
            and isOwn
            and (
                obs.qualityFlags
                or self._repo.has_case_link(obs.id)
                or self._repo.has_staff_edits(obs)
            )
        ):
            raise DomainError(
                ErrorCode.CONFLICT,
                "Observation cannot be corrected by contributor after review",
                statusCode=status.HTTP_409_CONFLICT,
            )

        if payload.methodId is not None and self._repo.get_method_by_id(payload.methodId) is None:
            raise DomainError(
                ErrorCode.NOT_FOUND,
                "Method not found",
                statusCode=status.HTTP_404_NOT_FOUND,
                field="methodId",
            )
        if payload.unitId is not None and self._repo.get_unit_by_id(payload.unitId) is None:
            raise DomainError(
                ErrorCode.NOT_FOUND,
                "Unit not found",
                statusCode=status.HTTP_404_NOT_FOUND,
                field="unitId",
            )

        newEventStart = (
            normalize_utc(payload.eventStartAt)
            if "eventStartAt" in payload.model_fields_set
            else normalize_utc(obs.eventStartAt)
        )
        newObservedAt = (
            normalize_utc(payload.observedAt)
            if "observedAt" in payload.model_fields_set
            else normalize_utc(obs.observedAt)
        )
        newObservedEnd = (
            normalize_utc(payload.observedEndAt)
            if "observedEndAt" in payload.model_fields_set
            else normalize_utc(obs.observedEndAt)
        )
        receivedAt = normalize_utc(obs.receivedAt)

        if newObservedEnd is not None and newObservedAt is None:
            raise DomainError(
                ErrorCode.VALIDATION_ERROR,
                "observedEndAt requires observedAt",
                statusCode=status.HTTP_422_UNPROCESSABLE_CONTENT,
                field="observedEndAt",
            )
        if (
            newObservedAt is not None
            and newObservedEnd is not None
            and newObservedEnd < newObservedAt
        ):
            raise DomainError(
                ErrorCode.VALIDATION_ERROR,
                "observedEndAt must be greater than or equal to observedAt",
                statusCode=status.HTTP_422_UNPROCESSABLE_CONTENT,
                field="observedEndAt",
            )
        if newEventStart is not None and receivedAt is not None and newEventStart > receivedAt:
            raise DomainError(
                ErrorCode.VALIDATION_ERROR,
                "eventStartAt cannot be after server receivedAt",
                statusCode=status.HTTP_422_UNPROCESSABLE_CONTENT,
                field="eventStartAt",
            )

        changedFields: dict[str, Any] = {}
        scalarUpdates: dict[str, Any] = {
            "observationType": (
                payload.observationType.strip() if payload.observationType is not None else None
            ),
            "description": payload.description.strip() if payload.description is not None else None,
            "isFirsthand": payload.isFirsthand,
            "structuredData": payload.structuredData,
            "methodId": payload.methodId,
            "unitId": payload.unitId,
            "instrument": payload.instrument,
            "eventStartAt": newEventStart,
            "observedAt": newObservedAt,
            "observedEndAt": newObservedEnd,
            "timePrecision": (
                payload.timePrecision.value if payload.timePrecision is not None else None
            ),
            "originalTimeWording": payload.originalTimeWording,
            "locationPrecision": (
                payload.locationPrecision.value
                if payload.locationPrecision is not None
                else None
            ),
            "originalLocationWording": payload.originalLocationWording,
        }

        for fieldName in payload.model_fields_set:
            if fieldName in {"reason", "lat", "lon"}:
                continue
            newVal = scalarUpdates[fieldName]
            oldVal = getattr(obs, fieldName)
            if isinstance(oldVal, datetime):
                oldVal = normalize_utc(oldVal)
            if oldVal != newVal:
                changedFields[fieldName] = {
                    "old": _serialize_json_value(oldVal),
                    "new": _serialize_json_value(newVal),
                }
                setattr(obs, fieldName, newVal)

        if payload.lat is not None and payload.lon is not None:
            newWkt = format_point_wkt(payload.lon, payload.lat)
            if obs.location != newWkt:
                changedFields["location"] = {"old": obs.location, "new": newWkt}
                obs.location = newWkt
                obs.publicLocation = coarsen_point(
                    payload.lon,
                    payload.lat,
                    accessClass=AccessClass(obs.accessClass),
                    locationPrecision=LocationPrecision(obs.locationPrecision),
                )

        if not changedFields:
            raise DomainError(
                ErrorCode.VALIDATION_ERROR,
                "Correction produced no field changes",
                statusCode=status.HTTP_422_UNPROCESSABLE_CONTENT,
            )

        obs.currentVersion += 1
        self._repo.create_version(
            observationId=obs.id,
            versionNumber=obs.currentVersion,
            changedFields=changedFields,
            reason=payload.reason.strip(),
            editedByUserId=userId,
        )
        record_audit_event(
            self._session,
            actorUserId=userId,
            actorRole=principal.primary_role_label,
            organisationId=obs.organisationId,
            action="observation.corrected",
            targetType="observation",
            targetId=obs.id,
            reason=payload.reason.strip(),
            details={
                "versionNumber": obs.currentVersion,
                "fields": sorted(changedFields.keys()),
            },
            requestId=requestId,
        )
        self._session.commit()
        self._session.refresh(obs)
        return ObservationRestrictedResponse.from_orm_record(obs)

    def update_quality_flags(
        self,
        principal: Principal,
        observationId: uuid.UUID,
        payload: UpdateQualityFlagsRequest,
        *,
        requestId: str | None = None,
    ) -> ObservationPublicSummaryResponse:
        """Update observation quality flags (RV/ES/SA, org-scoped) with audit event."""
        obs = self._get_visible_observation(principal, observationId)
        _ensure_obs_permission(principal, Permission.OBS_QUALITY_FLAG, obs)

        normalized = list(
            dict.fromkeys(flag.strip() for flag in payload.qualityFlags if flag.strip())
        )
        previous = list(obs.qualityFlags or [])
        obs.qualityFlags = normalized

        record_audit_event(
            self._session,
            actorUserId=principal.userId,
            actorRole=principal.primary_role_label,
            organisationId=obs.organisationId,
            action="observation.quality_flagged",
            targetType="observation",
            targetId=obs.id,
            reason=payload.reason,
            details={"previousFlags": previous, "qualityFlags": normalized},
            requestId=requestId,
        )
        self._session.commit()
        self._session.refresh(obs)
        return ObservationPublicSummaryResponse.from_orm_record(obs)

    def get_source(
        self,
        principal: Principal,
        observationId: uuid.UUID,
        *,
        requestId: str | None = None,
    ) -> ObservationSourceResponse:
        """Return isolated contributor identity/contact record (OA own org / SA only) and audit."""
        obs = self._get_visible_observation(principal, observationId)
        _ensure_obs_permission(principal, Permission.SOURCE_READ, obs)
        source = self._repo.get_source_by_observation_id(obs.id)
        if source is None:
            raise DomainError(
                ErrorCode.NOT_FOUND,
                "Observation source not found",
                statusCode=status.HTTP_404_NOT_FOUND,
            )
        record_audit_event(
            self._session,
            actorUserId=principal.userId,
            actorRole=principal.primary_role_label,
            organisationId=obs.organisationId,
            action="observation_source.viewed",
            targetType="observation_source",
            targetId=source.id,
            details={"observationId": str(obs.id)},
            requestId=requestId,
        )
        self._session.commit()
        return ObservationSourceResponse.model_validate(source)

    def list_methods(
        self, *, cursor: str | None = None, limit: int = 50
    ) -> CursorPage[MethodResponse]:
        """List registered field and analytical methods."""
        items, nextCursor, hasMore = self._repo.list_methods(cursor=cursor, limit=limit)
        return CursorPage[MethodResponse](
            items=[MethodResponse.model_validate(m) for m in items],
            nextCursor=nextCursor,
            hasMore=hasMore,
        )

    def create_method(
        self,
        principal: Principal,
        payload: CreateMethodRequest,
        *,
        requestId: str | None = None,
    ) -> MethodResponse:
        """Register a field or laboratory method (ES/SA only)."""
        _ensure_specialist_or_admin(principal)
        if self._repo.get_method_by_code(payload.code) is not None:
            raise DomainError(
                ErrorCode.CONFLICT,
                "A method with this code already exists",
                statusCode=status.HTTP_409_CONFLICT,
                field="code",
            )
        method = self._repo.create_method(
            code=payload.code,
            name=payload.name,
            version=payload.version,
            protocolText=payload.protocolText,
            instrumentClass=payload.instrumentClass,
        )
        record_audit_event(
            self._session,
            actorUserId=principal.userId,
            actorRole=principal.primary_role_label,
            action="method.created",
            targetType="method",
            targetId=method.id,
            details={"code": method.code, "version": method.version},
            requestId=requestId,
        )
        self._session.commit()
        self._session.refresh(method)
        return MethodResponse.model_validate(method)

    def list_units(
        self, *, cursor: str | None = None, limit: int = 50
    ) -> CursorPage[UnitResponse]:
        """List controlled measurement units."""
        items, nextCursor, hasMore = self._repo.list_units(cursor=cursor, limit=limit)
        return CursorPage[UnitResponse](
            items=[UnitResponse.model_validate(u) for u in items],
            nextCursor=nextCursor,
            hasMore=hasMore,
        )

    def create_unit(
        self,
        principal: Principal,
        payload: CreateUnitRequest,
        *,
        requestId: str | None = None,
    ) -> UnitResponse:
        """Register a controlled measurement unit (ES/SA only)."""
        _ensure_specialist_or_admin(principal)
        if self._repo.get_unit_by_symbol(payload.symbol) is not None:
            raise DomainError(
                ErrorCode.CONFLICT,
                "A unit with this symbol already exists",
                statusCode=status.HTTP_409_CONFLICT,
                field="symbol",
            )
        unit = self._repo.create_unit(
            symbol=payload.symbol,
            name=payload.name,
            dimension=payload.dimension,
            ucumCode=payload.ucumCode,
        )
        record_audit_event(
            self._session,
            actorUserId=principal.userId,
            actorRole=principal.primary_role_label,
            action="unit.created",
            targetType="unit",
            targetId=unit.id,
            details={"symbol": unit.symbol, "dimension": unit.dimension},
            requestId=requestId,
        )
        self._session.commit()
        self._session.refresh(unit)
        return UnitResponse.model_validate(unit)
