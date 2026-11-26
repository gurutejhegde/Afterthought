from typing import List, Optional
from datetime import datetime
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Task, OutcomeRecord


class TaskMemoryManager:
    """
    Outcome Ledger & Task Store managing persistent commitments,
    verification evidence, and tracked assumptions.
    """

    @staticmethod
    async def create_task(
        db: AsyncSession,
        title: str,
        description: Optional[str] = None,
        deadline: Optional[datetime] = None,
        source: str = "chat",
        assumption_notes: Optional[str] = None,
    ) -> Task:
        task = Task(
            title=title,
            description=description,
            deadline=deadline,
            source=source,
            status="pending",
            assumption_notes=assumption_notes,
        )
        db.add(task)
        await db.commit()
        await db.refresh(task)
        return task

    @staticmethod
    async def list_tasks(db: AsyncSession, status: Optional[str] = None) -> List[Task]:
        query = select(Task)
        if status:
            query = query.where(Task.status == status)
        result = await db.execute(query.order_by(Task.created_at.desc()))
        return list(result.scalars().all())

    @staticmethod
    async def update_task_status(
        db: AsyncSession,
        task_id: str,
        status: str,
        verification_evidence: Optional[str] = None,
    ) -> Optional[Task]:
        result = await db.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        if task:
            task.status = status
            if verification_evidence is not None:
                task.verification_evidence = verification_evidence
            await db.commit()
            await db.refresh(task)
        return task

    @staticmethod
    async def record_outcome(
        db: AsyncSession,
        title: str,
        category: str = "decision",
        details: Optional[str] = None,
    ) -> OutcomeRecord:
        record = OutcomeRecord(
            title=title,
            category=category,
            details=details,
            status="active",
        )
        db.add(record)
        await db.commit()
        await db.refresh(record)
        return record

    @staticmethod
    async def list_outcomes(db: AsyncSession) -> List[OutcomeRecord]:
        result = await db.execute(select(OutcomeRecord).order_by(OutcomeRecord.created_at.desc()))
        return list(result.scalars().all())
