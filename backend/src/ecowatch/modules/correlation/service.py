"""Correlation service: build features, score candidates, record human decisions.

This layer holds the two rules that are easy to lose in glue code:

  1. A scan never overwrites a decision. Re-scanning refreshes open suggestions
     and leaves `accepted` / `rejected` / `ambiguous` rows exactly as recorded.
  2. A reviewer never decides on their own submission, and every decision writes
     an audit event in the same transaction as the decision itself.
"""

import uuid
from typing import Any

from fastapi import status
from sqlalchemy.orm import Session

from ecowatch.core.errors import DomainError, ErrorCode
from ecowatch.core.models import utc_now
from ecowatch.core.spatial import parse_point_wkt
from ecowatch.modules.audit.service import record_audit_event
from ecowatch.modules.correlation.features import Location, ObservationFeatures
from ecowatch.modules.correlation.models import (
    CorrelationTask,
    EvidenceRelationship,
    RelationshipStatus,
)
from ecowatch.modules.correlation.repository import (
    MAX_CANDIDATES,
    CorrelationRepository,
    require_aware,
)
from ecowatch.modules.correlation.scoring import rank
from ecowatch.modules.identity.permissions import (
    Permission,
    Principal,
    ensure_not_self_submitted,
)
from ecowatch.modules.jobs.repository import JobsRepository
from ecowatch.modules.observations.models import Observation

SCAN_JOB_TYPE = "correlation.scan"


def features_for(
    observation: Observation,
    *,
    locationWkt: Any,
    sourceRef: str | None,
    dialectName: str,
) -> ObservationFeatures:
    """Project an observation onto the only fields correlation may compare."""
    point = parse_point_wkt(locationWkt) if locationWkt is not None else None
    return ObservationFeatures(
        observation_id=str(observation.id),
        text=observation.description,
        observed_at=require_aware(observation.observedAt, dialectName=dialectName),
        location=Location(lat=point[1], lon=point[0]) if point is not None else None,
        category=observation.observationType or None,
        source_ref=sourceRef,
    )


class CorrelationService:
    """Scan observations for related reports and record reviewer decisions."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._repo = CorrelationRepository(session)

    def scan_observation(self, observationId: uuid.UUID) -> int:
        """Score one observation against its bounded candidate set.

        Returns how many suggestions were written or refreshed. Never raises for
        an observation with nothing to compare: that is a normal outcome.
        """
        subject = self._repo.get_observation(observationId)
        if subject is None:
            raise DomainError(
                ErrorCode.NOT_FOUND,
                "Observation not found",
                statusCode=status.HTTP_404_NOT_FOUND,
            )

        dialectName = self._repo.dialect_name
        subjectFeatures = features_for(
            subject,
            locationWkt=self._repo.location_wkt(subject.id),
            sourceRef=subject.sourceRef,
            dialectName=dialectName,
        )

        candidateFeatures = [
            features_for(
                candidate,
                locationWkt=candidateWkt,
                sourceRef=candidate.sourceRef,
                dialectName=dialectName,
            )
            for candidate, candidateWkt in self._repo.candidate_rows(
                subject, limit=MAX_CANDIDATES
            )
        ]

        decided = self._repo.decided_partner_ids(subject.id)
        written = 0
        for suggestion in rank(subjectFeatures, candidateFeatures).suggestions:
            partnerId = uuid.UUID(suggestion.observation_b_id)
            if partnerId in decided:
                continue
            self._repo.upsert_suggestion(
                organisationId=subject.organisationId,
                firstId=subject.id,
                secondId=partnerId,
                task=CorrelationTask.SAME_EVENT.value,
                score=suggestion.score,
                components=dict(suggestion.components),
                missingSignals=list(suggestion.missing_signals),
                reasons=list(suggestion.reasons),
                sourceIndependent=suggestion.source_independent,
            )
            written += 1

        self._session.commit()
        return written

    def decide(
        self,
        principal: Principal,
        relationshipId: uuid.UUID,
        decision: RelationshipStatus,
        *,
        reason: str | None = None,
        requestId: str | None = None,
    ) -> EvidenceRelationship:
        """Record a reviewer decision on one suggestion, with its audit event."""
        if decision is RelationshipStatus.SUGGESTED:
            raise DomainError(
                ErrorCode.VALIDATION_ERROR,
                "A decision must be accepted, rejected, or ambiguous",
                statusCode=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        relationship = self._repo.get_relationship(relationshipId)
        # A caller without permission gets the same answer as one asking about a
        # record that does not exist, so existence does not leak across tenants.
        if relationship is None or not principal.has_permission(
            Permission.CORRELATION_REVIEW, relationship.organisationId
        ):
            raise DomainError(
                ErrorCode.NOT_FOUND,
                "Suggestion not found",
                statusCode=status.HTTP_404_NOT_FOUND,
            )

        for observationId in (relationship.observationAId, relationship.observationBId):
            observation = self._repo.get_observation(observationId)
            if observation is not None:
                ensure_not_self_submitted(principal, observation.submittedByUserId)

        if relationship.status != RelationshipStatus.SUGGESTED.value:
            raise DomainError(
                ErrorCode.INVALID_STATUS_TRANSITION,
                f"Suggestion is already {relationship.status}; a decision is reversed by "
                "a new decision, never by overwriting the record",
                statusCode=status.HTTP_409_CONFLICT,
            )

        relationship.status = decision.value
        relationship.decidedByUserId = principal.userId
        relationship.decidedAt = utc_now()
        relationship.decisionReason = reason

        record_audit_event(
            self._session,
            actorUserId=principal.userId,
            actorRole=principal.primary_role_label,
            action=f"correlation.{decision.value}",
            targetType="evidence_relationship",
            targetId=relationship.id,
            organisationId=relationship.organisationId,
            reason=reason,
            details={
                "observationAId": str(relationship.observationAId),
                "observationBId": str(relationship.observationBId),
                "task": relationship.task,
                "score": relationship.score,
                "methodVersion": relationship.methodVersion,
                "sourceIndependent": relationship.sourceIndependent,
            },
            requestId=requestId,
        )

        self._session.commit()
        return relationship

    def request_scan(
        self,
        principal: Principal,
        observationId: uuid.UUID,
    ) -> uuid.UUID:
        """Validate access, then queue the scan. Returns the job id."""
        observation = self._repo.get_observation(observationId)
        if observation is None or not principal.has_permission(
            Permission.CORRELATION_REVIEW, observation.organisationId
        ):
            raise DomainError(
                ErrorCode.NOT_FOUND,
                "Observation not found",
                statusCode=status.HTTP_404_NOT_FOUND,
            )
        jobId = enqueue_scan(self._session, observationId)
        self._session.commit()
        return jobId

    def list_suggestions(
        self, principal: Principal, *, limit: int = 50
    ) -> list[EvidenceRelationship]:
        """Open suggestions visible to the caller, best first."""
        organisationIds = (
            self._repo.all_org_ids()
            if principal.is_system_admin
            else principal.accessible_org_ids(Permission.CORRELATION_READ)
        )
        return self._repo.list_suggestions(organisationIds, limit=limit)


def enqueue_scan(session: Session, observationId: uuid.UUID) -> uuid.UUID:
    """Queue a scan so intake latency never includes scoring (`NFR-001`)."""
    job = JobsRepository(session).enqueue(
        SCAN_JOB_TYPE, {"observationId": str(observationId)}
    )
    return job.id
