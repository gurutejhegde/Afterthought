from datetime import datetime
import uuid
from sqlalchemy import Column, String, Text, DateTime, Boolean, Enum
from app.db.database import Base

class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    source = Column(String(50), default="chat") # chat, calendar, drive, email
    status = Column(String(50), default="pending") # pending, in_progress, stalled, overdue, completed
    deadline = Column(DateTime, nullable=True)
    verification_evidence = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class OutcomeRecord(Base):
    __tablename__ = "outcome_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    category = Column(String(50), default="decision") # decision, intention, commitment
    details = Column(Text, nullable=True)
    status = Column(String(50), default="active") # active, resolved, archived
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PendingAction(Base):
    __tablename__ = "pending_actions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tool_name = Column(String(100), nullable=False)
    parameters = Column(Text, nullable=False) # JSON encoded
    risk_level = Column(String(20), default="MEDIUM") # LOW, MEDIUM, HIGH
    summary = Column(Text, nullable=False)
    status = Column(String(30), default="pending_approval") # pending_approval, approved, rejected, executed
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    action_type = Column(String(100), nullable=False)
    details = Column(Text, nullable=False)
    is_reversible = Column(Boolean, default=False)
    undo_payload = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
