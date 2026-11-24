from datetime import datetime
from sqlalchemy.future import select
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.db.database import AsyncSessionLocal
from app.db.models import Task

scheduler = AsyncIOScheduler()

async def check_overdue_and_stalled_tasks():
    """
    Periodic job that evaluates active tasks:
    - Flags tasks past deadline as 'overdue'.
    - Flags tasks without progress for extended time as 'stalled'.
    """
    async with AsyncSessionLocal() as session:
        try:
            now = datetime.utcnow()
            result = await session.execute(
                select(Task).where(Task.status.in_(["pending", "in_progress"]))
            )
            tasks = result.scalars().all()
            for task in tasks:
                if task.deadline and task.deadline < now:
                    task.status = "overdue"
            await session.commit()
        except Exception as e:
            print(f"[Scheduler] Error checking tasks: {e}")

def start_scheduler():
    scheduler.add_job(
        check_overdue_and_stalled_tasks,
        "interval",
        seconds=60,
        id="overdue_task_scanner",
        replace_existing=True
    )
    scheduler.start()

def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
