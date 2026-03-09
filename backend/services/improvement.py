"""Continuous improvement loop — analyzes conversion patterns and updates strategy."""

import json
from pathlib import Path
from collections import Counter
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.lead import Lead, LeadScore
from models.conversation import InteractionLog
from models.analytics import ConversionMetric, ConversationStrategy


class ImprovementService:
    def __init__(self, db: Session):
        self.db = db
        # Load historical data
        hist_path = Path(__file__).parent.parent / "mock_data" / "historical.json"
        with open(hist_path) as f:
            self.historical_data = json.load(f)

    def get_conversion_analytics(self, date_range: str = None) -> dict:
        """
        get_conversion_analytics(date_range) → pipeline performance metrics
        """
        leads = self.db.query(Lead).all()

        total = len(leads)
        by_status = Counter(l.status.value if l.status else "unknown" for l in leads)
        by_score = Counter(l.score.value if l.score else "unscored" for l in leads)
        by_channel = {}
        by_service = {}

        for lead in leads:
            ch = lead.channel or "unknown"
            sv = lead.service_interest or "General"

            if ch not in by_channel:
                by_channel[ch] = {"captured": 0, "converted": 0, "qualified": 0, "lost": 0}
            by_channel[ch]["captured"] += 1
            if lead.status and lead.status.value == "converted":
                by_channel[ch]["converted"] += 1
            if lead.status and lead.status.value == "qualified":
                by_channel[ch]["qualified"] += 1
            if lead.status and lead.status.value == "lost":
                by_channel[ch]["lost"] += 1

            if sv not in by_service:
                by_service[sv] = {"captured": 0, "converted": 0}
            by_service[sv]["captured"] += 1
            if lead.status and lead.status.value == "converted":
                by_service[sv]["converted"] += 1

        # Calculate conversion rates
        for ch in by_channel:
            cap = by_channel[ch]["captured"]
            conv = by_channel[ch]["converted"]
            by_channel[ch]["conversion_rate"] = round((conv / cap * 100) if cap > 0 else 0, 1)

        for sv in by_service:
            cap = by_service[sv]["captured"]
            conv = by_service[sv]["converted"]
            by_service[sv]["conversion_rate"] = round((conv / cap * 100) if cap > 0 else 0, 1)

        overall_conversion = round((by_status.get("converted", 0) / total * 100) if total > 0 else 0, 1)

        # Include historical baseline
        hist_converted = sum(1 for h in self.historical_data if h["outcome"] == "converted")
        hist_total = len(self.historical_data)
        hist_rate = round((hist_converted / hist_total * 100) if hist_total > 0 else 0, 1)

        return {
            "total_leads": total,
            "by_status": dict(by_status),
            "by_score": dict(by_score),
            "by_channel": by_channel,
            "by_service": by_service,
            "overall_conversion_rate": overall_conversion,
            "historical_baseline": {
                "total_interactions": hist_total,
                "converted": hist_converted,
                "conversion_rate": hist_rate,
            },
        }

    def analyze_improvement_opportunities(self) -> dict:
        """
        Bonus: Analyze conversation paths and identify top-performing question sequences.
        """
        # Analyze historical data for question sequence patterns
        converted_sequences = []
        lost_sequences = []

        for interaction in self.historical_data:
            seq = tuple(interaction["questions_asked"])
            if interaction["outcome"] == "converted":
                converted_sequences.append(seq)
            elif interaction["outcome"] == "lost":
                lost_sequences.append(seq)

        # Find top converting sequences
        seq_counter = Counter(converted_sequences)
        top_sequences = seq_counter.most_common(2)

        # Avg response time for converted vs lost
        conv_times = [h["response_time_sec"] for h in self.historical_data if h["outcome"] == "converted"]
        lost_times = [h["response_time_sec"] for h in self.historical_data if h["outcome"] == "lost"]
        avg_conv_time = round(sum(conv_times) / len(conv_times), 1) if conv_times else 0
        avg_lost_time = round(sum(lost_times) / len(lost_times), 1) if lost_times else 0

        insights = {
            "top_converting_sequences": [
                {"questions": list(seq), "conversions": count}
                for seq, count in top_sequences
            ],
            "response_time_insight": {
                "avg_response_time_converted_sec": avg_conv_time,
                "avg_response_time_lost_sec": avg_lost_time,
                "recommendation": (
                    f"Converted leads had avg response time of {avg_conv_time}s vs "
                    f"{avg_lost_time}s for lost leads. Speed matters!"
                ),
            },
            "channel_insight": Counter(h["channel"] for h in self.historical_data if h["outcome"] == "converted"),
            "recommendations": [
                "Prioritize response time under 30 seconds for maximum conversion",
                "Use question sequences Q1→Q2→Q3→Q15 for high-urgency leads",
                "WhatsApp leads convert at a higher rate — focus marketing spend there",
            ],
        }

        return insights
