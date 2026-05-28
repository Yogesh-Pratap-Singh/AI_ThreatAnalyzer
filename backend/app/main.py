import asyncio
from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import auth, ingest, alerts, feedback, reports
from app.workers.normalization_worker import start_normalization_worker
from app.workers.scoring_worker import start_scoring_worker
from app.workers.alert_worker import start_alert_worker

# Set up logging configuration
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start background workers inside FastAPI lifespan
    logger.info("Initializing background processing pipeline workers...")
    norm_task = asyncio.create_task(start_normalization_worker())
    score_task = asyncio.create_task(start_scoring_worker())
    alert_task = asyncio.create_task(start_alert_worker())
    
    yield
    
    # Shutdown: Cancel workers on exit
    logger.info("Shutting down background workers...")
    norm_task.cancel()
    score_task.cancel()
    alert_task.cancel()
    
    # Await cancellation completion to prevent resource leaks
    await asyncio.gather(norm_task, score_task, alert_task, return_exceptions=True)
    logger.info("Background workers shut down successfully.")

app = FastAPI(
    title="AI Threat Analyzer API",
    version="1.0.0",
    lifespan=lifespan
)

# Set up CORS middleware
# Next.js frontend runs on port 3000
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers with prefix /api/v1
app.include_router(auth.router, prefix="/api/v1")
app.include_router(ingest.router, prefix="/api/v1")
app.include_router(alerts.router, prefix="/api/v1")
app.include_router(feedback.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")

@app.get("/api/v1/health", status_code=status.HTTP_200_OK, tags=["system"])
async def health_check():
    return {
        "status": "ok",
        "version": "1.0.0",
        "database": "connected"  # Baseline health check indicator
    }
