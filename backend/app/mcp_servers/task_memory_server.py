"""
Standalone Model Context Protocol (MCP) Server for Afterthought Task & Outcome Ledger.
Can be run directly via stdio (`python -m app.mcp_servers.task_memory_server`)
or imported by the FastAPI backend for tool schema inspection and execution.
"""

from datetime import datetime
from typing import Optional
try:
    from mcp.server.mcpserver import MCPServer
except ImportError:
    from mcp.server.fastmcp import FastMCP as MCPServer
from app.db.database import AsyncSessionLocal, init_db
from app.mcp_servers.task_memory import TaskMemoryManager
from app.mcp_servers.google_workspace import workspace_connector

mcp_server = MCPServer("afterthought-task-memory")


@mcp_server.tool()
async def list_active_tasks(status: Optional[str] = None) -> list[dict]:
    """List tasks from the Afterthought Outcome Ledger, optionally filtered by status."""
    async with AsyncSessionLocal() as db:
        tasks = await TaskMemoryManager.list_tasks(db, status=status)
        return [
            {
                "id": t.id,
                "title": t.title,
                "status": t.status,
                "source": t.source,
                "deadline": t.deadline.isoformat() if t.deadline else None,
                "verification_evidence": t.verification_evidence,
            }
            for t in tasks
        ]


@mcp_server.tool()
async def create_tracked_task(
    title: str,
    description: Optional[str] = None,
    deadline_iso: Optional[str] = None,
    source: str = "mcp",
) -> dict:
    """Create a tracked commitment in the Outcome Ledger."""
    deadline = datetime.fromisoformat(deadline_iso) if deadline_iso else None
    async with AsyncSessionLocal() as db:
        task = await TaskMemoryManager.create_task(
            db=db,
            title=title,
            description=description,
            deadline=deadline,
            source=source,
        )
        return {
            "id": task.id,
            "title": task.title,
            "status": task.status,
            "deadline": task.deadline.isoformat() if task.deadline else None,
        }


@mcp_server.tool()
async def update_task_outcome(
    task_id: str,
    status: str,
    verification_evidence: Optional[str] = None,
) -> dict:
    """Update task status with verification evidence when closing or progressing work."""
    async with AsyncSessionLocal() as db:
        task = await TaskMemoryManager.update_task_status(
            db=db,
            task_id=task_id,
            status=status,
            verification_evidence=verification_evidence,
        )
        if not task:
            return {"error": f"Task {task_id} not found"}
        return {
            "id": task.id,
            "title": task.title,
            "status": task.status,
            "verification_evidence": task.verification_evidence,
        }


@mcp_server.tool()
async def log_outcome_record(title: str, category: str = "decision", details: Optional[str] = None) -> dict:
    """Persist a decision, intention, or unfinished idea into structured memory."""
    async with AsyncSessionLocal() as db:
        record = await TaskMemoryManager.record_outcome(
            db=db, title=title, category=category, details=details
        )
        return {
            "id": record.id,
            "title": record.title,
            "category": record.category,
            "status": record.status,
        }


@mcp_server.tool()
async def get_calendar_agenda() -> list[dict]:
    """Fetch upcoming events from the connected Google Calendar MCP connector."""
    return await workspace_connector.list_calendar_events()


@mcp_server.tool()
async def search_drive_documents(query: str = "") -> list[dict]:
    """Search documents in the connected Google Drive MCP connector."""
    return await workspace_connector.search_drive_files(query)


@mcp_server.tool()
async def get_unread_emails() -> list[dict]:
    """Fetch unread messages from the connected Gmail MCP connector."""
    return await workspace_connector.list_emails(unread_only=True)


if __name__ == "__main__":
    import asyncio

    asyncio.run(init_db())
    mcp_server.run()
