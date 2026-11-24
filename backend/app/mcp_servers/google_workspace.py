from typing import List, Dict, Any, Optional
from datetime import datetime
from app.config import settings
from app.mcp_servers.mock_data import get_seed_calendar_events, get_seed_drive_files

class GoogleWorkspaceConnector:
    """
    Adapter supporting Google Workspace (Calendar, Drive) operations.
    Seamlessly runs with mock seed data when MOCK_MODE is enabled or API keys are omitted.
    """
    def __init__(self):
        self._calendar_events = get_seed_calendar_events()
        self._drive_files = get_seed_drive_files()

    async def list_calendar_events(self, start_date: Optional[str] = None) -> List[Dict[str, Any]]:
        return self._calendar_events

    async def create_calendar_event(self, title: str, start_time: str, end_time: str, description: str = "") -> Dict[str, Any]:
        new_event = {
            "id": f"cal-{len(self._calendar_events) + 1:02d}",
            "title": title,
            "start_time": start_time,
            "end_time": end_time,
            "location": "Online",
            "description": description
        }
        self._calendar_events.append(new_event)
        return new_event

    async def search_drive_files(self, query: str) -> List[Dict[str, Any]]:
        query_lower = query.lower()
        return [
            f for f in self._drive_files
            if query_lower in f["name"].lower() or query_lower in f["snippet"].lower()
        ]

    async def organize_drive_file(self, file_id: str, target_folder: str) -> Dict[str, Any]:
        for f in self._drive_files:
            if f["id"] == file_id:
                old_folder = f["folder"]
                f["folder"] = target_folder
                return {
                    "file_id": file_id,
                    "file_name": f["name"],
                    "old_folder": old_folder,
                    "new_folder": target_folder,
                    "status": "moved"
                }
        return {"error": "File not found"}

workspace_connector = GoogleWorkspaceConnector()
