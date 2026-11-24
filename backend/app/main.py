from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.db.database import init_db
from app.api.routes import router
from app.services.scheduler_service import start_scheduler, stop_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables
    await init_db()
    # Start proactive background scheduler
    start_scheduler()
    yield
    # Clean shutdown of scheduler
    stop_scheduler()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Intelligent assistant with MCP-connected apps, outcome tracking, and controlled execution.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "mock_mode": settings.MOCK_MODE,
        "database": "sqlite_ready"
    }
