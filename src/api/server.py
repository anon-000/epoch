import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import admin, jobs, metrics, workers
from src.db.session import init_db, close_db
from src.queue.redis_queue import redis_queue

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("epoch.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Epoch API server...")
    await init_db()
    await redis_queue.connect()
    logger.info("Database and Redis connected.")
    yield
    logger.info("Shutting down Epoch API server...")
    await redis_queue.close()
    await close_db()


app = FastAPI(
    title="Epoch - Distributed Job Scheduler",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs.router, prefix="/api/v1")
app.include_router(workers.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(metrics.router, prefix="/api/v1")
