"""Continuous improvement loop — analyzes conversion patterns and updates strategy."""

import json
from pathlib import Path
from collections import Counter
from typing import List, Dict, Any

from sqlalchemy.orm import Session

from models.lead import Lead, LeadScore, LeadStatus
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
        # Merge historical baseline with live interaction data from the DB
        all_interactions = self._collect_all_interactions()

        # Analyze for sequence patterns
        converted_sequences: List[tuple] = []
        lost_sequences: List[tuple] = []

        for interaction in all_interactions:
            seq = tuple(interaction["questions_asked"])
            if interaction["outcome"] == "converted":
                converted_sequences.append(seq)
            elif interaction["outcome"] == "lost":
                lost_sequences.append(seq)

        # Find top converting sequences (by raw count among converted leads)
        seq_counter = Counter(converted_sequences)
        top_sequences = seq_counter.most_common(2)

        # Simple response-time aggregates
        conv_times = [
            h["response_time_sec"]
            for h in all_interactions
            if h["outcome"] == "converted"
        ]
        lost_times = [
            h["response_time_sec"]
            for h in all_interactions
            if h["outcome"] == "lost"
        ]
        avg_conv_time = round(sum(conv_times) / len(conv_times), 1) if conv_times else 0
        avg_lost_time = round(sum(lost_times) / len(lost_times), 1) if lost_times else 0

        # If we have accumulated enough real interactions (20+), update the active
        # conversation strategy so that future leads use the best-performing sequence.
        strategies_updated = False
        active_strategies: List[Dict[str, Any]] = []
        if len(all_interactions) >= 20 and top_sequences:
            strategies_updated = True

            # Deactivate previous strategies
            self.db.query(ConversationStrategy).update(
                {ConversationStrategy.is_active: 0}
            )
            self.db.commit()

            # Persist top 2 sequences, mark the best one as active
            for idx, (seq, count) in enumerate(top_sequences):
                sequence_list = list(seq)
                strategy = ConversationStrategy(
                    strategy_name=f"auto_seq_{idx + 1}",
                    question_sequence=json.dumps(sequence_list),
                    conversion_rate=0.0,  # could be enriched later
                    sample_size=count,
                    is_active=1 if idx == 0 else 0,
                )
                self.db.add(strategy)
                self.db.commit()
                active_strategies.append(
                    {
                        "id": strategy.id,
                        "strategy_name": strategy.strategy_name,
                        "question_sequence": sequence_list,
                        "is_active": bool(strategy.is_active),
                        "sample_size": strategy.sample_size,
                    }
                )
        else:
            # Even if we don't update, expose any currently active strategies
            strategies = (
                self.db.query(ConversationStrategy)
                .order_by(ConversationStrategy.created_at.desc())
                .all()
            )
            for s in strategies:
                try:
                    sequence_list = json.loads(s.question_sequence)
                except json.JSONDecodeError:
                    sequence_list = []
                active_strategies.append(
                    {
                        "id": s.id,
                        "strategy_name": s.strategy_name,
                        "question_sequence": sequence_list,
                        "is_active": bool(s.is_active),
                        "sample_size": s.sample_size,
                    }
                )

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
            "strategies_updated": strategies_updated,
            "active_strategies": active_strategies,
        }

        return insights

    # ── Helpers for adaptive learning loop ──────────────────────────────────

    def _collect_all_interactions(self) -> List[Dict[str, Any]]:
        """
        Build a merged list of historical + live interaction summaries.

        Each entry roughly matches the structure used in historical.json:
        {
          "questions_asked": ["Q1", "Q2", ...],
          "outcome": "converted" | "lost" | ...,
          "channel": "whatsapp" | "instagram" | "webchat",
          "response_time_sec": float
        }
        """
        interactions: List[Dict[str, Any]] = list(self.historical_data)

        # Live data from DB: reconstruct per-lead question sequences from InteractionLog
        leads = self.db.query(Lead).all()
        for lead in leads:
            logs = (
                self.db.query(InteractionLog)
                .filter(
                    InteractionLog.lead_id == lead.id,
                    InteractionLog.stage == "qualifying",
                )
                .order_by(InteractionLog.created_at.asc())
                .all()
            )
            if not logs:
                continue

            questions_asked = [log.outcome for log in logs if log.outcome]

            # Map lead status to a simple outcome tag
            if lead.status == LeadStatus.CONVERTED:
                outcome = "converted"
            elif lead.status == LeadStatus.LOST:
                outcome = "lost"
            else:
                # For nurturing/qualified/etc. we don't strongly influence the
                # optimization loop yet; skip them.
                continue

            # Basic response-time approximation: seconds between first user message
            # and last qualifying question. This is good enough for trend analysis.
            first_log = logs[0]
            last_log = logs[-1]
            if first_log.created_at and last_log.created_at:
                delta = last_log.created_at - first_log.created_at
                response_time_sec = max(delta.total_seconds(), 1.0)
            else:
                response_time_sec = 30.0

            interactions.append(
                {
                    "lead_name": lead.name or "Unknown",
                    "channel": lead.channel or "unknown",
                    "service": lead.service_interest or "General",
                    "score": lead.score.value if lead.score else "unscored",
                    "outcome": outcome,
                    "questions_asked": questions_asked,
                    "response_time_sec": response_time_sec,
                }
            )

        return interactions
