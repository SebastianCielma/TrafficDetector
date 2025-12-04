from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.app.api.v1.router import router
from backend.app.core.config import settings
from backend.app.core.db import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    print(" Initializing Database connection...")
    try:
        await init_db()
        print("Database tables created successfully.")
    except Exception as e:
        print(f"Database connection failed: {e}")

    yield

    print("Shutting down application...")


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

app.include_router(router, prefix=settings.API_V1_STR)
app.mount("/results", StaticFiles(directory=settings.RESULTS_DIR), name="results")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
