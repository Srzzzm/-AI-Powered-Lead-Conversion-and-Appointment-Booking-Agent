"""Analytics model for continuous improvement tracking."""

from sqlalchemy import Column, Integer, String, DateTime, Text, Float, JSON
from sqlalchemy.sql import func
from database import Base


class ConversionMetric(Base):
    """Weekly conversion metrics snapshot."""
    __tablename__ = "conversion_metrics"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    week_start = Column(String(10), nullable=False)
    channel = Column(String(20), nullable=False)
    service_type = Column(String(100), nullable=True)
    leads_captured = Column(Integer, default=0)
    leads_qualified = Column(Integer, default=0)
    leads_converted = Column(Integer, default=0)
    leads_lost = Column(Integer, default=0)
    conversion_rate = Column(Float, default=0.0)
    avg_response_time_sec = Column(Float, default=0.0)
    created_at = Column(DateTime, server_default=func.now())


class ConversationStrategy(Base):
    """Stores optimized conversation strategies from improvement loop."""
    __tablename__ = "conversation_strategies"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    strategy_name = Column(String(100), nullable=False)
    question_sequence = Column(Text, nullable=False)  # JSON array of question IDs
    conversion_rate = Column(Float, default=0.0)
    sample_size = Column(Integer, default=0)
    is_active = Column(Integer, default=1)  # 1=active, 0=retired
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
