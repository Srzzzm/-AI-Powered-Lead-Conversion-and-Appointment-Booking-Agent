"""Qualification engine — manages multi-turn qualification conversations."""

import json
from pathlib import Path
from sqlalchemy.orm import Session
from models.lead import Lead, LeadStatus
from models.conversation import Conversation, InteractionLog
from services.ai_engine import AIEngine


class QualificationService:
    def __init__(self, db: Session):
        self.db = db
        self.ai = AIEngine()
        # Load question bank
        questions_path = Path(__file__).parent.parent / "mock_data" / "questions.json"
        with open(questions_path) as f:
            self.question_bank = json.load(f)["questions"]

    async def ask_qualification_question(
        self, lead_id: int, question_number: int, user_answer: str = ""
    ) -> dict:
        """
        ask_qualification_question(lead_id, question_number, context) → next adaptive question
        """
        lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            return {"error": "Lead not found"}

        # Update lead status to qualifying
        if lead.status == LeadStatus.CAPTURED:
            lead.status = LeadStatus.QUALIFYING
            self.db.commit()

        # Save the user's answer if provided
        if user_answer:
            conv = Conversation(
                lead_id=lead_id,
                sender="user",
                message=user_answer,
                channel=lead.channel,
            )
            self.db.add(conv)
            self.db.commit()

            # Update lead fields based on answers
            self._update_lead_from_answer(lead, user_answer, question_number)

        # Generate next question using AI
        lead_context = {
            "name": lead.name,
            "service_interest": lead.service_interest,
            "urgency": lead.urgency,
            "insurance_status": lead.insurance_status,
            "prior_experience": lead.prior_experience,
        }

        result = await self.ai.generate_qualification_response(
            lead_context, user_answer, question_number
        )

        # Save agent's question
        agent_msg = Conversation(
            lead_id=lead_id,
            sender="agent",
            message=result["question"],
            channel=lead.channel,
        )
        self.db.add(agent_msg)

        # Update qualification step
        lead.qualification_step = question_number + 1
        self.db.commit()

        # Log interaction
        log = InteractionLog(
            lead_id=lead_id,
            stage="qualifying",
            outcome=f"question_{question_number + 1}",
            details=result["question"],
        )
        self.db.add(log)
        self.db.commit()

        return result

    def _update_lead_from_answer(self, lead: Lead, answer: str, q_number: int):
        """Parse user answers to update lead fields."""
        answer_lower = answer.lower()

        # Try to determine what the answer is about
        if any(w in answer_lower for w in ["insurance", "insured", "star health", "cghs", "esi", "mediclaim"]):
            lead.insurance_status = "insured"
        elif any(w in answer_lower for w in ["self-pay", "pay myself", "cash", "no insurance", "out of pocket"]):
            lead.insurance_status = "self-pay"

        if any(w in answer_lower for w in ["urgent", "immediately", "asap", "today", "tomorrow"]):
            lead.urgency = "high"
        elif any(w in answer_lower for w in ["next week", "this month", "soon"]):
            lead.urgency = "medium"
        elif any(w in answer_lower for w in ["no rush", "sometime", "later", "just checking"]):
            lead.urgency = "low"

        if any(w in answer_lower for w in ["visited before", "been here", "returning", "last time"]):
            lead.prior_experience = "returning_patient"
        elif any(w in answer_lower for w in ["first time", "never", "new patient"]):
            lead.prior_experience = "new_patient"

        self.db.commit()
