import json
from typing import Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import PendingAction, AuditLog

class GuardService:
    """
    Controlled execution and prompt-injection defense layer.
    Categorizes tools into Risk Tiers:
    - Tier 1 (Read-Only): Immediate execution (e.g. list_tasks, search_drive).
    - Tier 2 (Safe Modification): Auto-logged execution with undo ledger (e.g. create_task, record_outcome).
    - Tier 3 (External / Destructive): Staged for explicit user approval before execution (e.g. organize_drive_file, delete_task).
    """

    TOOL_TIERS = {
        "list_calendar_events": "TIER_1",
        "search_drive_files": "TIER_1",
        "list_tasks": "TIER_1",
        "list_outcomes": "TIER_1",
        "create_task": "TIER_2",
        "record_outcome": "TIER_2",
        "update_task_status": "TIER_2",
        "create_calendar_event": "TIER_3",
        "organize_drive_file": "TIER_3",
        "delete_task": "TIER_3",
    }

    @classmethod
    def evaluate_tool_risk(cls, tool_name: str) -> str:
        return cls.TOOL_TIERS.get(tool_name, "TIER_3")

    @classmethod
    async def stage_action_for_approval(
        cls,
        db: AsyncSession,
        tool_name: str,
        parameters: Dict[str, Any],
        summary: str
    ) -> PendingAction:
        risk_level = "HIGH" if cls.evaluate_tool_risk(tool_name) == "TIER_3" else "MEDIUM"
        action = PendingAction(
            tool_name=tool_name,
            parameters=json.dumps(parameters),
            risk_level=risk_level,
            summary=summary,
            status="pending_approval"
        )
        db.add(action)
        await db.commit()
        await db.refresh(action)
        return action

    @classmethod
    async def log_audit_trail(
        cls,
        db: AsyncSession,
        action_type: str,
        details: str,
        is_reversible: bool = False,
        undo_payload: str = None
    ) -> AuditLog:
        log = AuditLog(
            action_type=action_type,
            details=details,
            is_reversible=is_reversible,
            undo_payload=undo_payload
        )
        db.add(log)
        await db.commit()
        await db.refresh(log)
        return log
