"""Appointment API endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from services.appointment import AppointmentService

router = APIRouter(prefix="/api/appointments", tags=["appointments"])


@router.get("/")
async def get_all_appointments(db: Session = Depends(get_db)):
    """Get all booked appointments."""
    service = AppointmentService(db)
    return service.get_all_appointments()


@router.get("/availability/{specialty}")
async def check_availability(specialty: str, db: Session = Depends(get_db)):
    """Check doctor availability by specialty."""
    service = AppointmentService(db)
    return service.check_doctor_availability(specialty)
