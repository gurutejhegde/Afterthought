import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.database import get_db
from app.db.models import Task, OutcomeRecord, PendingAction, AuditLog, FollowUpNudge, ChatMessage
from app.mcp_servers.google_workspace import workspace_connector
from app.mcp_servers.task_memory import TaskMemoryManager
from app.mcp_servers.task_memory_server import mcp_server
from app.services.reasoning_engine import ReasoningEngine
from app.services.guard_service import GuardService
from app.services.scheduler_service import check_overdue_and_stalled_tasks
from app.services.voice_service import VoiceService
from app.api.schemas import (
    ChatRequest,
    TaskCreateRequest,
    StatusUpdateRequest,
    OutcomeCreateRequest,
    OutcomeUpdateRequest,
    VoiceSynthesizeRequest,
)

router = APIRouter()


@router.post("/chat")
async def chat_endpoint(payload: ChatRequest, db: AsyncSession = Depends(get_db)):
    return await ReasoningEngine.process_user_intent(db, payload.message)


@router.get("/chat/history")
async def get_chat_history(limit: int = 40, db: AsyncSession = Depends(get_db)):
    return await ReasoningEngine.get_chat_history(db, limit=limit)


@router.delete("/chat/history")
async def clear_chat_history(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ChatMessage))
    for msg in result.scalars().all():
        await db.delete(msg)
    await db.commit()
    return {"status": "cleared"}


@router.get("/briefing")
async def get_daily_briefing(db: AsyncSession = Depends(get_db)):
    return await ReasoningEngine.process_user_intent(
        db, "daily briefing", persist_history=False
    )


@router.get("/workspace/overview")
async def get_workspace_overview():
    return await workspace_connector.get_workspace_snapshot()


@router.get("/mcp/tools")
async def list_mcp_tools():
    tools = await mcp_server.list_tools()
    return {
        "server_name": mcp_server.name,
        "tools": [
            {
                "name": t.name,
                "description": t.description,
                "risk_tier": GuardService.evaluate_tool_risk(t.name),
            }
            for t in tools
        ],
    }


@router.get("/tasks")
async def list_tasks(status: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    return await TaskMemoryManager.list_tasks(db, status=status)


@router.post("/tasks")
async def create_task(payload: TaskCreateRequest, db: AsyncSession = Depends(get_db)):
    task = await TaskMemoryManager.create_task(
        db=db,
        title=payload.title,
        description=payload.description,
        deadline=payload.deadline,
        source="manual",
    )
    await GuardService.log_audit_trail(
        db=db,
        action_type="create_task",
        details=f"Manually created task '{task.title}'",
        is_reversible=True,
        undo_payload=json.dumps({"tool_name": "create_task", "task_id": task.id}),
    )
    return task


@router.patch("/tasks/{task_id}/status")
async def update_task_status(
    task_id: str, payload: StatusUpdateRequest, db: AsyncSession = Depends(get_db)
):
    existing_res = await db.execute(select(Task).where(Task.id == task_id))
    existing = existing_res.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Task not found")

    previous_status = existing.status
    task = await TaskMemoryManager.update_task_status(
        db=db,
        task_id=task_id,
        status=payload.status,
        verification_evidence=payload.verification_evidence,
    )

    if payload.status == "completed":
        nudge_res = await db.execute(
            select(FollowUpNudge).where(
                FollowUpNudge.task_id == task_id,
                FollowUpNudge.status == "pending",
            )
        )
        for nudge in nudge_res.scalars().all():
            nudge.status = "resolved"
        await db.commit()

    await GuardService.log_audit_trail(
        db=db,
        action_type="update_task_status",
        details=f"Updated '{task.title}' from {previous_status} to {payload.status}",
        is_reversible=True,
        undo_payload=json.dumps({
            "tool_name": "update_task_status",
            "task_id": task.id,
            "previous_status": previous_status,
        }),
    )
    return task


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    title = task.title
    await db.delete(task)
    await GuardService.log_audit_trail(
        db=db,
        action_type="delete_task",
        details=f"Deleted task '{title}'",
        is_reversible=False,
    )
    await db.commit()
    return {"status": "deleted", "task_id": task_id}


@router.get("/outcomes")
async def list_outcomes(db: AsyncSession = Depends(get_db)):
    return await TaskMemoryManager.list_outcomes(db)


@router.post("/outcomes")
async def create_outcome(payload: OutcomeCreateRequest, db: AsyncSession = Depends(get_db)):
    record = await TaskMemoryManager.record_outcome(
        db=db, title=payload.title, category=payload.category, details=payload.details
    )
    await GuardService.log_audit_trail(
        db=db,
        action_type="record_outcome",
        details=f"Recorded {payload.category} '{record.title}'",
    )
    return record


@router.patch("/outcomes/{outcome_id}")
async def update_outcome(
    outcome_id: str, payload: OutcomeUpdateRequest, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(OutcomeRecord).where(OutcomeRecord.id == outcome_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Outcome record not found")
    record.status = payload.status
    await db.commit()
    await db.refresh(record)
    return record


@router.get("/followups")
async def list_followups(status: str = "pending", db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(FollowUpNudge)
        .where(FollowUpNudge.status == status)
        .order_by(FollowUpNudge.created_at.desc())
    )
    return result.scalars().all()


@router.post("/followups/scan")
async def trigger_followup_scan():
    return await check_overdue_and_stalled_tasks()


@router.post("/followups/{nudge_id}/resolve")
async def resolve_followup(nudge_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FollowUpNudge).where(FollowUpNudge.id == nudge_id))
    nudge = result.scalar_one_or_none()
    if not nudge:
        raise HTTPException(status_code=404, detail="Follow-up nudge not found")
    nudge.status = "resolved"
    await db.commit()
    return {"status": "resolved", "id": nudge_id}


@router.get("/actions/pending")
async def list_pending_actions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PendingAction)
        .where(PendingAction.status == "pending_approval")
        .order_by(PendingAction.created_at.desc())
    )
    return result.scalars().all()


