"""Conversation history model for tracking all interactions."""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from database import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    sender = Column(String(10), nullable=False)  # "agent" or "user"
    message = Column(Text, nullable=False)
    channel = Column(String(20), nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class InteractionLog(Base):
    """Logs pipeline events for analytics."""
    __tablename__ = "interaction_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    stage = Column(String(30), nullable=False)  # captured, qualified, scoring, booking, converted, lost
    outcome = Column(String(50), nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
