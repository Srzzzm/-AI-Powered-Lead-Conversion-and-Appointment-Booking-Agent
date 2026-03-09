"""Lead capture service — extracts structured lead info from raw messages."""

import json
from sqlalchemy.orm import Session
from models.lead import Lead, LeadStatus
from models.conversation import Conversation, InteractionLog
from services.ai_engine import AIEngine


class LeadCaptureService:
    def __init__(self, db: Session):
        self.db = db
        self.ai = AIEngine()

    async def capture_lead(self, channel: str, raw_message: str, channel_user_id: str = None) -> Lead:
        """
        capture_lead(channel, raw_message) → structured lead object
        Parses incoming message, extracts name/contact/intent using AI.
        """
        # Use AI to extract structured info from the raw message
        extracted = await self.ai.extract_lead_info(raw_message)

        lead = Lead(
            name=extracted.get("name"),
            contact=extracted.get("contact"),
            channel=channel,
            channel_user_id=channel_user_id,
            service_interest=extracted.get("service_interest"),
            urgency=extracted.get("urgency", "medium"),
            status=LeadStatus.CAPTURED,
            raw_message=raw_message,
        )
        self.db.add(lead)
        self.db.commit()
        self.db.refresh(lead)

        # Log interaction
        self._log(lead.id, "captured", f"Lead captured from {channel}")

        # Save the first conversation entry
        conv = Conversation(
            lead_id=lead.id,
            sender="user",
            message=raw_message,
            channel=channel,
        )
        self.db.add(conv)
        self.db.commit()

        return lead

    async def classify_intent(self, message_text: str) -> dict:
        """
        classify_intent(message_text) → {service_category, urgency_score}
        """
        return await self.ai.classify_intent(message_text)

    def _log(self, lead_id: int, stage: str, details: str):
        log = InteractionLog(lead_id=lead_id, stage=stage, outcome="success", details=details)
        self.db.add(log)
        self.db.commit()
