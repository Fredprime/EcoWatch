"""SQLAlchemy repository for cases, case-observation links, and cross-module lookups."""

import uuid
from datetime import datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy import Boolean, DateTime, String, Text, Uuid, and_, or_, select
from sqlalchemy.orm import Session

from ecowatch.core.pagination import paginate_descending
from ecowatch.modules.cases.models import Case, CaseObservation


class CaseRepository:
    """Data-access operations for cases and decoupled cross-module table lookups."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def _reflected_table(
        self, tableName: str, candidateColumns: dict[str, Any]
    ) -> sa.TableClause | None:
        """Build a sa.table(...) containing only columns present in the live schema."""
        bind = self._session.get_bind()
        if bind is None:
            return None
        inspector = sa.inspect(bind)
        if not inspector.has_table(tableName):
            return None
        existing = {col["name"] for col in inspector.get_columns(tableName)}
        selectedCols = [
            sa.column(name, colType)
            for name, colType in candidateColumns.items()
            if name in existing
        ]
        return sa.table(tableName, *selectedCols) if selectedCols else None

    def _active_record_exists(self, tableName: str, recordId: uuid.UUID) -> bool:
        tableClause = self._reflected_table(
            tableName,
            {"id": Uuid(as_uuid=True), "is_active": Boolean},
        )
        if tableClause is None or "id" not in tableClause.c or "is_active" not in tableClause.c:
            return False
        row = self._session.execute(
            select(tableClause.c.id).where(
                tableClause.c.id == recordId,
                tableClause.c.is_active.is_(True),
            )
        ).one_or_none()
        return row is not None

    def organisation_exists(self, organisationId: uuid.UUID) -> bool:
        """Return True if an active organisation exists without importing identity models."""
        return self._active_record_exists("organisations", organisationId)

    def user_exists(self, userId: uuid.UUID) -> bool:
        """Return True if an active user exists without importing identity models."""
        return self._active_record_exists("users", userId)

    def user_has_active_membership(self, userId: uuid.UUID, organisationId: uuid.UUID) -> bool:
        """Return True if the user has at least one active membership in the organisation."""
        membershipsTable = self._reflected_table(
            "memberships",
            {
                "user_id": Uuid(as_uuid=True),
                "organisation_id": Uuid(as_uuid=True),
                "is_active": Boolean,
            },
        )
        if (
            membershipsTable is None
            or "user_id" not in membershipsTable.c
            or "organisation_id" not in membershipsTable.c
            or "is_active" not in membershipsTable.c
        ):
            return False
        row = self._session.execute(
            select(membershipsTable.c.user_id)
            .where(
                membershipsTable.c.user_id == userId,
                membershipsTable.c.organisation_id == organisationId,
                membershipsTable.c.is_active.is_(True),
            )
            .limit(1)
        ).first()
        return row is not None

    def lookup_observation(self, observationId: uuid.UUID) -> dict[str, Any] | None:
        """Fetch observation scope fields via reflection without importing observations.models."""
        obsTable = self._reflected_table(
            "observations",
            {
                "id": Uuid(as_uuid=True),
                "organisation_id": Uuid(as_uuid=True),
                "submitted_by_user_id": Uuid(as_uuid=True),
            },
        )
        if obsTable is None or "id" not in obsTable.c or "organisation_id" not in obsTable.c:
            return None
        row = (
            self._session.execute(select(obsTable).where(obsTable.c.id == observationId))
            .mappings()
            .one_or_none()
        )
        return dict(row) if row is not None else None

    def list_observation_rows(self, observationIds: list[uuid.UUID]) -> list[dict[str, Any]]:
        """Fetch temporal and provenance metadata for linked observations via reflection."""
        if not observationIds:
            return []
        obsTable = self._reflected_table(
            "observations",
            {
                "id": Uuid(as_uuid=True),
                "organisation_id": Uuid(as_uuid=True),
                "submitted_by_user_id": Uuid(as_uuid=True),
                "event_start_at": DateTime(timezone=True),
                "observed_at": DateTime(timezone=True),
                "submitted_at": DateTime(timezone=True),
                "received_at": DateTime(timezone=True),
                "time_precision": String(32),
                "source_type": String(64),
                "observation_type": String(64),
            },
        )
        if obsTable is None or "id" not in obsTable.c:
            return []
        rows = (
            self._session.execute(select(obsTable).where(obsTable.c.id.in_(observationIds)))
            .mappings()
            .all()
        )
        return [dict(row) for row in rows]

    def list_evidence_rows_for_observations(
        self, observationIds: list[uuid.UUID]
    ) -> list[dict[str, Any]]:
        """Fetch linked evidence_assets rows via reflection for timeline aggregation."""
        if not observationIds:
            return []
        evidenceTable = self._reflected_table(
            "evidence_assets",
            {
                "id": Uuid(as_uuid=True),
                "observation_id": Uuid(as_uuid=True),
                "received_at": DateTime(timezone=True),
                "created_at": DateTime(timezone=True),
                "media_type": String(128),
                "mime_type": String(128),
                "acquisition_method": String(64),
                "source": String(128),
            },
        )
        if (
            evidenceTable is None
            or "id" not in evidenceTable.c
            or "observation_id" not in evidenceTable.c
        ):
            return []
        rows = (
            self._session.execute(
                select(evidenceTable).where(evidenceTable.c.observation_id.in_(observationIds))
            )
            .mappings()
            .all()
        )
        return [dict(row) for row in rows]

    def list_case_audit_rows(
        self, caseId: uuid.UUID, linkIds: list[uuid.UUID]
    ) -> list[dict[str, Any]]:
        """Fetch audit_events rows for a case and its case_observation links via reflection."""
        auditTable = self._reflected_table(
            "audit_events",
            {
                "id": Uuid(as_uuid=True),
                "occurred_at": DateTime(timezone=True),
                "action": String(100),
                "target_type": String(64),
                "target_id": Uuid(as_uuid=True),
                "actor_role": String(64),
                "reason": Text,
            },
        )
        if auditTable is None:
            return []
        caseFilter = and_(
            auditTable.c.target_type == "case",
            auditTable.c.target_id == caseId,
        )
        if linkIds:
            linkFilter = and_(
                auditTable.c.target_type == "case_observation",
                auditTable.c.target_id.in_(linkIds),
            )
            whereClause = or_(caseFilter, linkFilter)
        else:
            whereClause = caseFilter
        rows = (
            self._session.execute(
                select(auditTable)
                .where(whereClause)
                .order_by(auditTable.c.occurred_at.asc(), auditTable.c.id.asc())
            )
            .mappings()
            .all()
        )
        return [dict(row) for row in rows]

    def get_case(self, caseId: uuid.UUID) -> Case | None:
        return self._session.get(Case, caseId)

    def get_case_by_code(self, caseCode: str) -> Case | None:
        return self._session.scalar(select(Case).where(Case.caseCode == caseCode))

    def get_public_case(self, caseId: uuid.UUID) -> Case | None:
        return self._session.scalar(
            select(Case).where(
                Case.id == caseId,
                Case.isPublicSummaryApproved.is_(True),
                Case.publicSummary.is_not(None),
            )
        )

    def create_case(
        self,
        *,
        organisationId: uuid.UUID,
        caseCode: str,
        title: str,
        summary: str,
        statusValue: str,
        statusRationale: str,
        areaGeometry: str | None,
        publicGeometry: str | None,
        areaReference: str | None,
        leadInvestigatorId: uuid.UUID | None,
        investigationQuestions: list[str],
        competingHypotheses: list[str],
        evidenceGaps: list[str],
        accessClass: str,
        publicSummary: str | None,
        createdByUserId: uuid.UUID,
        lastReviewedAt: datetime | None,
    ) -> Case:
        case = Case(
            organisationId=organisationId,
            caseCode=caseCode,
            title=title,
            summary=summary,
            status=statusValue,
            statusRationale=statusRationale,
            areaGeometry=areaGeometry,
            publicGeometry=publicGeometry,
            areaReference=areaReference,
            leadInvestigatorId=leadInvestigatorId,
            investigationQuestions=investigationQuestions,
            competingHypotheses=competingHypotheses,
            evidenceGaps=evidenceGaps,
            accessClass=accessClass,
            isPublicSummaryApproved=False,
            publicSummary=publicSummary,
            createdByUserId=createdByUserId,
            lastReviewedAt=lastReviewedAt,
        )
        self._session.add(case)
        self._session.flush()
        return case

    def list_cases(
        self,
        *,
        organisationIds: set[uuid.UUID] | None = None,
        organisationId: uuid.UUID | None = None,
        statusFilter: str | None = None,
        leadInvestigatorId: uuid.UUID | None = None,
        cursor: str | None = None,
        limit: int = 50,
    ) -> tuple[list[Case], str | None, bool]:
        if organisationIds is not None and not organisationIds:
            return [], None, False

        stmt = select(Case)
        if organisationIds is not None:
            stmt = stmt.where(Case.organisationId.in_(organisationIds))
        if organisationId is not None:
            stmt = stmt.where(Case.organisationId == organisationId)
        if statusFilter is not None:
            stmt = stmt.where(Case.status == statusFilter)
        if leadInvestigatorId is not None:
            stmt = stmt.where(Case.leadInvestigatorId == leadInvestigatorId)
        return paginate_descending(
            self._session,
            stmt,
            timeCol=Case.createdAt,
            idCol=Case.id,
            cursor=cursor,
            limit=limit,
        )

    def list_public_cases(
        self,
        *,
        cursor: str | None = None,
        limit: int = 50,
    ) -> tuple[list[Case], str | None, bool]:
        stmt = select(Case).where(
            Case.isPublicSummaryApproved.is_(True),
            Case.publicSummary.is_not(None),
        )
        return paginate_descending(
            self._session,
            stmt,
            timeCol=Case.createdAt,
            idCol=Case.id,
            cursor=cursor,
            limit=limit,
        )

    def get_case_observation(
        self, caseId: uuid.UUID, observationId: uuid.UUID
    ) -> CaseObservation | None:
        return self._session.scalar(
            select(CaseObservation).where(
                CaseObservation.caseId == caseId,
                CaseObservation.observationId == observationId,
            )
        )

    def get_cluster_for_action(
        self, clusterId: uuid.UUID
    ) -> tuple[uuid.UUID, list[uuid.UUID]] | None:
        """Return (organisationId, member observation ids) for a provisional cluster."""
        clusterTable = self._reflected_table(
            "correlation_clusters",
            {"id": Uuid(as_uuid=True), "organisation_id": Uuid(as_uuid=True)},
        )
        memberTable = self._reflected_table(
            "correlation_cluster_members",
            {"cluster_id": Uuid(as_uuid=True), "observation_id": Uuid(as_uuid=True)},
        )
        if clusterTable is None or memberTable is None:
            return None
        row = self._session.execute(
            select(clusterTable.c.organisation_id).where(clusterTable.c.id == clusterId)
        ).one_or_none()
        if row is None:
            return None
        memberRows = self._session.execute(
            select(memberTable.c.observation_id).where(memberTable.c.cluster_id == clusterId)
        ).all()
        return row.organisation_id, [member.observation_id for member in memberRows]

    def move_case_observation(self, linkId: uuid.UUID, targetCaseId: uuid.UUID) -> None:
        """Repoint an existing case-observation link to another case."""
        link = self._session.get(CaseObservation, linkId)
        if link is not None:
            link.caseId = targetCaseId
            self._session.flush()

    def delete_case_observation(self, linkId: uuid.UUID) -> None:
        """Remove a duplicate link row after its observation was moved elsewhere."""
        link = self._session.get(CaseObservation, linkId)
        if link is not None:
            self._session.delete(link)
            self._session.flush()

    def list_case_observations(self, caseId: uuid.UUID) -> list[CaseObservation]:
        return list(
            self._session.scalars(
                select(CaseObservation)
                .where(CaseObservation.caseId == caseId)
                .order_by(CaseObservation.createdAt.asc(), CaseObservation.id.asc())
            ).all()
        )

    def create_case_observation(
        self,
        *,
        caseId: uuid.UUID,
        observationId: uuid.UUID,
        linkRationale: str,
        proposedByType: str,
        proposedByUserId: uuid.UUID | None,
        reviewStatus: str,
        reviewedByUserId: uuid.UUID | None,
        reviewedAt: datetime | None,
        isContested: bool,
        contestedNote: str | None,
    ) -> CaseObservation:
        link = CaseObservation(
            caseId=caseId,
            observationId=observationId,
            linkRationale=linkRationale,
            proposedByType=proposedByType,
            proposedByUserId=proposedByUserId,
            reviewStatus=reviewStatus,
            reviewedByUserId=reviewedByUserId,
            reviewedAt=reviewedAt,
            isContested=isContested,
            contestedNote=contestedNote,
        )
        self._session.add(link)
        self._session.flush()
        return link
