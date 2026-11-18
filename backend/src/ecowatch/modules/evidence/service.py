"""Business logic for evidence upload, scan/derivative processing, and retrieval."""

import hashlib
import hmac
import uuid

from fastapi import status
from sqlalchemy.orm import Session

from ecowatch.core.config import Settings
from ecowatch.core.errors import DomainError, ErrorCode
from ecowatch.core.models import utc_now
from ecowatch.core.security import hash_tracking_code
from ecowatch.core.storage import StorageProvider
from ecowatch.modules.audit.service import record_audit_event
from ecowatch.modules.evidence.models import (
    AssetDerivative,
    DerivativeType,
    EvidenceAsset,
    MetadataExtractionStatus,
    ScanStatus,
)
from ecowatch.modules.evidence.repository import EvidenceRepository
from ecowatch.modules.evidence.scanner import (
    IMAGE_MIME_TYPES,
    create_exif_stripped_preview,
    detect_mime_from_bytes,
    extract_image_metadata,
    is_mime_compatible,
    normalize_declared_mime,
    sanitize_filename,
    scan_evidence_bytes,
)
from ecowatch.modules.evidence.schemas import (
    AssetDerivativeResponse,
    EvidenceAssetResponse,
    EvidenceScanStatusResponse,
)
from ecowatch.modules.identity.permissions import Permission, Principal
from ecowatch.modules.jobs.repository import JobsRepository
from ecowatch.modules.observations.models import AccessClass, Observation, SourceType
from ecowatch.modules.observations.repository import ObservationRepository


