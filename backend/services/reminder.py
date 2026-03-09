"""Reminder service — nudges leads who haven't replied in time."""

from datetime import datetime, timedelta, timezone
from typing import List

from sqlalchemy.orm import Session

from config import get_settings
from models.lead import Lead, LeadStatus
from models.conversation import Conversation
from models.conversation import InteractionLog
from channels.whatsapp import send_whatsapp_message
from channels.instagram import send_instagram_dm
from channels.webchat import send_webchat_message


settings = get_settings()


class ReminderService:
    def __init__(self, db: Session):
        self.db = db

    async def run_reminder_tick(self) -> int:
        """
        Scan active leads and send a gentle reminder to those who
        haven't replied after the last agent question.

        Returns number of reminders sent.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(
            minutes=settings.reminder_inactive_minutes
        )

        # Only consider leads that are still in an active stage
        active_statuses: List[LeadStatus] = [
            LeadStatus.CAPTURED,
            LeadStatus.QUALIFYING,
            LeadStatus.QUALIFIED,
            LeadStatus.NURTURING,
        ]

        leads = (
            self.db.query(Lead)
            .filter(Lead.status.in_(active_statuses))
            .all()
        )

        sent_count = 0
        for lead in leads:
            last_agent, last_user = self._get_last_messages(lead.id)
            if not last_agent:
                continue

            # Only remind if the last message was from the agent,
            # it is older than cutoff, and there is no user reply after it.
            if last_agent.created_at is None or last_agent.created_at > cutoff:
                continue

            if last_user and last_user.created_at and last_user.created_at > last_agent.created_at:
                # User has already replied after our last question
                continue

            # Avoid spamming: check if we already sent a reminder after this last_agent
            if self._already_reminded_after(lead.id, last_agent.created_at):
                continue

            reminder_text = (
                "It looks like we haven't heard back from you yet. "
                "Just to confirm, what healthcare service do you need help with right now?"
            )

            # Send via the appropriate channel
            if lead.channel == "whatsapp" and lead.channel_user_id:
                await send_whatsapp_message(lead.channel_user_id, reminder_text)
            elif lead.channel == "instagram" and lead.channel_user_id:
                await send_instagram_dm(lead.channel_user_id, reminder_text)
            elif lead.channel == "webchat" and lead.channel_user_id:
                await send_webchat_message(lead.channel_user_id, reminder_text)

            # Persist as a conversation message
            conv = Conversation(
                lead_id=lead.id,
                sender="agent",
                message=reminder_text,
                channel=lead.channel,
            )
            self.db.add(conv)

            log = InteractionLog(
                lead_id=lead.id,
                stage="reminder",
                outcome="sent",
                details=f"Reminder sent after inactivity since {last_agent.created_at}",
            )
            self.db.add(log)
            self.db.commit()

            sent_count += 1

        return sent_count

    def _get_last_messages(self, lead_id: int):
        """Return (last_agent_msg, last_user_msg) Conversation objects for a lead."""
        convs = (
            self.db.query(Conversation)
            .filter(Conversation.lead_id == lead_id)
            .order_by(Conversation.created_at.desc())
            .all()
        )
        last_agent = next((c for c in convs if c.sender == "agent"), None)
        last_user = next((c for c in convs if c.sender == "user"), None)
        return last_agent, last_user

    def _already_reminded_after(self, lead_id: int, since_time) -> bool:
        """Check if a reminder has already been sent after the given timestamp."""
        q = (
            self.db.query(InteractionLog)
            .filter(
                InteractionLog.lead_id == lead_id,
                InteractionLog.stage == "reminder",
            )
        )
        if since_time:
            q = q.filter(InteractionLog.created_at > since_time)
        return q.first() is not None

