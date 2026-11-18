"""Top-level API router mounting liveness, readiness, and /api/v1 module endpoints."""

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ecowatch.core.config import Settings, get_settings
from ecowatch.core.database import check_database_readiness, get_db
from ecowatch.core.schemas import CamelModel
from ecowatch.modules.audit.router import router as auditRouter
from ecowatch.modules.cases.router import router as casesRouter
from ecowatch.modules.collection.router import router as collectionRouter
from ecowatch.modules.evidence.router import router as evidenceRouter
from ecowatch.modules.identity.router import router as identityRouter
from ecowatch.modules.jobs.router import router as jobsRouter
from ecowatch.modules.notifications.router import router as notificationsRouter
from ecowatch.modules.observations.router import router as observationsRouter


class HealthResponse(CamelModel):
    """Service liveness and readiness status payload."""

    status: str
    database: str
    postgisVersion: str | None = None
    storageRootReady: bool = False


apiRouter = APIRouter()


@apiRouter.get("/health", response_model=HealthResponse, tags=["health"])
def health_check(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> HealthResponse | JSONResponse:
    """Verify database connectivity, PostGIS availability, and storage readiness."""
    try:
        dbReady, postgisVersion = check_database_readiness(db)
    except Exception:
        body = HealthResponse(
            status="degraded",
            database="unavailable",
            postgisVersion=None,
            storageRootReady=settings.storageRoot.exists(),
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=body.model_dump(by_alias=True),
        )
    return HealthResponse(
        status="ok" if dbReady else "degraded",
        database="ok" if dbReady else "unavailable",
        postgisVersion=postgisVersion,
        storageRootReady=settings.storageRoot.exists(),
    )


v1Router = APIRouter(prefix="/api/v1")
v1Router.include_router(identityRouter)
v1Router.include_router(collectionRouter)
v1Router.include_router(observationsRouter)
v1Router.include_router(evidenceRouter)
v1Router.include_router(casesRouter)
v1Router.include_router(notificationsRouter)
v1Router.include_router(auditRouter)
v1Router.include_router(jobsRouter)

apiRouter.include_router(v1Router)
