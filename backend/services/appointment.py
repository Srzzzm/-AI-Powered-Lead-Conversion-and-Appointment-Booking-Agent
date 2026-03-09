"""Appointment booking service — check availability and book slots."""

import json
from pathlib import Path
from sqlalchemy.orm import Session
from models.lead import Lead, LeadStatus
from models.appointment import Appointment
from models.conversation import InteractionLog


class AppointmentService:
    def __init__(self, db: Session):
        self.db = db
        doctors_path = Path(__file__).parent.parent / "mock_data" / "doctors.json"
        with open(doctors_path) as f:
            self.doctors_data = json.load(f)

    def check_doctor_availability(self, specialty: str, date_range: list[str] = None) -> list[dict]:
        """
        check_doctor_availability(specialty, date_range) → available slots
        """
        results = []
        for spec in self.doctors_data["specialties"]:
            if specialty.lower() in spec["name"].lower():
                for doctor in spec["doctors"]:
                    for slot in doctor["slots"]:
                        if slot["available"]:
                            if date_range:
                                if slot["date"] in date_range:
                                    results.append({
                                        "slot_id": slot["id"],
                                        "doctor_name": doctor["name"],
                                        "specialty": spec["name"],
                                        "date": slot["date"],
                                        "time": slot["time"],
                                        "preparation": spec.get("preparation", ""),
                                    })
                            else:
                                results.append({
                                    "slot_id": slot["id"],
                                    "doctor_name": doctor["name"],
                                    "specialty": spec["name"],
                                    "date": slot["date"],
                                    "time": slot["time"],
                                    "preparation": spec.get("preparation", ""),
                                })
        return results

    def book_appointment(self, lead_id: int, slot_id: str) -> dict:
        """
        book_appointment(lead_id, slot_id) → confirms booking + sends confirmation
        """
        lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            return {"error": "Lead not found"}

        # Find the slot
        slot_info = None
        for spec in self.doctors_data["specialties"]:
            for doctor in spec["doctors"]:
                for slot in doctor["slots"]:
                    if slot["id"] == slot_id:
                        slot_info = {
                            "doctor_name": doctor["name"],
                            "specialty": spec["name"],
                            "date": slot["date"],
                            "time": slot["time"],
                            "preparation": spec.get("preparation", ""),
                        }
                        # Mark as unavailable
                        slot["available"] = False
                        break

        if not slot_info:
            return {"error": "Slot not found or already booked"}

        # Create appointment
        appointment = Appointment(
            lead_id=lead_id,
            doctor_name=slot_info["doctor_name"],
            specialty=slot_info["specialty"],
            slot_date=slot_info["date"],
            slot_time=slot_info["time"],
            slot_id=slot_id,
            status="confirmed",
            preparation_instructions=slot_info["preparation"],
        )
        self.db.add(appointment)

        # Update lead status
        lead.status = LeadStatus.CONVERTED
        self.db.commit()
        self.db.refresh(appointment)

        # Log
        log = InteractionLog(
            lead_id=lead_id,
            stage="booking",
            outcome="confirmed",
            details=f"Booked with {slot_info['doctor_name']} on {slot_info['date']} at {slot_info['time']}",
        )
        self.db.add(log)
        self.db.commit()

        confirmation = {
            "appointment_id": appointment.id,
            "status": "confirmed",
            "doctor": slot_info["doctor_name"],
            "specialty": slot_info["specialty"],
            "date": slot_info["date"],
            "time": slot_info["time"],
            "preparation_instructions": slot_info["preparation"],
            "confirmation_message": (
                f"✅ Your appointment is confirmed!\n\n"
                f"👨‍⚕️ Doctor: {slot_info['doctor_name']}\n"
                f"🏥 Department: {slot_info['specialty']}\n"
                f"📅 Date: {slot_info['date']}\n"
                f"⏰ Time: {slot_info['time']}\n\n"
                f"📋 Preparation:\n{slot_info['preparation']}\n\n"
                f"We look forward to seeing you!"
            ),
        }
        return confirmation

    def get_all_appointments(self) -> list[dict]:
        """Get all appointments."""
        appointments = self.db.query(Appointment).all()
        return [
            {
                "id": a.id,
                "lead_id": a.lead_id,
                "doctor_name": a.doctor_name,
                "specialty": a.specialty,
                "date": a.slot_date,
                "time": a.slot_time,
                "status": a.status,
            }
            for a in appointments
        ]
