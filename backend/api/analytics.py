"""Analytics API endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from services.improvement import ImprovementService

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/conversion")
async def get_conversion_analytics(db: Session = Depends(get_db)):
    """Get pipeline performance metrics."""
    service = ImprovementService(db)
    return service.get_conversion_analytics()


@router.get("/improvement")
async def get_improvement_insights(db: Session = Depends(get_db)):
    """Get continuous improvement insights and recommendations."""
    service = ImprovementService(db)
    return service.analyze_improvement_opportunities()
