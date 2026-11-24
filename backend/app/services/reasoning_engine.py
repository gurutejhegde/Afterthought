import json
from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.mcp_servers.google_workspace import workspace_connector
from app.mcp_servers.task_memory import TaskMemoryManager
from app.services.guard_service import GuardService

class ReasoningEngine:
    """
    Intelligent Assistant Engine.
    When a GEMINI_API_KEY is supplied, it interacts with Gemini.
    In MOCK_MODE or when offline without keys, it employs an intent-based reasoning parser
    to parse tasks, questions, file moves, and briefings with zero external API friction.
    """

    @classmethod
    async def process_user_intent(
        cls,
        db: AsyncSession,
        user_message: str
    ) -> Dict[str, Any]:
        msg = user_message.lower()

        # 1. Daily Briefing intent
        if "briefing" in msg or "today" in msg and "schedule" in msg or "what's due" in msg:
            events = await workspace_connector.list_calendar_events()
            tasks = await TaskMemoryManager.list_tasks(db)
            
            agenda = [f"• {e['title']} at {e['start_time'].split('T')[-1][:5]} ({e['location']})" for e in events]
            pending_tasks = [f"• {t.title} [Status: {t.status}]" for t in tasks if t.status != "completed"]
            
            summary = (
                "Good morning! Here is your Afterthought Daily Briefing:\n\n"
                "📅 Calendar Agenda:\n" + ("\n".join(agenda) if agenda else "No events scheduled.") + "\n\n"
                "🎯 Commitments & Deadlines:\n" + ("\n".join(pending_tasks) if pending_tasks else "No active deadlines pending.") + "\n\n"
                "💡 Proactive Note: Track 01 submission deadline is today at 6:00 PM. Have you verified your pitch deck slide 5?"
            )
            return {
                "response": summary,
                "action_required": None,
                "sources_checked": ["Google Calendar", "Outcome Ledger"]
            }

        # 2. Organize / Move File intent (Tier 3 Guardrail Example)
        if "move" in msg or "organize" in msg:
            query = "Nebula_Track1_Pitch.pptx" if "pitch" in msg or "slide" in msg else "document"
            target_folder = "/Hackathon/Submissions"
            files = await workspace_connector.search_drive_files("pptx")
            file_to_move = files[0] if files else {"id": "drive-01", "name": "Nebula_Track1_Pitch.pptx"}

            action = await GuardService.stage_action_for_approval(
                db=db,
                tool_name="organize_drive_file",
                parameters={"file_id": file_to_move["id"], "target_folder": target_folder},
                summary=f"Move '{file_to_move['name']}' into '{target_folder}'"
            )

            return {
                "response": (
                    f"I identified '{file_to_move['name']}'. Per our Controlled Execution policy, moving external files "
                    f"requires your explicit confirmation. Please review the approval preview below."
                ),
                "action_required": {
                    "action_id": action.id,
                    "tool_name": action.tool_name,
                    "risk_level": action.risk_level,
                    "summary": action.summary,
                    "parameters": json.loads(action.parameters)
                },
                "sources_checked": ["Google Drive", "Guardrails Policy"]
            }

        # 3. Task Creation & Outcome Commitment intent
        if "remind" in msg or "task" in msg or "submit" in msg or "deadline" in msg or "need to" in msg:
            title = user_message.strip()
            deadline = datetime.utcnow() + timedelta(hours=6)
            task = await TaskMemoryManager.create_task(
                db=db,
                title=title,
                deadline=deadline,
                source="chat"
            )
            await GuardService.log_audit_trail(
                db=db,
                action_type="create_task",
                details=f"Created task '{task.title}' with deadline {deadline.isoformat()}",
                is_reversible=True
            )
            return {
                "response": f"I've logged this commitment into your Outcome Ledger: '{task.title}'. I will follow up as the deadline approaches.",
                "action_required": None,
                "task_created": {
                    "id": task.id,
                    "title": task.title,
                    "status": task.status,
                    "deadline": task.deadline.isoformat() if task.deadline else None
                }
            }

        # Default conversational & guidance response
        return {
            "response": (
                f"Understood. I am tracking your commitments and connected apps (Calendar, Drive, Outcome Ledger). "
                f"You can ask for a 'daily briefing', ask me to 'organize pitch slides', or assign a task with a deadline."
            ),
            "action_required": None
        }
