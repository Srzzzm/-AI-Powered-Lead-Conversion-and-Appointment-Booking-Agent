"""Unified message router — routes messages from all channels to the lead pipeline."""

from sqlalchemy.orm import Session
from models.lead import Lead, LeadStatus, LeadScore
from models.conversation import Conversation
from services.lead_capture import LeadCaptureService
from services.qualification import QualificationService
from services.scoring import ScoringService
from services.appointment import AppointmentService
from services.nurture import NurtureService
from services.ai_engine import AIEngine


class MessageRouter:
    """Routes incoming messages through the lead conversion pipeline."""

    def __init__(self, db: Session):
        self.db = db
        self.ai = AIEngine()
        self.capture = LeadCaptureService(db)
        self.qualification = QualificationService(db)
        self.scoring = ScoringService(db)
        self.appointment = AppointmentService(db)
        self.nurture = NurtureService(db)

    async def handle_message(
        self, channel: str, channel_user_id: str, message_text: str
    ) -> dict:
        """
        Main entry point: receives a message and routes through the pipeline.
        1. Check if lead exists → if not, capture
        2. If captured, send personalized greeting + start qualification
        3. If qualifying, continue qualification conversation
        4. If qualified, take action based on score
        """
        # Check for existing lead
        lead = (
            self.db.query(Lead)
            .filter(Lead.channel_user_id == channel_user_id, Lead.channel == channel)
            .order_by(Lead.created_at.desc())
            .first()
        )

        if not lead:
            # ── Step 1: New lead — capture and greet ──
            lead = await self.capture.capture_lead(channel, message_text, channel_user_id)

            # Generate personalized greeting
            greeting = await self.ai.generate_personalized_greeting(
                lead.name, lead.service_interest, channel
            )

            # Save agent greeting
            conv = Conversation(
                lead_id=lead.id, sender="agent", message=greeting, channel=channel
            )
            self.db.add(conv)
            self.db.commit()

            # Start qualification — ask first question
            q_result = await self.qualification.ask_qualification_question(
                lead.id, 0, ""
            )

            full_response = f"{greeting}\n\n{q_result['question']}"
            return {
                "lead_id": lead.id,
                "status": "captured",
                "agent_response": full_response,
            }

        elif lead.status in (LeadStatus.CAPTURED, LeadStatus.QUALIFYING):
            # ── Step 2-3: Continuing qualification ──
            # Save user message
            conv = Conversation(
                lead_id=lead.id, sender="user", message=message_text, channel=channel
            )
            self.db.add(conv)
            self.db.commit()

            step = lead.qualification_step or 0

            if step < 5:
                # Continue asking questions
                q_result = await self.qualification.ask_qualification_question(
                    lead.id, step, message_text
                )

                if q_result.get("is_final", False) or step >= 4:
                    # ── Step 4: Score the lead ──
                    score_result = self.scoring.score_lead(lead.id)
                    self.db.refresh(lead)

                    return await self._handle_scored_lead(lead, score_result)

                return {
                    "lead_id": lead.id,
                    "status": "qualifying",
                    "agent_response": q_result["question"],
                }
            else:
                # Score if not yet scored
                score_result = self.scoring.score_lead(lead.id)
                self.db.refresh(lead)
                return await self._handle_scored_lead(lead, score_result)

        elif lead.status == LeadStatus.QUALIFIED:
            # Already scored — handle based on score
            return await self._continue_post_qualification(lead, message_text)

        else:
            # Nurturing or converted — generic response
            return {
                "lead_id": lead.id,
                "status": lead.status.value,
                "agent_response": (
                    "Thank you for your message! A member of our team will be in touch shortly. "
                    "Is there anything else I can help you with?"
                ),
            }

    async def _handle_scored_lead(self, lead: Lead, score_result: dict) -> dict:
        """Take action based on lead score."""
        if lead.score == LeadScore.HOT:
            # 🔥 Hot: Book appointment immediately
            specialty = self._extract_specialty(lead.service_interest)
            slots = self.appointment.check_doctor_availability(specialty)

            if slots:
                slot = slots[0]
                booking = self.appointment.book_appointment(lead.id, slot["slot_id"])

                response = (
                    f"Great news! Based on our conversation, I can see you need prompt attention. "
                    f"I've found the perfect appointment for you:\n\n"
                    f"{booking['confirmation_message']}"
                )
            else:
                response = (
                    f"I can see this is urgent for you. Unfortunately, we don't have immediate openings "
                    f"in that department. Let me have our team call you within the hour to arrange something. "
                    f"Your inquiry is marked as high priority!"
                )

            return {"lead_id": lead.id, "status": "converted", "agent_response": response}

        elif lead.score == LeadScore.WARM:
            # 🌤️ Warm: Nurture sequence
            nurture_result = self.nurture.add_to_nurture_sequence(lead.id, "warm")
            response = (
                f"Thank you for sharing all that information! "
                f"I'm preparing a detailed information pack about {lead.service_interest} for you. "
                f"Our team will also schedule a follow-up call to answer any questions. "
                f"In the meantime, feel free to reach out anytime!"
            )
            return {"lead_id": lead.id, "status": "nurturing", "agent_response": response}

        else:
            # ❄️ Cold: Add to awareness sequence
            nurture_result = self.nurture.add_to_nurture_sequence(lead.id, "cold")
            response = (
                f"Thank you for your interest! I've noted your inquiry. "
                f"I'll send you some helpful health information and updates about our services. "
                f"Whenever you're ready to book, just message us — we're here 24/7! 😊"
            )
            return {"lead_id": lead.id, "status": "nurturing", "agent_response": response}

    async def _continue_post_qualification(self, lead: Lead, message: str) -> dict:
        """Handle messages from already-scored leads."""
        msg_lower = message.lower()
        if any(w in msg_lower for w in ["book", "appointment", "schedule", "yes", "slot"]):
            specialty = self._extract_specialty(lead.service_interest)
            slots = self.appointment.check_doctor_availability(specialty)
            if slots:
                slot = slots[0]
                booking = self.appointment.book_appointment(lead.id, slot["slot_id"])
                return {
                    "lead_id": lead.id,
                    "status": "converted",
                    "agent_response": booking["confirmation_message"],
                }
        return {
            "lead_id": lead.id,
            "status": lead.status.value,
            "agent_response": "Thank you! Our team will follow up with you shortly. Is there anything else I can help with?",
        }

    def _extract_specialty(self, service_interest: str) -> str:
        """Extract specialty name from service interest string."""
        if not service_interest:
            return "General"
        mapping = {
            "orthop": "Orthopedics",
            "cardio": "Cardiology",
            "heart": "Cardiology",
            "pediatr": "Pediatrics",
            "child": "Pediatrics",
            "diagnos": "Diagnostics",
            "mri": "Diagnostics",
            "dental": "Dentistry",
            "eye": "Ophthalmology",
            "ophthal": "Ophthalmology",
            "matern": "Obstetrics",
            "obstet": "Obstetrics",
            "checkup": "Health Checkup",
        }
        lower = service_interest.lower()
        for keyword, spec in mapping.items():
            if keyword in lower:
                return spec
        return "General"
