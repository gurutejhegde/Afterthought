from datetime import timedelta
from typing import Dict
from sqlalchemy.future import select
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.db.database import AsyncSessionLocal
from app.db.models import Task, FollowUpNudge, utc_now

scheduler = AsyncIOScheduler()
STALLED_THRESHOLD_HOURS = 12


async def check_overdue_and_stalled_tasks() -> Dict[str, int]:
    """
    Periodic job evaluating active tasks:
    - Flags tasks past deadline as 'overdue'.
    - Flags tasks without updates for STALLED_THRESHOLD_HOURS as 'stalled'.
    - Creates FollowUpNudge entries for newly flagged tasks without duplicate pending nudges.
    """
    summary = {"overdue_flagged": 0, "stalled_flagged": 0, "nudges_created": 0}
    async with AsyncSessionLocal() as session:
        try:
            now = utc_now()
            stalled_cutoff = now - timedelta(hours=STALLED_THRESHOLD_HOURS)

            result = await session.execute(
                select(Task).where(Task.status.in_(["pending", "in_progress"]))
            )
            tasks = result.scalars().all()

            for task in tasks:
                reason = None
                nudge_msg = None

                if task.deadline and task.deadline < now:
                    task.status = "overdue"
                    reason = "overdue"
                    nudge_msg = (
                        f"'{task.title}' passed its deadline. "
                        "Did you complete it (share evidence), or should we reschedule?"
                    )
                    summary["overdue_flagged"] += 1
                elif task.updated_at and task.updated_at < stalled_cutoff:
                    task.status = "stalled"
                    reason = "stalled"
                    nudge_msg = (
                        f"'{task.title}' has had no progress for over {STALLED_THRESHOLD_HOURS}h. "
                        "What is the next concrete step?"
                    )
                    summary["stalled_flagged"] += 1

                if reason and nudge_msg:
                    existing = await session.execute(
                        select(FollowUpNudge).where(
                            FollowUpNudge.task_id == task.id,
                            FollowUpNudge.status == "pending",
                        )
                    )
                    if not existing.scalar_one_or_none():
                        session.add(
                            FollowUpNudge(
                                task_id=task.id,
                                reason=reason,
                                message=nudge_msg,
                                status="pending",
                            )
                        )
                        summary["nudges_created"] += 1

            await session.commit()
        except Exception as e:
            print(f"[Scheduler] Error checking tasks: {e}")
    return summary


def start_scheduler():
    if not scheduler.running:
        scheduler.add_job(
            check_overdue_and_stalled_tasks,
            "interval",
            seconds=60,
            id="overdue_task_scanner",
            replace_existing=True,
        )
        scheduler.start()


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
