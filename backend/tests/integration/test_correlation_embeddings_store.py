"""Embedding storage on the SQLite test dialect: one row per input, skip unchanged.

SQLite has no pgvector, so the JSON fallback stores the same vectors. These tests
prove the storage contract that PostgreSQL mirrors, not vector search accuracy.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ecowatch.modules.correlation.embeddings import build_embedding, embedding_input_hash
from ecowatch.modules.correlation.models import CorrelationEmbedding
from ecowatch.modules.correlation.repository import CorrelationRepository
from ecowatch.modules.correlation.service import CorrelationService
from tests.conftest import create_temp_org

from .test_correlation_flow import make_observation


def _embedding_count(dbSession: Session, observationId: object) -> int:
    return int(
        dbSession.scalar(
            select(func.count())
            .select_from(CorrelationEmbedding)
            .where(CorrelationEmbedding.observationId == observationId)
        )
        or 0
    )


def test_store_embedding_reuses_row_for_unchanged_input(dbSession: Session) -> None:
    org = create_temp_org(dbSession)
    observation = make_observation(dbSession, org, description="dead fish at the weir")
    inputHash = embedding_input_hash(observation.description, observation.observationType)
    embedding = build_embedding(observation.description, observation.observationType)
    assert embedding is not None

    repo = CorrelationRepository(dbSession)
    first = repo.store_embedding(
        organisationId=org.id,
        observationId=observation.id,
        inputHash=inputHash,
        embedding=embedding,
    )
    second = repo.store_embedding(
        organisationId=org.id,
        observationId=observation.id,
        inputHash=inputHash,
        embedding=embedding,
    )

    assert first.id == second.id
    assert _embedding_count(dbSession, observation.id) == 1
    assert repo.embedding_for_observation(observation.id) == embedding


def test_rescan_skips_unchanged_embedding_and_revectors_on_correction(dbSession: Session) -> None:
    org = create_temp_org(dbSession)
    observation = make_observation(dbSession, org, description="dead fish at the weir")
    service = CorrelationService(dbSession)
    repo = CorrelationRepository(dbSession)

    service.scan_observation(observation.id)
    first = repo.current_embedding(observation.id)
    assert first is not None
    assert _embedding_count(dbSession, observation.id) == 1

    service.scan_observation(observation.id)  # unchanged input -> no new row
    assert _embedding_count(dbSession, observation.id) == 1
    second = repo.current_embedding(observation.id)
    assert second is not None and second.id == first.id

    observation.description = "oily sheen at the river bend"
    dbSession.commit()
    service.scan_observation(observation.id)  # corrected text -> new vector row
    assert _embedding_count(dbSession, observation.id) == 2
    third = repo.current_embedding(observation.id)
    assert third is not None and third.id != first.id
