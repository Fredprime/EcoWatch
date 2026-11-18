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
from ecowatch.modules.correlation.detectors import TASK_REASONS, task_for
from ecowatch.modules.correlation.features import Location, ObservationFeatures
from ecowatch.modules.correlation.models import (
    CorrelationCluster,
    EvidenceRelationship,
    RelationshipStatus,
)
from ecowatch.modules.correlation.policy import policy_for
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

        # One policy for retrieval and scoring, so a candidate cannot be
        # retrieved on a wide window and then scored to zero on a narrow one.
        bounds = policy_for(
            subject.observationType, has_location=subjectFeatures.location is not None
        )

        candidateFeatures = [
            features_for(
                candidate,
                locationWkt=candidateWkt,
                sourceRef=candidate.sourceRef,
                dialectName=dialectName,
            )
            for candidate, candidateWkt in self._repo.candidate_rows(
                subject, limit=MAX_CANDIDATES, policy=bounds
            )
        ]

        # Every scanned report gets a provisional home, even when nothing matched,
        # so a reviewer can find it. This claims nothing about the report.
        self._repo.ensure_cluster(subject.organisationId, subject.id)

        decided = self._repo.decided_partner_ids(subject.id)
        ranking = rank(
            subjectFeatures,
            candidateFeatures,
            temporal_window_hours=bounds.window_hours,
            radius_km=bounds.radius_km,
        )
        written = 0
        for position, suggestion in enumerate(ranking.suggestions):
            partnerId = uuid.UUID(suggestion.observation_b_id)
            task = task_for(suggestion)
            if partnerId in decided or task is None:
                continue
            self._repo.upsert_suggestion(
                organisationId=subject.organisationId,
                firstId=subject.id,
                secondId=partnerId,
                task=task.value,
                score=suggestion.score,
                components=dict(suggestion.components),
                missingSignals=list(suggestion.missing_signals),
                # The task's own wording leads, so a reviewer sees what kind of
                # link this is before the individual signals that support it.
                reasons=[TASK_REASONS[task], *suggestion.reasons],
                sourceIndependent=suggestion.source_independent,
                # A tie is for a person to break, so both ends of it are marked
                # rather than ordered and left to look decisive.
                ambiguous=ranking.ambiguous_at_top and position < 2,
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

        relationship = self._require_reviewable(principal, relationshipId)

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

    def _require_reviewable(
        self, principal: Principal, relationshipId: uuid.UUID
    ) -> EvidenceRelationship:
        """Load a suggestion the caller may act on, or raise the same 404.

        A caller without permission gets the same answer as one asking about a
        record that does not exist, so existence does not leak across tenants.
        """
        relationship = self._repo.get_relationship(relationshipId)
        if relationship is None or not principal.has_permission(
            Permission.CORRELATION_REVIEW, relationship.organisationId
        ):
            raise DomainError(
                ErrorCode.NOT_FOUND,
                "Suggestion not found",
                statusCode=status.HTTP_404_NOT_FOUND,
            )
        return relationship

    def reopen(
        self,
        principal: Principal,
        relationshipId: uuid.UUID,
        *,
        reason: str,
        requestId: str | None = None,
    ) -> EvidenceRelationship:
        """Return a decided suggestion to the queue, so it can be decided again.

        The row holds current state only: the decision fields are cleared, and the
        previous decision stays in `audit_events`, which is append-only. That is
        what makes reversal an action rather than an edit.

        A reason is required. Reopening silently is how a decision gets undone
        without anyone being able to say why.
        """
        relationship = self._require_reviewable(principal, relationshipId)
        previous = relationship.status
        if previous == RelationshipStatus.SUGGESTED.value:
            raise DomainError(
                ErrorCode.INVALID_STATUS_TRANSITION,
                "Suggestion is already open; there is no decision to reopen",
                statusCode=status.HTTP_409_CONFLICT,
            )

        relationship.status = RelationshipStatus.SUGGESTED.value
        relationship.decidedByUserId = None
        relationship.decidedAt = None
        relationship.decisionReason = None

        record_audit_event(
            self._session,
            actorUserId=principal.userId,
            actorRole=principal.primary_role_label,
            action="correlation.reopened",
            targetType="evidence_relationship",
            targetId=relationship.id,
            organisationId=relationship.organisationId,
            reason=reason,
            details={
                "previousStatus": previous,
                "observationAId": str(relationship.observationAId),
                "observationBId": str(relationship.observationBId),
                "task": relationship.task,
            },
            requestId=requestId,
        )
        self._session.commit()
        return relationship

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

    def list_clusters(
        self, principal: Principal, *, limit: int = 50
    ) -> list[tuple[CorrelationCluster, list[uuid.UUID]]]:
        """Provisional clusters visible to the caller. Staff-only by permission."""
        organisationIds = (
            self._repo.all_org_ids()
            if principal.is_system_admin
            else principal.accessible_org_ids(Permission.CORRELATION_READ)
        )
        return self._repo.clusters_with_members(organisationIds)[:limit]


def enqueue_scan(session: Session, observationId: uuid.UUID) -> uuid.UUID:
    """Queue a scan so intake latency never includes scoring (`NFR-001`)."""
    job = JobsRepository(session).enqueue(
        SCAN_JOB_TYPE, {"observationId": str(observationId)}
    )
    return job.id