@router.post("/actions/{action_id}/approve")
async def approve_action(action_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PendingAction).where(PendingAction.id == action_id))
    action = result.scalar_one_or_none()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    if action.status != "pending_approval":
        raise HTTPException(status_code=400, detail=f"Action already {action.status}")

    params = json.loads(action.parameters)
    execution_result = {}
    undo_payload = None
    is_reversible = False

    if action.tool_name == "organize_drive_file":
        execution_result = await workspace_connector.organize_drive_file(
            file_id=params["file_id"],
            target_folder=params["target_folder"],
        )
        if "old_folder" in execution_result:
            is_reversible = True
            undo_payload = json.dumps({
                "tool_name": "organize_drive_file",
                "file_id": params["file_id"],
                "restore_folder": execution_result["old_folder"],
            })
    elif action.tool_name == "create_calendar_event":
        execution_result = await workspace_connector.create_calendar_event(
            title=params.get("title", "Event"),
            start_time=params.get("start_time", ""),
            end_time=params.get("end_time", ""),
        )
        if "id" in execution_result:
            is_reversible = True
            undo_payload = json.dumps({
                "tool_name": "create_calendar_event",
                "event_id": execution_result["id"],
            })
    elif action.tool_name == "delete_task":
        task_res = await db.execute(select(Task).where(Task.id == params["task_id"]))
        task = task_res.scalar_one_or_none()
        if task:
            await db.delete(task)
            execution_result = {"deleted_task_id": params["task_id"]}

    action.status = "executed"
    audit_log = await GuardService.log_audit_trail(
        db=db,
        action_type=f"execute_{action.tool_name}",
        details=f"Approved and executed: {action.summary}",
        is_reversible=is_reversible,
        undo_payload=undo_payload,
    )
    await db.commit()
    return {"status": "executed", "result": execution_result, "audit_id": audit_log.id}


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
        details=f"User rejected action: {action.summary}",
    )
    await db.commit()
    return {"status": "rejected"}


@router.get("/audit")
async def get_audit_trail(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AuditLog).order_by(AuditLog.timestamp.desc()))
    return result.scalars().all()


@router.post("/audit/{audit_id}/undo")
async def undo_audit_entry(audit_id: str, db: AsyncSession = Depends(get_db)):
    result = await GuardService.execute_undo(db, audit_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# --- Voice Engine Endpoints ---

@router.get("/voice/status")
async def voice_status():
    return VoiceService.get_status()


@router.get("/voice/voices")
async def list_voices():
    return await VoiceService.list_voices()


@router.post("/voice/synthesize")
async def synthesize_voice(payload: VoiceSynthesizeRequest):
    audio_bytes = await VoiceService.synthesize_speech(payload.text, voice_id=payload.voice_id)
    if audio_bytes is None:
        return {
            "provider": "web_speech_fallback",
            "message": "ELEVENLABS_API_KEY not configured; use browser Web Speech API.",
            "speech_text": VoiceService.clean_text_for_speech(payload.text),
        }
    return Response(content=audio_bytes, media_type="audio/mpeg")


@router.post("/voice/transcribe")
async def transcribe_voice(audio: UploadFile = File(...)):
    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio upload")
    return await VoiceService.transcribe_audio(
        audio_bytes=audio_bytes,
        filename=audio.filename or "recording.webm",
        content_type=audio.content_type or "audio/webm",
    )


@router.post("/voice/chat")
async def voice_chat_turn(
    audio: Optional[UploadFile] = File(default=None),
    transcript: Optional[str] = Form(default=None),
    voice_id: Optional[str] = Form(default=None),
    db: AsyncSession = Depends(get_db),
):
    """
    Full voice-to-voice conversational turn:
    1. Accepts audio file (transcribed via ElevenLabs Scribe) OR text transcript (from Web Speech).
    2. Processes intent through ReasoningEngine (Gemini / offline fallback).
    3. Synthesizes reply audio via ElevenLabs TTS when configured.
    """
    stt_provider = "client_transcript"
    user_text = (transcript or "").strip()

    if not user_text and audio is not None:
        audio_bytes = await audio.read()
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="Empty audio file")
        stt_result = await VoiceService.transcribe_audio(
            audio_bytes=audio_bytes,
            filename=audio.filename or "recording.webm",
            content_type=audio.content_type or "audio/webm",
        )
        stt_provider = stt_result["provider"]
        if not stt_result.get("transcript"):
            return {
                "status": "fallback_required",
                "stt_provider": stt_provider,
                "tts_provider": VoiceService.get_status()["tts_provider"],
                "message": stt_result.get("message"),
            }
        user_text = stt_result["transcript"]

    if not user_text:
        raise HTTPException(status_code=400, detail="Provide either an audio file or a transcript")

    engine_result = await ReasoningEngine.process_user_intent(db, user_text)
    audio_b64 = await VoiceService.synthesize_speech_base64(
        engine_result["response"], voice_id=voice_id
    )

    return {
        "transcript": user_text,
        "stt_provider": stt_provider,
        "tts_provider": "elevenlabs" if audio_b64 else "web_speech_fallback",
        "speech_text": VoiceService.clean_text_for_speech(engine_result["response"]),
        "audio_base64": audio_b64,
        **engine_result,
    }
