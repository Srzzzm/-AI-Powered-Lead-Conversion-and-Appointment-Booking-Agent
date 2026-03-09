"""Appointment database model."""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from database import Base


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    doctor_name = Column(String(100), nullable=False)
    specialty = Column(String(100), nullable=False)
    slot_date = Column(String(20), nullable=False)
    slot_time = Column(String(20), nullable=False)
    slot_id = Column(String(50), nullable=False)
    status = Column(String(20), default="confirmed")  # confirmed, cancelled, completed
    preparation_instructions = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