class EvidenceService:
    """Service managing original evidence preservation, scanning, and derivatives."""

    def __init__(self, session: Session, storage: StorageProvider) -> None:
        self._session = session
        self._storage = storage
        self._repo = EvidenceRepository(session)
        self._obsRepo = ObservationRepository(session)
        self._jobsRepo = JobsRepository(session)

    def _get_visible_observation(
        self, principal: Principal, observationId: uuid.UUID
    ) -> Observation:
        obs = self._obsRepo.get_by_id(observationId)
        if obs is None or (obs.isHidden and not principal.is_system_admin):
            raise DomainError(
                ErrorCode.NOT_FOUND,
                "Observation not found",
                statusCode=status.HTTP_404_NOT_FOUND,
            )
        return obs

    def _to_asset_response(self, asset: EvidenceAsset) -> EvidenceAssetResponse:
        derivatives = self._repo.list_derivatives_for_asset(asset.id)
        return EvidenceAssetResponse(
            id=asset.id,
            observationId=asset.observationId,
            organisationId=asset.organisationId,
            originalFilename=asset.originalFilename,
            declaredMimeType=asset.declaredMimeType,
            detectedMimeType=asset.detectedMimeType,
            sizeBytes=asset.sizeBytes,
            sha256Checksum=asset.sha256Checksum,
            scanStatus=ScanStatus(asset.scanStatus),
            metadataExtractionStatus=MetadataExtractionStatus(
                asset.metadataExtractionStatus
            ),
            accessClass=AccessClass(asset.accessClass),
            receivedAt=asset.receivedAt,
            createdAt=asset.createdAt,
            derivatives=[AssetDerivativeResponse.model_validate(d) for d in derivatives],
        )

    def _authorize_upload(
        self,
        principal: Principal,
        observation: Observation,
        *,
        trackingCode: str | None,
        settings: Settings,
    ) -> None:
        if principal.isAuthenticated:
            canOrgUpload = principal.is_system_admin or principal.has_permission(
                Permission.EVIDENCE_UPLOAD, observation.organisationId
            )
            isOwn = (
                observation.submittedByUserId is not None
                and observation.submittedByUserId == principal.userId
            )
            if not (canOrgUpload or isOwn):
                raise DomainError(
                    ErrorCode.NOT_FOUND,
                    "Observation not found",
                    statusCode=status.HTTP_404_NOT_FOUND,
                )
            return

        if not trackingCode or not trackingCode.strip():
            raise DomainError(
                ErrorCode.UNAUTHORIZED,
                "Authentication or X-Tracking-Code header required to upload evidence",
                statusCode=status.HTTP_401_UNAUTHORIZED,
            )
        if observation.trackingCodeHash is None:
            raise DomainError(
                ErrorCode.FORBIDDEN,
                "Invalid tracking code for observation",
                statusCode=status.HTTP_403_FORBIDDEN,
            )
        providedHash = hash_tracking_code(trackingCode.strip(), settings.authSecret)
        if not hmac.compare_digest(providedHash, observation.trackingCodeHash):
            raise DomainError(
                ErrorCode.FORBIDDEN,
                "Invalid tracking code for observation",
                statusCode=status.HTTP_403_FORBIDDEN,
            )

    def upload_evidence(
        self,
        principal: Principal,
        observationId: uuid.UUID,
        *,
        rawBytes: bytes,
        filename: str | None,
        declaredMimeType: str | None,
        accessClass: AccessClass = AccessClass.RESTRICTED,
        trackingCode: str | None = None,
        settings: Settings,
        requestId: str | None = None,
    ) -> EvidenceAssetResponse:
        """Validate, store untouched original bytes, enqueue scan job, and audit."""
        obs = self._get_visible_observation(principal, observationId)
        self._authorize_upload(principal, obs, trackingCode=trackingCode, settings=settings)

        if not rawBytes:
            raise DomainError(
                ErrorCode.VALIDATION_ERROR,
                "Uploaded evidence file must not be empty",
                statusCode=status.HTTP_422_UNPROCESSABLE_CONTENT,
                field="file",
            )
        if len(rawBytes) > settings.maxUploadBytes:
            raise DomainError(
                ErrorCode.PAYLOAD_TOO_LARGE,
                f"Evidence file exceeds maximum allowed size of {settings.maxUploadBytes} bytes",
                statusCode=status.HTTP_413_CONTENT_TOO_LARGE,
                field="file",
            )

        normalizedDeclared = normalize_declared_mime(declaredMimeType)
        detectedMime = detect_mime_from_bytes(rawBytes, normalizedDeclared)
        if not is_mime_compatible(detectedMime, normalizedDeclared):
            raise DomainError(
                ErrorCode.UNSUPPORTED_MEDIA_TYPE,
                "Unsupported or mismatched file content signature",
                statusCode=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                field="file",
            )
        assert detectedMime is not None

        now = utc_now()
        assetId = uuid.uuid4()
        storageKey = f"originals/{now:%Y}/{now:%m}/{assetId}"
        checksum = hashlib.sha256(rawBytes).hexdigest()
        safeName = sanitize_filename(filename)

        self._storage.put_bytes(storageKey, rawBytes)

        asset = self._repo.create_asset(
            id=assetId,
            observationId=obs.id,
            organisationId=obs.organisationId,
            storageKey=storageKey,
            originalFilename=safeName,
            declaredMimeType=normalizedDeclared,
            detectedMimeType=detectedMime,
            sizeBytes=len(rawBytes),
            sha256Checksum=checksum,
            scanStatus=ScanStatus.PENDING.value,
            metadataExtractionStatus=MetadataExtractionStatus.PENDING.value,
            extractedMetadata=None,
            accessClass=accessClass.value,
            uploadedByUserId=principal.userId,
            receivedAt=now,
            createdAt=now,
        )

        self._jobsRepo.enqueue(
            "evidence.scan_and_derive",
            {"assetId": str(asset.id)},
            maxAttempts=settings.workerMaxAttempts,
        )

        record_audit_event(
            self._session,
            actorUserId=principal.userId,
            actorRole=principal.primary_role_label,
            organisationId=obs.organisationId,
            action="evidence.uploaded",
            targetType="evidence_asset",
            targetId=asset.id,
            details={
                "observationId": str(obs.id),
                "detectedMimeType": detectedMime,
                "sizeBytes": len(rawBytes),
                "sha256": checksum,
            },
            requestId=requestId,
        )
        self._session.commit()
        self._session.refresh(asset)
        return self._to_asset_response(asset)

    def process_scan_and_derive(self, assetId: uuid.UUID) -> None:
        """Worker handler: scan bytes, extract EXIF, and build EXIF-stripped derivatives."""
        asset = self._repo.get_asset_by_id(assetId)
        if asset is None:
            raise ValueError(f"EvidenceAsset {assetId} not found")

        rawBytes = self._storage.get_bytes(asset.storageKey)
        scanStatus, scanReason = scan_evidence_bytes(rawBytes, asset.detectedMimeType)
        if scanStatus != ScanStatus.CLEAN:
            asset.scanStatus = scanStatus.value
            asset.metadataExtractionStatus = MetadataExtractionStatus.UNAVAILABLE.value
            record_audit_event(
                self._session,
                actorUserId=None,
                actorRole="system",
                organisationId=asset.organisationId,
                action="evidence.scanned",
                targetType="evidence_asset",
                targetId=asset.id,
                reason=scanReason,
                details={"scanStatus": asset.scanStatus},
            )
            self._session.flush()
            return

        if asset.detectedMimeType in IMAGE_MIME_TYPES:
            metaStatus, metadata = extract_image_metadata(rawBytes)
            asset.metadataExtractionStatus = metaStatus.value
            asset.extractedMetadata = metadata

            existingTypes = {
                d.derivativeType for d in self._repo.list_derivatives_for_asset(asset.id)
            }
            now = utc_now()
            for derivType, maxDim in (
                (DerivativeType.EXIF_STRIPPED_PREVIEW, 1600),
                (DerivativeType.THUMBNAIL, 320),
            ):
                if derivType.value in existingTypes:
                    continue
                derivBytes, derivMime = create_exif_stripped_preview(
                    rawBytes, asset.detectedMimeType, maxDimension=maxDim
                )
                derivId = uuid.uuid4()
                derivKey = f"derivatives/{now:%Y}/{now:%m}/{derivId}"
                self._storage.put_bytes(derivKey, derivBytes)
                self._repo.create_derivative(
                    id=derivId,
                    parentAssetId=asset.id,
                    derivativeType=derivType.value,
                    storageKey=derivKey,
                    mimeType=derivMime,
                    sizeBytes=len(derivBytes),
                    sha256Checksum=hashlib.sha256(derivBytes).hexdigest(),
                    exifStripped=True,
                    accessClass=AccessClass.INTERNAL.value,
                    createdAt=now,
                )
        else:
            asset.metadataExtractionStatus = MetadataExtractionStatus.UNAVAILABLE.value

        asset.scanStatus = ScanStatus.CLEAN.value
        record_audit_event(
            self._session,
            actorUserId=None,
            actorRole="system",
            organisationId=asset.organisationId,
            action="evidence.scanned",
            targetType="evidence_asset",
            targetId=asset.id,
            details={
                "scanStatus": asset.scanStatus,
                "metadataExtractionStatus": asset.metadataExtractionStatus,
            },
        )
        self._session.flush()

    def _get_scoped_asset(
        self, principal: Principal, assetId: uuid.UUID, permission: Permission
    ) -> tuple[EvidenceAsset, Observation]:
        asset = self._repo.get_asset_by_id(assetId)
        if asset is None:
            raise DomainError(
                ErrorCode.NOT_FOUND,
                "Evidence asset not found",
                statusCode=status.HTTP_404_NOT_FOUND,
            )
        if not principal.is_system_admin and not principal.has_permission(
            permission, asset.organisationId
        ):
            raise DomainError(
                ErrorCode.NOT_FOUND,
                "Evidence asset not found",
                statusCode=status.HTTP_404_NOT_FOUND,
            )
        obs = self._obsRepo.get_by_id(asset.observationId)
        if obs is None or (obs.isHidden and not principal.is_system_admin):
            raise DomainError(
                ErrorCode.NOT_FOUND,
                "Evidence asset not found",
                statusCode=status.HTTP_404_NOT_FOUND,
            )
        return asset, obs

    @staticmethod
    def _enforce_scan_policy(asset: EvidenceAsset, obs: Observation) -> None:
        if asset.scanStatus in {ScanStatus.QUARANTINED.value, ScanStatus.REJECTED.value}:
            raise DomainError(
                ErrorCode.EVIDENCE_QUARANTINED,
                "Evidence asset is quarantined or rejected",
                statusCode=status.HTTP_403_FORBIDDEN,
            )
        if (
            obs.sourceType == SourceType.COMMUNITY_ANONYMOUS.value
            and asset.scanStatus != ScanStatus.CLEAN.value
        ):
            raise DomainError(
                ErrorCode.EVIDENCE_NOT_READY,
                "Anonymous evidence asset is not ready until security scan completes",
                statusCode=status.HTTP_409_CONFLICT,
            )

    def get_original_bytes(
        self,
        principal: Principal,
        assetId: uuid.UUID,
        *,
        requestId: str | None = None,
    ) -> tuple[EvidenceAsset, bytes]:
        """Authorize, audit, and fetch untouched original evidence bytes."""
        asset, obs = self._get_scoped_asset(
            principal, assetId, Permission.EVIDENCE_READ_ORIGINAL
        )
        self._enforce_scan_policy(asset, obs)

        data = self._storage.get_bytes(asset.storageKey)
        record_audit_event(
            self._session,
            actorUserId=principal.userId,
            actorRole=principal.primary_role_label,
            organisationId=asset.organisationId,
            action="evidence.original_accessed",
            targetType="evidence_asset",
            targetId=asset.id,
            details={"observationId": str(asset.observationId)},
            requestId=requestId,
        )
        self._session.commit()
        return asset, data

    def get_derivative_bytes(
        self,
        principal: Principal,
        assetId: uuid.UUID,
        derivativeId: uuid.UUID,
    ) -> tuple[AssetDerivative, bytes]:
        """Authorize and fetch EXIF-stripped derivative bytes."""
        asset, obs = self._get_scoped_asset(
            principal, assetId, Permission.EVIDENCE_READ_DERIVATIVE
        )
        derivative = self._repo.get_derivative_by_id(derivativeId)
        if derivative is None or derivative.parentAssetId != asset.id:
            raise DomainError(
                ErrorCode.NOT_FOUND,
                "Evidence derivative not found",
                statusCode=status.HTTP_404_NOT_FOUND,
            )
        self._enforce_scan_policy(asset, obs)
        data = self._storage.get_bytes(derivative.storageKey)
        return derivative, data

    def get_scan_status(
        self, principal: Principal, assetId: uuid.UUID
    ) -> EvidenceScanStatusResponse:
        """Return security scan and metadata extraction status for an org-scoped asset."""
        asset, _ = self._get_scoped_asset(
            principal, assetId, Permission.EVIDENCE_READ_SCAN_STATUS
        )
        derivatives = self._repo.list_derivatives_for_asset(asset.id)
        return EvidenceScanStatusResponse(
            id=asset.id,
            observationId=asset.observationId,
            organisationId=asset.organisationId,
            scanStatus=ScanStatus(asset.scanStatus),
            metadataExtractionStatus=MetadataExtractionStatus(
                asset.metadataExtractionStatus
            ),
            extractedMetadata=asset.extractedMetadata,
            derivatives=[AssetDerivativeResponse.model_validate(d) for d in derivatives],
        )

    def list_observation_evidence(
        self, principal: Principal, observationId: uuid.UUID
    ) -> list[EvidenceAssetResponse]:
        """List evidence assets metadata for an org-scoped observation."""
        obs = self._get_visible_observation(principal, observationId)
        if not principal.is_system_admin and not principal.has_permission(
            Permission.EVIDENCE_READ_DERIVATIVE, obs.organisationId
        ):
            raise DomainError(
                ErrorCode.NOT_FOUND,
                "Observation not found",
                statusCode=status.HTTP_404_NOT_FOUND,
            )
        assets = self._repo.list_assets_for_observation(obs.id)
        return [self._to_asset_response(asset) for asset in assets]
