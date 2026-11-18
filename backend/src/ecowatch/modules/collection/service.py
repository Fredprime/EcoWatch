"""Collection service handling idempotent intake, rate limits, and tracking-code lookup."""

import hashlib
import json
import uuid

from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ecowatch.core.config import Settings
from ecowatch.core.errors import DomainError, ErrorCode
from ecowatch.core.models import utc_now
from ecowatch.core.rate_limit import check_and_increment_limit, reset_limit
from ecowatch.core.security import generate_tracking_code, hash_tracking_code
from ecowatch.core.spatial import format_point_wkt
from ecowatch.modules.audit.service import record_audit_event
from ecowatch.modules.collection.schemas import (
    CreateObservationRequest,
    IntakeReceiptResponse,
    ReceiptLookupRequest,
    ReceiptLookupResponse,
)
from ecowatch.modules.correlation.service import enqueue_scan
from ecowatch.modules.identity.models import Organisation
from ecowatch.modules.identity.permissions import Principal
from ecowatch.modules.observations.models import (
    LocationPrecision,
    Observation,
    SourceType,
    TimePrecision,
)
from ecowatch.modules.observations.repository import ObservationRepository
from ecowatch.modules.observations.schemas import coarsen_point, normalize_utc


def compute_payload_hash(payload: CreateObservationRequest) -> str:
    """Compute a deterministic SHA-256 hash over the canonical intake payload."""
    canonical = payload.model_dump(mode="json", exclude={"idempotencyKey"})
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _build_receipt(
    obs: Observation, *, trackingCode: str | None, idempotentReplay: bool
) -> IntakeReceiptResponse:
    return IntakeReceiptResponse(
        observationId=obs.id,
        organisationId=obs.organisationId,
        receivedAt=obs.receivedAt,
        observationType=obs.observationType,
        timePrecision=TimePrecision(obs.timePrecision),
        locationPrecision=LocationPrecision(obs.locationPrecision),
        currentVersion=obs.currentVersion,
        trackingCode=trackingCode,
        idempotentReplay=idempotentReplay,
    )


