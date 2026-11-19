"""Service layer for environmental intelligence and reproducible analysis."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from ecowatch.core.errors import DomainError, ErrorCode
from ecowatch.core.models import utc_now
from ecowatch.core.schemas import CursorPage
from ecowatch.modules.identity.permissions import Permission, Principal
from ecowatch.modules.intelligence import enums, models, rules
from ecowatch.modules.intelligence.schemas import (
    AnalysisOutputResponse,
    AnalysisRunResponse,
    EntityResponse,
    RelationshipResponse,
)
from ecowatch.modules.jobs.repository import JobsRepository
from ecowatch.modules.phase3Contracts import record_event, require_permission, require_text
from ecowatch.modules.phase3Reads import list_page, load_scoped_parent, read_scope, scope_statement

ANALYSIS_JOB_TYPE = "analysis.run"


class IntelligenceService:
    """Record environmental entities, relationships, analyses, and outputs."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create_environmental_entity(
        self,
        principal: Principal,
        *,
        organisationId: UUID,
        entityType: str | enums.EnvironmentalEntityType,
        name: str,
        crs: str = "EPSG:4326",
        description: str | None = None,
        geometry: Any | None = None,
        parentEntityId: UUID | None = None,
        requestId: str | None = None,
    ) -> models.EnvironmentalEntity:
        """Create an environmental entity used to relate observations."""
        require_permission(principal, Permission.INTELLIGENCE_WRITE, organisationId)
        entityTypeValue = rules.require_enum(
            enums.EnvironmentalEntityType, entityType, "entityType"
        )
        require_text(name, "name")
        require_text(crs, "crs")
        record = models.EnvironmentalEntity(
            organisationId=organisationId,
            entityType=entityTypeValue.value,
            name=name.strip(),
            description=description,
            geometry=geometry,
            crs=crs.strip(),
            parentEntityId=parentEntityId,
        )
        self._session.add(record)
        self._session.flush()
        record_event(
            self._session,
            principal,
            organisationId=organisationId,
            action="intelligence.entity.created",
            targetType="environmentalEntity",
            targetId=record.id,
            detail={"name": record.name},
            requestId=requestId,
        )
        self._session.commit()
        return record

    def propose_environmental_relationship(
        self,
        principal: Principal,
        *,
        organisationId: UUID,
        relationshipType: str | enums.EnvironmentalRelationshipType,
        evidenceSummary: str,
        uncertainty: str | enums.UncertaintyLevel,
        uncertaintyNote: str,
        alternativeExplanations: str,
        methodName: str,
        methodVersion: str,
        reviewState: str | enums.ReviewState = enums.ReviewState.PROPOSED,
        fromEntityId: UUID | None = None,
        fromObservationId: UUID | None = None,
        toEntityId: UUID | None = None,
        toObservationId: UUID | None = None,
        spatialScope: str | None = None,
        temporalStartAt: datetime | None = None,
        temporalEndAt: datetime | None = None,
        supportingEvidenceAssetIds: list[str] | None = None,
        requestId: str | None = None,
    ) -> models.EnvironmentalRelationship:
        """Propose an evidence-backed relationship with explicit uncertainty."""
        require_permission(principal, Permission.INTELLIGENCE_WRITE, organisationId)
        rules.assert_environmental_relationship_valid(
            relationshipType=relationshipType,
            fromEntityId=fromEntityId,
            fromObservationId=fromObservationId,
            toEntityId=toEntityId,
            toObservationId=toObservationId,
            evidenceSummary=evidenceSummary,
            uncertainty=uncertainty,
            uncertaintyNote=uncertaintyNote,
            alternativeExplanations=alternativeExplanations,
            methodName=methodName,
            methodVersion=methodVersion,
        )
        reviewStateValue = rules.require_enum(enums.ReviewState, reviewState, "reviewState")
        rules.assert_temporal_scope(temporalStartAt, temporalEndAt)
        relationshipTypeValue = rules.require_enum(
            enums.EnvironmentalRelationshipType, relationshipType, "relationshipType"
        )
        uncertaintyValue = rules.require_enum(
            enums.UncertaintyLevel, uncertainty, "uncertainty"
        )
        record = models.EnvironmentalRelationship(
            organisationId=organisationId,
            relationshipType=relationshipTypeValue.value,
            fromEntityId=fromEntityId,
            fromObservationId=fromObservationId,
            toEntityId=toEntityId,
            toObservationId=toObservationId,
            spatialScope=spatialScope,
            temporalStartAt=temporalStartAt,
            temporalEndAt=temporalEndAt,
            evidenceSummary=evidenceSummary.strip(),
            supportingEvidenceAssetIds=supportingEvidenceAssetIds or [],
            methodName=methodName.strip(),
            methodVersion=methodVersion.strip(),
            uncertainty=uncertaintyValue.value,
            uncertaintyNote=uncertaintyNote.strip(),
            alternativeExplanations=alternativeExplanations.strip(),
            reviewState=reviewStateValue.value,
        )
        self._session.add(record)
        self._session.flush()
        record_event(
            self._session,
            principal,
            organisationId=organisationId,
            action="intelligence.relationship.proposed",
            targetType="environmentalRelationship",
            targetId=record.id,
            detail={"relationshipType": record.relationshipType},
            requestId=requestId,
        )
        self._session.commit()
        return record

    def review_environmental_relationship(
        self,
        principal: Principal,
        *,
        organisationId: UUID,
        relationshipId: UUID,
        reviewState: str | enums.ReviewState,
        requestId: str | None = None,
    ) -> models.EnvironmentalRelationship:
        """Move a proposed relationship to a reviewed, rejected, or contested state."""
        require_permission(principal, Permission.INTELLIGENCE_REVIEW, organisationId)
        record = self._session.get(models.EnvironmentalRelationship, relationshipId)
        if record is None or record.organisationId != organisationId:
            raise DomainError(
                ErrorCode.NOT_FOUND,
                "Environmental relationship not found.",
                statusCode=404,
                field="relationshipId",
            )
        reviewStateValue = rules.require_enum(enums.ReviewState, reviewState, "reviewState")
        if reviewStateValue is enums.ReviewState.PROPOSED:
            raise DomainError(
                ErrorCode.CONFLICT,
                "A review must move the relationship out of proposed.",
                field="reviewState",
            )
        record.reviewState = reviewStateValue.value
        record.reviewedByUserId = principal.userId
        record.reviewedAt = utc_now()
        self._session.flush()
        record_event(
            self._session,
            principal,
            organisationId=organisationId,
            action="intelligence.relationship.reviewed",
            targetType="environmentalRelationship",
            targetId=record.id,
            detail={"reviewState": record.reviewState},
            requestId=requestId,
        )
        self._session.commit()
        return record

    def queue_analysis_run(
        self,
        principal: Principal,
        *,
        organisationId: UUID,
        question: str,
        analysisType: str | enums.AnalysisType,
        methodName: str,
        methodVersion: str,
        inputDatasetVersionIds: list[str],
        crs: str,
        parameters: dict[str, Any],
        limitations: str,
        caseId: UUID | None = None,
        qualityMaskNotes: str | None = None,
        seasonalContext: str | None = None,
        requestId: str | None = None,
    ) -> models.AnalysisRun:
        """Queue a reproducible analysis run with all required inputs."""
        require_permission(principal, Permission.INTELLIGENCE_WRITE, organisationId)
        rules.assert_analysis_run_reproducible(
            question=question,
            analysisType=analysisType,
            methodName=methodName,
            methodVersion=methodVersion,
            inputDatasetVersionIds=inputDatasetVersionIds,
            crs=crs,
            parameters=parameters,
            limitations=limitations,
        )
        analysisTypeValue = rules.require_enum(enums.AnalysisType, analysisType, "analysisType")
        record = models.AnalysisRun(
            organisationId=organisationId,
            caseId=caseId,
            question=question.strip(),
            analysisType=analysisTypeValue.value,
            methodName=methodName.strip(),
            methodVersion=methodVersion.strip(),
            parameters=parameters,
            inputDatasetVersionIds=inputDatasetVersionIds,
            crs=crs.strip(),
            qualityMaskNotes=qualityMaskNotes,
            seasonalContext=seasonalContext,
            limitations=limitations.strip(),
            status=enums.AnalysisStatus.QUEUED.value,
            requestedByUserId=principal.userId,
        )
        self._session.add(record)
        self._session.flush()
        record_event(
            self._session,
            principal,
            organisationId=organisationId,
            action="intelligence.analysisRun.queued",
            targetType="analysisRun",
            targetId=record.id,
            detail={"analysisType": record.analysisType},
            requestId=requestId,
        )
        # Keep inference out of the request: a worker advances this run through
        # the same durable queue used by correlation and evidence scans.
        JobsRepository(self._session).enqueue(
            ANALYSIS_JOB_TYPE,
            {"analysisRunId": str(record.id)},
        )
        self._session.commit()
        return record

    def mark_analysis_run_running(self, analysisRunId: UUID) -> models.AnalysisRun:
        """Worker handler: move a queued run to running; never invent an output.

        Idempotent so a retried job cannot overwrite an already-started run.
        """
        run = self._session.get(models.AnalysisRun, analysisRunId)
        if run is None:
            raise DomainError(
                ErrorCode.NOT_FOUND,
                "Analysis run not found.",
                statusCode=404,
                field="analysisRunId",
            )
        if run.status == enums.AnalysisStatus.QUEUED.value:
            run.status = enums.AnalysisStatus.RUNNING.value
            run.startedAt = utc_now()
            self._session.flush()
        return run

    def record_analysis_output(
        self,
        principal: Principal,
        *,
        organisationId: UUID,
        analysisRunId: UUID,
        outputType: str | enums.AnalysisOutputType,
        summary: str,
        limitations: str,
        storageKey: str | None = None,
        derivedFromObservationIds: list[str] | None = None,
        requestId: str | None = None,
    ) -> models.AnalysisOutput:
        """Record a derived output pending human interpretation."""
        require_permission(principal, Permission.INTELLIGENCE_WRITE, organisationId)
        run = self._session.get(models.AnalysisRun, analysisRunId)
        if run is None or run.organisationId != organisationId:
            raise DomainError(
                ErrorCode.NOT_FOUND,
                "Analysis run not found.",
                statusCode=404,
                field="analysisRunId",
            )
        if run.status not in (
            enums.AnalysisStatus.RUNNING.value,
            enums.AnalysisStatus.SUCCEEDED.value,
        ):
            raise DomainError(
                ErrorCode.CONFLICT,
                "Analysis output requires a running or succeeded analysis.",
                field="analysisRunId",
            )
        rules.assert_derived_output(
            analysisRunId=analysisRunId,
            outputType=outputType,
            summary=summary,
            limitations=limitations,
        )
        outputTypeValue = rules.require_enum(
            enums.AnalysisOutputType, outputType, "outputType"
        )
        record = models.AnalysisOutput(
            analysisRunId=analysisRunId,
            outputType=outputTypeValue.value,
            summary=summary.strip(),
            storageKey=storageKey,
            isDerived=True,
            derivedFromObservationIds=derivedFromObservationIds or [],
            interpretationState=enums.InterpretationState.PENDING_REVIEW.value,
            limitations=limitations.strip(),
        )
        self._session.add(record)
        self._session.flush()
        record_event(
            self._session,
            principal,
            organisationId=organisationId,
            action="intelligence.analysisOutput.recorded",
            targetType="analysisOutput",
            targetId=record.id,
            detail={"outputType": record.outputType},
            requestId=requestId,
        )
        self._session.commit()
        return record

    def request_prediction(
        self,
        principal: Principal,
        *,
        organisationId: UUID,
        modelName: str | None,
        modelVersion: str | None,
        validationReportRef: str | None,
        representativeDataRef: str | None,
        targetDefined: bool,
    ) -> None:
        """Block predictive analysis until a validated model and target exist."""
        require_permission(principal, Permission.INTELLIGENCE_WRITE, organisationId)
        rules.assert_prediction_allowed(
            modelName=modelName,
            modelVersion=modelVersion,
            validationReportRef=validationReportRef,
            representativeDataRef=representativeDataRef,
            targetDefined=targetDefined,
        )

    def list_entities(
        self,
        principal: Principal,
        *,
        organisationId: UUID | None = None,
        cursor: str | None = None,
        limit: int = 50,
    ) -> CursorPage[EntityResponse]:
        """List environmental entities scoped to the caller's organisations."""
        allowedOrgIds = read_scope(principal, Permission.INTELLIGENCE_WRITE)
        stmt = scope_statement(
            select(models.EnvironmentalEntity),
            models.EnvironmentalEntity,
            allowedOrgIds,
            organisationId,
        )
        rows, nextCursor, hasMore = list_page(
            self._session, stmt, models.EnvironmentalEntity, cursor=cursor, limit=limit
        )
        return CursorPage[EntityResponse](
            items=[EntityResponse.model_validate(row) for row in rows],
            nextCursor=nextCursor,
            hasMore=hasMore,
        )

    def list_relationships(
        self,
        principal: Principal,
        *,
        organisationId: UUID | None = None,
        cursor: str | None = None,
        limit: int = 50,
    ) -> CursorPage[RelationshipResponse]:
        """List proposed and reviewed relationships, including their review state."""
        allowedOrgIds = read_scope(principal, Permission.INTELLIGENCE_WRITE)
        stmt = scope_statement(
            select(models.EnvironmentalRelationship),
            models.EnvironmentalRelationship,
            allowedOrgIds,
            organisationId,
        )
        rows, nextCursor, hasMore = list_page(
            self._session, stmt, models.EnvironmentalRelationship, cursor=cursor, limit=limit
        )
        return CursorPage[RelationshipResponse](
            items=[RelationshipResponse.model_validate(row) for row in rows],
            nextCursor=nextCursor,
            hasMore=hasMore,
        )

    def list_analysis_runs(
        self,
        principal: Principal,
        *,
        organisationId: UUID | None = None,
        cursor: str | None = None,
        limit: int = 50,
    ) -> CursorPage[AnalysisRunResponse]:
        """List queued and completed analysis runs with their method provenance."""
        allowedOrgIds = read_scope(principal, Permission.INTELLIGENCE_WRITE)
        stmt = scope_statement(
            select(models.AnalysisRun),
            models.AnalysisRun,
            allowedOrgIds,
            organisationId,
        )
        rows, nextCursor, hasMore = list_page(
            self._session, stmt, models.AnalysisRun, cursor=cursor, limit=limit
        )
        return CursorPage[AnalysisRunResponse](
            items=[AnalysisRunResponse.model_validate(row) for row in rows],
            nextCursor=nextCursor,
            hasMore=hasMore,
        )

    def list_analysis_outputs(
        self,
        principal: Principal,
        analysisRunId: UUID,
        *,
        cursor: str | None = None,
        limit: int = 50,
    ) -> CursorPage[AnalysisOutputResponse]:
        """List outputs of one in-scope analysis run; the parent carries the org scope."""
        allowedOrgIds = read_scope(principal, Permission.INTELLIGENCE_WRITE)
        load_scoped_parent(
            self._session,
            models.AnalysisRun,
            analysisRunId,
            allowedOrgIds,
            fieldName="analysisRunId",
            label="Analysis run",
        )
        stmt = select(models.AnalysisOutput).where(
            models.AnalysisOutput.analysisRunId == analysisRunId
        )
        rows, nextCursor, hasMore = list_page(
            self._session, stmt, models.AnalysisOutput, cursor=cursor, limit=limit
        )
        return CursorPage[AnalysisOutputResponse](
            items=[AnalysisOutputResponse.model_validate(row) for row in rows],
            nextCursor=nextCursor,
            hasMore=hasMore,
        )
