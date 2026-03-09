"""Cron-style endpoints for background maintenance tasks."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from services.reminder import ReminderService


router = APIRouter(prefix="/api/cron", tags=["cron"])


@router.post("/reminders")
async def run_reminder_tick(db: Session = Depends(get_db)):
    """
    Manually trigger the inactivity reminder scan.

    Can be called by an external cron job or scheduler.
    """
    service = ReminderService(db)
    count = await service.run_reminder_tick()
    return {"status": "ok", "reminders_sent": count}

