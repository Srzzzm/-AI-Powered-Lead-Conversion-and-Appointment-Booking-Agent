"""Lead database model."""

from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Enum as SQLEnum
from sqlalchemy.sql import func
from database import Base
import enum


class LeadStatus(str, enum.Enum):
    CAPTURED = "captured"
    QUALIFYING = "qualifying"
    QUALIFIED = "qualified"
    CONVERTED = "converted"
    NURTURING = "nurturing"
    LOST = "lost"


class LeadScore(str, enum.Enum):
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"
    UNSCORED = "unscored"


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=True)
    contact = Column(String(50), nullable=True)
    email = Column(String(100), nullable=True)
    channel = Column(String(20), nullable=False)  # whatsapp, instagram, webchat
    channel_user_id = Column(String(100), nullable=True)  # platform-specific ID
    service_interest = Column(String(200), nullable=True)
    urgency = Column(String(20), nullable=True)  # high, medium, low
    score = Column(SQLEnum(LeadScore), default=LeadScore.UNSCORED)
    score_reasoning = Column(Text, nullable=True)
    status = Column(SQLEnum(LeadStatus), default=LeadStatus.CAPTURED)
    insurance_status = Column(String(50), nullable=True)  # insured, self-pay, unknown
    prior_experience = Column(Text, nullable=True)
    timeline = Column(String(50), nullable=True)
    qualification_step = Column(Integer, default=0)
    raw_message = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
