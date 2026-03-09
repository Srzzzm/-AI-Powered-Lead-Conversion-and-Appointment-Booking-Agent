"""Lead scoring service — classifies leads as Hot / Warm / Cold."""

from sqlalchemy.orm import Session
from models.lead import Lead, LeadScore, LeadStatus
from models.conversation import InteractionLog


class ScoringService:
    def __init__(self, db: Session):
        self.db = db

    def score_lead(self, lead_id: int) -> dict:
        """
        score_lead(lead_id, qualification_answers) → Hot / Warm / Cold with reasoning
        """
        lead = self.db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            return {"error": "Lead not found"}

        score_points = 0
        reasoning = []

        # 1. Service Interest Clarity (0-3 points)
        if lead.service_interest and lead.service_interest != "General Inquiry":
            score_points += 3
            reasoning.append(f"Clear service need: {lead.service_interest}")
        elif lead.service_interest == "General Inquiry":
            score_points += 0
            reasoning.append("No specific service identified — general browsing")

        # 2. Urgency (0-3 points)
        if lead.urgency == "high":
            score_points += 3
            reasoning.append("High urgency — needs immediate attention")
        elif lead.urgency == "medium":
            score_points += 2
            reasoning.append("Moderate urgency — interested but not immediate")
        else:
            score_points += 0
            reasoning.append("Low urgency — just exploring")

        # 3. Insurance clarity (0-2 points)
        if lead.insurance_status in ("insured", "self-pay"):
            score_points += 2
            reasoning.append(f"Payment clear: {lead.insurance_status}")
        else:
            score_points += 1
            reasoning.append("Payment status unknown")

        # 4. Engagement (0-2 points) — check how many qualification questions answered
        if lead.qualification_step >= 4:
            score_points += 2
            reasoning.append("Highly engaged — answered 4+ questions")
        elif lead.qualification_step >= 2:
            score_points += 1
            reasoning.append("Moderately engaged")
        else:
            reasoning.append("Low engagement — minimal responses")

        # Determine score
        if score_points >= 8:
            final_score = LeadScore.HOT
            reasoning.insert(0, "🔥 HOT LEAD — Ready to convert!")
        elif score_points >= 5:
            final_score = LeadScore.WARM
            reasoning.insert(0, "🌤️ WARM LEAD — Needs nurturing")
        else:
            final_score = LeadScore.COLD
            reasoning.insert(0, "❄️ COLD LEAD — Add to awareness pipeline")

        # Update lead
        lead.score = final_score
        lead.score_reasoning = " | ".join(reasoning)
        lead.status = LeadStatus.QUALIFIED
        self.db.commit()

        # Log
        log = InteractionLog(
            lead_id=lead_id,
            stage="scoring",
            outcome=final_score.value,
            details=" | ".join(reasoning),
        )
        self.db.add(log)
        self.db.commit()

        return {
            "lead_id": lead_id,
            "score": final_score.value,
            "points": score_points,
            "max_points": 10,
            "reasoning": reasoning,
        }
