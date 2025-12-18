from contextlib import asynccontextmanager

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.app.api.v1.router import router
from backend.app.core.config import init_directories, settings
from backend.app.core.db import init_db
from backend.app.core.logger import get_logger, setup_logging

logger = get_logger("main")


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    setup_logging()
    init_directories()

    logger.info("startup", message="Starting Traffic AI System...")

    try:
        await init_db()
        logger.info("db_connected", status="success")
    except Exception as e:
        logger.error("db_failed", error=str(e))

    yield

    logger.info("shutdown", message="Shutting down...")


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

app.add_middleware(CorrelationIdMiddleware)

app.include_router(router, prefix=settings.API_V1_STR)
app.mount("/results", StaticFiles(directory=settings.RESULTS_DIR), name="results")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
