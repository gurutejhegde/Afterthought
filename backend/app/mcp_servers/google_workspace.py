from typing import List, Dict, Any, Optional
from app.mcp_servers.mock_data import (
    get_seed_calendar_events,
    get_seed_drive_files,
    get_seed_emails,
)


class GoogleWorkspaceConnector:
    """
    Adapter supporting Google Workspace (Calendar, Drive, Gmail) operations.
    Runs with pre-seeded demo data when MOCK_MODE is active or OAuth credentials are absent.
    """

    def __init__(self):
        self._calendar_events = get_seed_calendar_events()
        self._drive_files = get_seed_drive_files()
        self._emails = get_seed_emails()

    async def list_calendar_events(self, start_date: Optional[str] = None) -> List[Dict[str, Any]]:
        return self._calendar_events

    async def create_calendar_event(
        self, title: str, start_time: str, end_time: str, description: str = ""
    ) -> Dict[str, Any]:
        new_event = {
            "id": f"cal-{len(self._calendar_events) + 1:02d}",
            "title": title,
            "start_time": start_time,
            "end_time": end_time,
            "location": "Online",
            "description": description,
        }
        self._calendar_events.append(new_event)
        return new_event

    async def delete_calendar_event(self, event_id: str) -> Dict[str, Any]:
        for idx, ev in enumerate(self._calendar_events):
            if ev["id"] == event_id:
                removed = self._calendar_events.pop(idx)
                return {"status": "deleted", "event": removed}
        return {"error": "Event not found"}

    async def search_drive_files(self, query: str) -> List[Dict[str, Any]]:
        query_lower = query.lower().strip()
        if not query_lower:
            return self._drive_files
        return [
            f
            for f in self._drive_files
            if query_lower in f["name"].lower()
            or query_lower in f["snippet"].lower()
            or query_lower in f["folder"].lower()
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
                    "status": "moved",
                }
        return {"error": "File not found"}

    async def list_emails(self, unread_only: bool = False) -> List[Dict[str, Any]]:
        if unread_only:
            return [e for e in self._emails if e.get("unread")]
        return self._emails

    async def get_workspace_snapshot(self) -> Dict[str, Any]:
        return {
            "calendar_events": self._calendar_events,
            "drive_files": self._drive_files,
            "emails": self._emails,
        }


workspace_connector = GoogleWorkspaceConnector()
