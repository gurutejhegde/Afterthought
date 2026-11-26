from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=AsyncSession,
)

Base = declarative_base()


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await seed_initial_data()


async def seed_initial_data():
    """Populate realistic initial hackathon demo data when the database is empty."""
    from app.db.models import Task, OutcomeRecord, FollowUpNudge

    async with AsyncSessionLocal() as session:
        count_result = await session.execute(select(func.count(Task.id)))
        if (count_result.scalar() or 0) > 0:
            return

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        seed_tasks = [
            Task(
                title="Verify Track 01 architecture slide & MCP flow",
                description="Review Nebula_Track1_Pitch.pptx slide 5 before mentor check-in.",
                source="drive",
                status="in_progress",
                deadline=now + timedelta(hours=3),
                updated_at=now - timedelta(hours=14),
            ),
            Task(
                title="Submit wHACKiest 2026 MVP repository & demo video",
                description="Upload GitHub repo link and recorded briefing + approval walkthrough.",
                source="calendar",
                status="pending",
                deadline=now + timedelta(hours=8),
            ),
            Task(
                title="Reply to mentor email on prompt-injection guardrails",
                description="Confirm external email/Drive data is sandboxed from system instructions.",
                source="email",
                status="pending",
                deadline=now - timedelta(hours=1),
            ),
        ]
        session.add_all(seed_tasks)

        seed_outcomes = [
            OutcomeRecord(
                title="Dual-mode Google Workspace connector",
                category="decision",
                details="Run rich seeded mock mode when OAuth credentials are absent so demos never block.",
                status="active",
            ),
            OutcomeRecord(
                title="Add WhatsApp & Notion MCP connectors post-MVP",
                category="idea",
                details="Deferred until core Calendar + Drive + Outcome Ledger loop is verified.",
                status="active",
            ),
        ]
        session.add_all(seed_outcomes)
        await session.flush()

        nudge = FollowUpNudge(
            task_id=seed_tasks[0].id,
            reason="stalled",
            message=(
                f"'{seed_tasks[0].title}' has had no progress for 14h. "
                "Is slide 5 verified, or is someone else reviewing it?"
            ),
            status="pending",
        )
        session.add(nudge)
        await session.commit()
