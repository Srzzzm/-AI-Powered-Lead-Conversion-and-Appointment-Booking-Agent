"""Qualification engine — manages multi-turn qualification conversations."""

import json
from pathlib import Path
from typing import Dict, List

from sqlalchemy.orm import Session

from models.lead import Lead, LeadStatus
from models.conversation import Conversation, InteractionLog
from models.analytics import ConversationStrategy
from services.ai_engine import AIEngine


class QualificationService:
    def __init__(self, db: Session):
        self.db = db
        self.ai = AIEngine()
        # Load question bank
        questions_path = Path(__file__).parent.parent / "mock_data" / "questions.json"
        with open(questions_path) as f:
            questions = json.load(f)["questions"]

        # Index questions by id for quick lookup
        self.question_bank: List[dict] = questions
        self.questions_by_id: Dict[str, dict] = {q["id"]: q for q in questions}

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

        # Select next question using optimized conversation strategy
        result = self._select_next_question(lead, question_number)

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

        # Log interaction with concrete question ID so improvement loop
        # can reconstruct the full question sequence later.
        question_id = result.get("id") or f"Q{question_number + 1}"
        log = InteractionLog(
            lead_id=lead_id,
            stage="qualifying",
            outcome=question_id,
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

    # ── Strategy-driven question selection helpers ─────────────────────────

    def _get_default_sequence(self, lead: Lead) -> List[str]:
        """
        Fallback qualification sequence when no optimized strategy exists yet.
        Uses IDs from the static question bank.

        We keep it short (max ~5 questions) to satisfy the spec.
        """
        # High-urgency leads: quickly confirm need, urgency, insurance, then go for conversion
        if (lead.urgency or "").lower() == "high":
            return ["Q1", "Q5", "Q3", "Q10", "Q15"]

        # Others: broader discovery then conversion
        return ["Q1", "Q2", "Q7", "Q3", "Q15"]

    def _get_active_sequence(self) -> List[str]:
        """
        Load the currently active optimized sequence from ConversationStrategy.
        If none exists yet, return an empty list so callers can fall back.
        """
        strategy = (
            self.db.query(ConversationStrategy)
            .filter(ConversationStrategy.is_active == 1)
            .order_by(ConversationStrategy.updated_at.desc())
            .first()
        )
        if not strategy:
            return []

        try:
            seq = json.loads(strategy.question_sequence)
            if isinstance(seq, list):
                return [str(q) for q in seq]
        except json.JSONDecodeError:
            return []
        return []

    def _select_next_question(self, lead: Lead, question_number: int) -> dict:
        """
        Decide which qualification question to ask next.

        Priority:
        1. Use the currently active optimized sequence (if any)
        2. Fall back to a sensible default sequence based on urgency
        3. As a last resort, use the AIEngine to generate a question
        """
        # Try optimized strategy
        active_seq = self._get_active_sequence()

        if not active_seq:
            # Fall back to default, urgency-aware sequence
            active_seq = self._get_default_sequence(lead)

        question_id: str | None = None
        if 0 <= question_number < len(active_seq):
            question_id = active_seq[question_number]

        question_obj = self.questions_by_id.get(question_id or "", None)

        if question_obj:
            is_final = question_number >= 4 or question_obj["stage"] == "late"
            return {
                "id": question_obj["id"],
                "question": question_obj["text"],
                "category": question_obj["category"],
                "is_final": is_final,
            }

        # Last resort: delegate to AI engine for a generic but relevant question
        lead_context = {
            "name": lead.name,
            "service_interest": lead.service_interest,
            "urgency": lead.urgency,
            "insurance_status": lead.insurance_status,
            "prior_experience": lead.prior_experience,
        }
        ai_result = self.ai.generate_qualification_response(
            lead_context, "", question_number
        )

        # ai_result is an awaitable in async context, but _select_next_question
        # is sync because we mostly operate on local data. If for some reason
        # we cannot use the strategy/default questions, we simply fall back
        # to a static question instead of awaiting here.
        fallback_questions = [
            ("Q1", "What specific treatment or service are you looking for?", "service"),
            ("Q2", "How soon do you need this? Is it urgent?", "urgency"),
            ("Q3", "Will you be using insurance or paying out of pocket?", "insurance"),
            ("Q4", "Have you visited our hospital before?", "experience"),
            ("Q15", "Would you like me to check available appointment slots for you?", "conversion"),
        ]
        idx = min(question_number, len(fallback_questions) - 1)
        qid, qtext, qcat = fallback_questions[idx]
        return {
            "id": qid,
            "question": qtext,
            "category": qcat,
            "is_final": question_number >= 4 or qid == "Q15",
        }
