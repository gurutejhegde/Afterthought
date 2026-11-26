import json
import re
from typing import Dict, Any, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.models import PendingAction, AuditLog, Task
from app.mcp_servers.google_workspace import workspace_connector


INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior)\s+instructions", re.IGNORECASE),
    re.compile(r"disregard\s+(your\s+)?system\s+prompt", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(in\s+)?developer\s+mode", re.IGNORECASE),
    re.compile(r"execute\s+shell|run\s+command|exfiltrate", re.IGNORECASE),
]


class GuardService:
    """
    Controlled execution and prompt-injection defense layer.
    Categorizes tools into Risk Tiers:
    - Tier 1 (Read-Only): Immediate execution.
    - Tier 2 (Safe Modification): Auto-logged execution with undo ledger.
    - Tier 3 (External / Destructive): Staged for explicit user approval before execution.
    """

    TOOL_TIERS = {
        "list_calendar_events": "TIER_1",
        "get_calendar_agenda": "TIER_1",
        "search_drive_files": "TIER_1",
        "search_drive_documents": "TIER_1",
        "list_emails": "TIER_1",
        "get_unread_emails": "TIER_1",
        "list_tasks": "TIER_1",
        "list_active_tasks": "TIER_1",
        "list_outcomes": "TIER_1",
        "create_task": "TIER_2",
        "create_tracked_task": "TIER_2",
        "record_outcome": "TIER_2",
        "log_outcome_record": "TIER_2",
        "update_task_status": "TIER_2",
        "update_task_outcome": "TIER_2",
        "create_calendar_event": "TIER_3",
        "organize_drive_file": "TIER_3",
        "delete_task": "TIER_3",
    }

    @classmethod
    def evaluate_tool_risk(cls, tool_name: str) -> str:
        return cls.TOOL_TIERS.get(tool_name, "TIER_3")

    @classmethod
    def sanitize_external_content(cls, content: str, source: str) -> Tuple[str, bool]:
        """
        Wrap untrusted external content (emails, Drive snippets, calendar text) as passive data
        and detect potential prompt-injection attempts.
        """
        flagged = any(pattern.search(content) for pattern in INJECTION_PATTERNS)
        sanitized = content.replace("</untrusted_data>", "[/untrusted_data]")
        wrapped = (
            f'<untrusted_data source="{source}" injection_flagged="{str(flagged).lower()}">\n'
            f"{sanitized}\n"
            f"</untrusted_data>"
        )
        return wrapped, flagged

    @classmethod
    async def stage_action_for_approval(
        cls,
        db: AsyncSession,
        tool_name: str,
        parameters: Dict[str, Any],
        summary: str,
    ) -> PendingAction:
        risk_level = "HIGH" if cls.evaluate_tool_risk(tool_name) == "TIER_3" else "MEDIUM"
        action = PendingAction(
            tool_name=tool_name,
            parameters=json.dumps(parameters),
            risk_level=risk_level,
            summary=summary,
            status="pending_approval",
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
        undo_payload: Optional[str] = None,
    ) -> AuditLog:
        log = AuditLog(
            action_type=action_type,
            details=details,
            is_reversible=is_reversible,
            undo_payload=undo_payload,
        )
        db.add(log)
        await db.commit()
        await db.refresh(log)
        return log

    @classmethod
    async def execute_undo(cls, db: AsyncSession, audit_id: str) -> Dict[str, Any]:
        """Reverse a previously logged reversible action using its stored undo payload."""
        result = await db.execute(select(AuditLog).where(AuditLog.id == audit_id))
        log = result.scalar_one_or_none()
        if not log:
            return {"error": "Audit log not found"}
        if not log.is_reversible or not log.undo_payload:
            return {"error": "Action is not reversible"}
        if log.undone:
            return {"error": "Action has already been undone"}

        payload = json.loads(log.undo_payload)
        tool = payload.get("tool_name")
        undo_result: Dict[str, Any] = {}

        if tool == "organize_drive_file":
            undo_result = await workspace_connector.organize_drive_file(
                file_id=payload["file_id"],
                target_folder=payload["restore_folder"],
            )
        elif tool == "create_calendar_event":
            undo_result = await workspace_connector.delete_calendar_event(payload["event_id"])
        elif tool == "create_task":
            task_res = await db.execute(select(Task).where(Task.id == payload["task_id"]))
            task = task_res.scalar_one_or_none()
            if task:
                await db.delete(task)
                undo_result = {"deleted_task_id": payload["task_id"]}
        elif tool == "update_task_status":
            task_res = await db.execute(select(Task).where(Task.id == payload["task_id"]))
            task = task_res.scalar_one_or_none()
            if task:
                task.status = payload["previous_status"]
                undo_result = {"restored_task_id": task.id, "status": task.status}
        else:
            return {"error": f"Unsupported undo tool: {tool}"}

        log.undone = True
        await cls.log_audit_trail(
            db=db,
            action_type=f"undo_{tool}",
            details=f"Reverted audit action {audit_id}: {log.details}",
            is_reversible=False,
        )
        await db.commit()
        return {"status": "undone", "result": undo_result}
