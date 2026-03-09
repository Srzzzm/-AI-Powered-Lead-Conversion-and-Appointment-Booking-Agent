"""Nurture sequence service — enrolls Warm/Cold leads in follow-up flows."""

from sqlalchemy.orm import Session
from models.lead import Lead, LeadStatus
from models.conversation import Conversation, InteractionLog


NURTURE_SEQUENCES = {
    "warm": {
        "name": "Warm Lead Nurture",
        "messages": [
            "Hi {name}! Just following up on your inquiry about {service}. We've prepared an information pack for you. Would you like us to email it or share it here?",
            "Good news, {name}! We currently have special offers on {service}. Would you like to learn more?",
            "Hi {name}, just checking in! Our {service} department has new availability this week. Shall I book a consultation?",
        ],
        "interval_days": 2,
    },
    "cold": {
        "name": "Cold Lead Awareness",
        "messages": [
            "Hi {name}! Did you know HealthFirst Hospital is ranked #1 in patient satisfaction? Learn about our services: healthfirst.com/services",
            "🏥 Health Tip from HealthFirst: Regular health checkups can prevent 80% of chronic conditions. Book your annual checkup today!",
            "Hi {name}, we've launched new health packages perfect for families. Check them out at healthfirst.com/packages",
        ],
        "interval_days": 5,
    },
}


class NurtureService:
    def __init__(self, db: Session):
        self.db = db

    def add_to_nurture_sequence(self, lead_id: int, sequence_type: str) -> dict:
        """
        add_to_nurture_sequence(lead_id, sequence_type) → enrolls lead in follow-up flow
        """
        lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            return {"error": "Lead not found"}

        sequence = NURTURE_SEQUENCES.get(sequence_type)
        if not sequence:
            return {"error": f"Unknown sequence type: {sequence_type}"}

        # Update lead status
        lead.status = LeadStatus.NURTURING
        self.db.commit()

        # Send first nurture message
        first_msg = sequence["messages"][0].format(
            name=lead.name or "there",
            service=lead.service_interest or "healthcare services",
        )

        conv = Conversation(
            lead_id=lead_id,
            sender="agent",
            message=first_msg,
            channel=lead.channel,
        )
        self.db.add(conv)

        # Log
        log = InteractionLog(
            lead_id=lead_id,
            stage="nurturing",
            outcome=f"enrolled_{sequence_type}",
            details=f"Enrolled in {sequence['name']} sequence",
        )
        self.db.add(log)
        self.db.commit()

        return {
            "lead_id": lead_id,
            "sequence_type": sequence_type,
            "sequence_name": sequence["name"],
            "first_message": first_msg,
            "total_messages": len(sequence["messages"]),
            "interval_days": sequence["interval_days"],
            "status": "enrolled",
        }
