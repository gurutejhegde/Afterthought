from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, String, Text, DateTime, Boolean
from app.db.database import Base


def utc_now() -> datetime:
    """Return timezone-naive UTC datetime without deprecated utcnow()."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    source = Column(String(50), default="chat")  # chat, calendar, drive, email, manual, mcp
    status = Column(String(50), default="pending")  # pending, in_progress, stalled, overdue, completed
    deadline = Column(DateTime, nullable=True)
    verification_evidence = Column(Text, nullable=True)
    assumption_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)


class OutcomeRecord(Base):
    __tablename__ = "outcome_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    category = Column(String(50), default="decision")  # decision, intention, idea, milestone
    details = Column(Text, nullable=True)
    status = Column(String(50), default="active")  # active, resolved, archived
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)


class PendingAction(Base):
    __tablename__ = "pending_actions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tool_name = Column(String(100), nullable=False)
    parameters = Column(Text, nullable=False)  # JSON encoded
    risk_level = Column(String(20), default="MEDIUM")  # LOW, MEDIUM, HIGH
    summary = Column(Text, nullable=False)
    status = Column(String(30), default="pending_approval")  # pending_approval, approved, rejected, executed
    created_at = Column(DateTime, default=utc_now)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    action_type = Column(String(100), nullable=False)
    details = Column(Text, nullable=False)
    is_reversible = Column(Boolean, default=False)
    undo_payload = Column(Text, nullable=True)
    undone = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=utc_now)


class FollowUpNudge(Base):
    __tablename__ = "followup_nudges"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String(36), nullable=False)
    reason = Column(String(50), nullable=False)  # overdue, stalled, weak_assumption
    message = Column(Text, nullable=False)
    status = Column(String(30), default="pending")  # pending, resolved, dismissed
    created_at = Column(DateTime, default=utc_now)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    role = Column(String(20), nullable=False)  # user, assistant
    content = Column(Text, nullable=False)
    sources_checked = Column(Text, nullable=True)  # JSON encoded list
    action_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=utc_now)
