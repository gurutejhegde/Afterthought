from datetime import datetime


def get_seed_calendar_events():
    today = datetime.now()
    return [
        {
            "id": "cal-01",
            "title": "Hackathon Mentor Check-in & Architecture Review",
            "start_time": today.replace(hour=11, minute=0, second=0, microsecond=0).isoformat(),
            "end_time": today.replace(hour=11, minute=30, second=0, microsecond=0).isoformat(),
            "location": "Google Meet",
            "description": "Discuss Track 01 deliverables, outcome ledger demo and MCP tooling."
        },
        {
            "id": "cal-02",
            "title": "Team Sync: Frontend Voice & Daily Briefing integration",
            "start_time": today.replace(hour=15, minute=0, second=0, microsecond=0).isoformat(),
            "end_time": today.replace(hour=15, minute=45, second=0, microsecond=0).isoformat(),
            "location": "Discord / Voice Channel",
            "description": "Align with teammates on UI flow and ElevenLabs integration."
        },
        {
            "id": "cal-03",
            "title": "Project Submission Deadline (wHACKiest 2026)",
            "start_time": today.replace(hour=18, minute=0, second=0, microsecond=0).isoformat(),
            "end_time": today.replace(hour=18, minute=0, second=0, microsecond=0).isoformat(),
            "location": "Hackathon Portal",
            "description": "Submit GitHub repo URL, live demo link, and demo recording."
        }
    ]


def get_seed_drive_files():
    return [
        {
            "id": "drive-01",
            "name": "Nebula_Track1_Pitch.pptx",
            "mimeType": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "folder": "/Documents/Presentations",
            "last_modified": "Today 08:30 AM",
            "snippet": "Slide 5: Process Flow and MCP Architecture. Needs final verification."
        },
        {
            "id": "drive-02",
            "name": "wHACKiest_Track1_Rubric.pdf",
            "mimeType": "application/pdf",
            "folder": "/Hackathon/Guidelines",
            "last_modified": "Yesterday",
            "snippet": "Evaluation criteria: Real-world feasibility, MCP extensibility, and user control."
        },
        {
            "id": "drive-03",
            "name": "Team_Nebula_Notes.gdoc",
            "mimeType": "application/vnd.google-apps.document",
            "folder": "/Documents/Notes",
            "last_modified": "2 hours ago",
            "snippet": "Follow-up items: Add approval guardrail for file organization and action auditing."
        }
    ]


def get_seed_emails():
    return [
        {
            "id": "mail-01",
            "sender": "mentor@whackiest.org",
            "subject": "Track 01 Check-in & Guardrails Verification",
            "received_at": "Today 07:45 AM",
            "unread": True,
            "snippet": "Please confirm how your assistant prevents prompt injection inside Drive docs and emails before 11 AM."
        },
        {
            "id": "mail-02",
            "sender": "submissions@whackiest.org",
            "subject": "Reminder: Ideathon Submission Window Closes Today",
            "received_at": "Today 06:30 AM",
            "unread": True,
            "snippet": "Final pitch deck and working prototype links must be submitted by 6:00 PM IST."
        },
        {
            "id": "mail-03",
            "sender": "teammate@aitm.edu",
            "subject": "Updated ElevenLabs voice test clip",
            "received_at": "Yesterday 10:15 PM",
            "unread": False,
            "snippet": "Uploaded the sample briefing audio notes to /Documents/Notes for review."
        }
    ]
