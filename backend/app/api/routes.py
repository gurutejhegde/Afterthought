import json
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.database import get_db
from app.db.models import Task, OutcomeRecord, PendingAction, AuditLog
from app.mcp_servers.google_workspace import workspace_connector
from app.services.reasoning_engine import ReasoningEngine
from app.services.guard_service import GuardService

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

class TaskCreateRequest(BaseModel):
    title: str
    description: Optional[str] = None
    deadline: Optional[datetime] = None

class StatusUpdateRequest(BaseModel):
    status: str
    verification_evidence: Optional[str] = None

@router.post("/chat")
async def chat_endpoint(payload: ChatRequest, db: AsyncSession = Depends(get_db)):
    result = await ReasoningEngine.process_user_intent(db, payload.message)
    return result

@router.get("/briefing")
async def get_daily_briefing(db: AsyncSession = Depends(get_db)):
    result = await ReasoningEngine.process_user_intent(db, "daily briefing")
    return result

@router.get("/tasks")
async def list_tasks(status: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    query = select(Task)
    if status:
        query = query.where(Task.status == status)
    result = await db.execute(query.order_by(Task.created_at.desc()))
    return result.scalars().all()

@router.post("/tasks")
async def create_task(payload: TaskCreateRequest, db: AsyncSession = Depends(get_db)):
    task = Task(
        title=payload.title,
        description=payload.description,
        deadline=payload.deadline,
        source="manual"
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task

@router.patch("/tasks/{task_id}/status")
async def update_task_status(task_id: str, payload: StatusUpdateRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.status = payload.status
    if payload.verification_evidence:
        task.verification_evidence = payload.verification_evidence
    await db.commit()
    await db.refresh(task)
    return task

@router.get("/actions/pending")
async def list_pending_actions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PendingAction).where(PendingAction.status == "pending_approval")
    )
    return result.scalars().all()

@router.post("/actions/{action_id}/approve")
async def approve_action(action_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PendingAction).where(PendingAction.id == action_id))
    action = result.scalar_one_or_none()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    
    params = json.loads(action.parameters)
    execution_result = {}
    
    # Execute verified tool
    if action.tool_name == "organize_drive_file":
        execution_result = await workspace_connector.organize_drive_file(
            file_id=params["file_id"],
            target_folder=params["target_folder"]
        )
    elif action.tool_name == "create_calendar_event":
        execution_result = await workspace_connector.create_calendar_event(
            title=params.get("title", "Event"),
            start_time=params.get("start_time", ""),
            end_time=params.get("end_time", "")
        )

    action.status = "executed"
    await GuardService.log_audit_trail(
        db=db,
        action_type=f"execute_{action.tool_name}",
        details=f"Approved and executed: {action.summary}",
        is_reversible=True,
        undo_payload=action.parameters
    )
    await db.commit()
    return {"status": "executed", "result": execution_result}

@router.post("/actions/{action_id}/reject")
async def reject_action(action_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PendingAction).where(PendingAction.id == action_id))
    action = result.scalar_one_or_none()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    
    action.status = "rejected"
    await GuardService.log_audit_trail(
        db=db,
        action_type=f"reject_{action.tool_name}",
        details=f"User rejected action: {action.summary}"
    )
    await db.commit()
    return {"status": "rejected"}

@router.get("/audit")
async def get_audit_trail(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AuditLog).order_by(AuditLog.timestamp.desc()))
    return result.scalars().all()