class CollectionService:
    """Intake service for anonymous and authenticated observation submissions."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._obsRepo = ObservationRepository(session)

    def _resolve_organisation_id(
        self, principal: Principal, requestedOrgId: uuid.UUID | None
    ) -> uuid.UUID:
        if requestedOrgId is not None:
            org = self._session.get(Organisation, requestedOrgId)
            if org is None or not org.isActive:
                raise DomainError(
                    ErrorCode.NOT_FOUND,
                    "Organisation not found",
                    statusCode=status.HTTP_404_NOT_FOUND,
                    field="organisationId",
                )
            return org.id

        if principal.isAuthenticated:
            memberOrgIds = {orgId for orgId, _ in principal.memberships}
            if len(memberOrgIds) == 1:
                return next(iter(memberOrgIds))

        activeOrgs = list(
            self._session.scalars(
                select(Organisation).where(Organisation.isActive.is_(True))
            ).all()
        )
        if len(activeOrgs) == 1:
            return activeOrgs[0].id

        publicOrgs = [
            org
            for org in activeOrgs
            if org.orgType.lower() in {"public", "community", "default"}
        ]
        if len(publicOrgs) == 1:
            return publicOrgs[0].id

        raise DomainError(
            ErrorCode.VALIDATION_ERROR,
            "organisationId is required when no unique default organisation exists",
            statusCode=status.HTTP_422_UNPROCESSABLE_CONTENT,
            field="organisationId",
        )

    def submit_observation(
        self,
        principal: Principal,
        payload: CreateObservationRequest,
        *,
        settings: Settings,
        clientIp: str,
        requestId: str | None = None,
    ) -> tuple[IntakeReceiptResponse, bool]:
        """Persist an observation idempotently with isolated source and audit event."""
        receivedAt = utc_now()
        eventStartAt = normalize_utc(payload.eventStartAt)
        if eventStartAt is not None and eventStartAt > receivedAt:
            raise DomainError(
                ErrorCode.VALIDATION_ERROR,
                "eventStartAt cannot be after server receivedAt",
                statusCode=status.HTTP_422_UNPROCESSABLE_CONTENT,
                field="eventStartAt",
            )

        if not principal.isAuthenticated:
            if (
                payload.sourceType is not None
                and payload.sourceType != SourceType.COMMUNITY_ANONYMOUS
            ):
                raise DomainError(
                    ErrorCode.FORBIDDEN,
                    "Anonymous submissions must use sourceType community_anonymous",
                    statusCode=status.HTTP_403_FORBIDDEN,
                    field="sourceType",
                )
            resolvedSourceType = SourceType.COMMUNITY_ANONYMOUS
        else:
            resolvedSourceType = payload.sourceType or SourceType.COMMUNITY_REGISTERED

        payloadHash = compute_payload_hash(payload)
        existing = self._obsRepo.get_by_idempotency_key(payload.idempotencyKey)
        if existing is not None:
            if existing.payloadHash != payloadHash:
                raise DomainError(
                    ErrorCode.IDEMPOTENCY_KEY_CONFLICT,
                    "Idempotency key already used with a different payload",
                    statusCode=status.HTTP_409_CONFLICT,
                    field="idempotencyKey",
                )
            return _build_receipt(existing, trackingCode=None, idempotentReplay=True), True

        if not principal.isAuthenticated:
            try:
                check_and_increment_limit(
                    self._session,
                    f"public_intake:ip:{clientIp}",
                    maxAttempts=settings.publicIntakeRateLimit,
                    windowSeconds=settings.publicIntakeWindowSeconds,
                )
            except DomainError:
                self._session.commit()
                raise

        organisationId = self._resolve_organisation_id(principal, payload.organisationId)

        if payload.methodId is not None and self._obsRepo.get_method_by_id(
            payload.methodId
        ) is None:
            raise DomainError(
                ErrorCode.NOT_FOUND,
                "Method not found",
                statusCode=status.HTTP_404_NOT_FOUND,
                field="methodId",
            )
        if payload.unitId is not None and self._obsRepo.get_unit_by_id(payload.unitId) is None:
            raise DomainError(
                ErrorCode.NOT_FOUND,
                "Unit not found",
                statusCode=status.HTTP_404_NOT_FOUND,
                field="unitId",
            )

        trackingCode = generate_tracking_code()
        trackingCodeHash = hash_tracking_code(trackingCode, settings.authSecret)

        locationWkt: str | None = None
        publicLocationWkt: str | None = None
        if payload.lat is not None and payload.lon is not None:
            locationWkt = format_point_wkt(payload.lon, payload.lat)
            publicLocationWkt = coarsen_point(
                payload.lon,
                payload.lat,
                accessClass=payload.accessClass,
                locationPrecision=payload.locationPrecision,
            )

        obs = self._obsRepo.create_observation(
            organisationId=organisationId,
            idempotencyKey=payload.idempotencyKey,
            payloadHash=payloadHash,
            trackingCodeHash=trackingCodeHash,
            observationType=payload.observationType.strip(),
            sourceType=resolvedSourceType.value,
            description=payload.description.strip(),
            isFirsthand=payload.isFirsthand,
            structuredData=payload.structuredData,
            methodId=payload.methodId,
            unitId=payload.unitId,
            instrument=payload.instrument.strip() if payload.instrument else None,
            eventStartAt=eventStartAt,
            observedAt=normalize_utc(payload.observedAt),
            observedEndAt=normalize_utc(payload.observedEndAt),
            submittedAt=normalize_utc(payload.submittedAt),
            receivedAt=receivedAt,
            timePrecision=payload.timePrecision.value,
            originalTimeWording=payload.originalTimeWording,
            location=locationWkt,
            publicLocation=publicLocationWkt,
            locationPrecision=payload.locationPrecision.value,
            originalLocationWording=payload.originalLocationWording,
            qualityFlags=[],
            accessClass=payload.accessClass.value,
            isHidden=False,
            currentVersion=1,
            submittedByUserId=principal.userId,
        )

        self._obsRepo.create_version(
            observationId=obs.id,
            versionNumber=1,
            changedFields={
                "observationType": obs.observationType,
                "sourceType": obs.sourceType,
                "description": obs.description,
                "timePrecision": obs.timePrecision,
                "locationPrecision": obs.locationPrecision,
            },
            reason="Initial submission",
            editedByUserId=principal.userId,
        )

        sourceInput = payload.source
        self._obsRepo.create_source(
            observationId=obs.id,
            reporterName=sourceInput.reporterName if sourceInput else None,
            contactChannel=sourceInput.contactChannel if sourceInput else None,
            contactValue=sourceInput.contactValue if sourceInput else None,
            consentGiven=sourceInput.consentGiven if sourceInput else False,
            privacyNoticeVersion=(
                sourceInput.privacyNoticeVersion if sourceInput else "v1"
            ),
            safetyAck=sourceInput.safetyAck if sourceInput else False,
            clientMetadata=sourceInput.clientMetadata if sourceInput else None,
        )

        record_audit_event(
            self._session,
            actorUserId=principal.userId,
            actorRole=principal.primary_role_label,
            organisationId=obs.organisationId,
            action="observation.created",
            targetType="observation",
            targetId=obs.id,
            details={
                "observationType": obs.observationType,
                "sourceType": obs.sourceType,
            },
            requestId=requestId,
        )

        # New reports are scanned in the background, never in this request:
        # intake latency must not include model work (`NFR-001`). The enqueue
        # shares this transaction, so a rolled-back submission leaves no job,
        # and an idempotent replay returns above without queueing a second one.
        enqueue_scan(self._session, obs.id, maxAttempts=settings.workerMaxAttempts)

        self._session.commit()
        self._session.refresh(obs)

        return _build_receipt(obs, trackingCode=trackingCode, idempotentReplay=False), False

    def lookup_receipt(
        self,
        payload: ReceiptLookupRequest,
        *,
        settings: Settings,
        clientIp: str,
    ) -> ReceiptLookupResponse:
        """Look up an anonymous submission receipt by tracking code with attempt lockout."""
        bucketKey = f"receipt_lookup:ip:{clientIp}"
        try:
            check_and_increment_limit(
                self._session,
                bucketKey,
                maxAttempts=settings.trackingLookupMaxAttempts,
                windowSeconds=settings.trackingLookupLockoutSeconds,
                lockoutSeconds=settings.trackingLookupLockoutSeconds,
                lockoutCode=ErrorCode.TRACKING_CODE_LOCKED,
            )
        except DomainError:
            self._session.commit()
            raise

        codeHash = hash_tracking_code(payload.trackingCode.strip(), settings.authSecret)
        obs = self._obsRepo.get_by_tracking_code_hash(codeHash)
        if obs is None or obs.isHidden:
            self._session.commit()
            raise DomainError(
                ErrorCode.NOT_FOUND,
                "Receipt not found for provided tracking code",
                statusCode=status.HTTP_404_NOT_FOUND,
            )

        reset_limit(self._session, bucketKey)
        evidenceCount = self._obsRepo.count_evidence_assets(obs.id)
        self._session.commit()

        return ReceiptLookupResponse(
            observationId=obs.id,
            receivedAt=obs.receivedAt,
            observationType=obs.observationType,
            timePrecision=TimePrecision(obs.timePrecision),
            locationPrecision=LocationPrecision(obs.locationPrecision),
            evidenceCount=evidenceCount,
        )
