"""REST API endpoints for the Lead Pipeline Dashboard."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db
from models.lead import Lead, LeadStatus, LeadScore
from models.conversation import Conversation, InteractionLog
from services.scoring import ScoringService
from services.appointment import AppointmentService
from services.nurture import NurtureService
from channels.router import MessageRouter

router = APIRouter(prefix="/api/leads", tags=["leads"])


# ── Pydantic schemas ──

class LeadResponse(BaseModel):
    id: int
    name: Optional[str]
    contact: Optional[str]
    channel: str
    service_interest: Optional[str]
    urgency: Optional[str]
    score: Optional[str]
    score_reasoning: Optional[str]
    status: str
    insurance_status: Optional[str]
    qualification_step: int
    created_at: str

    class Config:
        from_attributes = True


class SimulateMessageRequest(BaseModel):
    channel: str
    channel_user_id: str
    message_text: str
    sender_name: Optional[str] = None


class ScoreLeadRequest(BaseModel):
    lead_id: int


class BookAppointmentRequest(BaseModel):
    lead_id: int
    slot_id: str


# ── Endpoints ──

@router.get("/")
async def get_all_leads(db: Session = Depends(get_db)):
    """Get all leads with their current status."""
    leads = db.query(Lead).order_by(Lead.created_at.desc()).all()
    return [
        {
            "id": l.id,
            "name": l.name,
            "contact": l.contact,
            "channel": l.channel,
            "service_interest": l.service_interest,
            "urgency": l.urgency,
            "score": l.score.value if l.score else None,
            "score_reasoning": l.score_reasoning,
            "status": l.status.value if l.status else None,
            "insurance_status": l.insurance_status,
            "qualification_step": l.qualification_step or 0,
            "created_at": str(l.created_at) if l.created_at else None,
        }
        for l in leads
    ]


@router.get("/pipeline")
async def get_pipeline(db: Session = Depends(get_db)):
    """Get leads organized by pipeline stage for the Kanban board."""
    leads = db.query(Lead).all()
    pipeline = {
        "captured": [],
        "qualifying": [],
        "qualified": [],
        "converted": [],
        "nurturing": [],
        "lost": [],
    }
    for l in leads:
        status = l.status.value if l.status else "captured"
        if status in pipeline:
            pipeline[status].append({
                "id": l.id,
                "name": l.name,
                "channel": l.channel,
                "service_interest": l.service_interest,
                "score": l.score.value if l.score else None,
                "urgency": l.urgency,
                "created_at": str(l.created_at) if l.created_at else None,
            })
    return pipeline


@router.get("/{lead_id}")
async def get_lead(lead_id: int, db: Session = Depends(get_db)):
    """Get a single lead with conversation history."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    conversations = (
        db.query(Conversation)
        .filter(Conversation.lead_id == lead_id)
        .order_by(Conversation.created_at.asc())
        .all()
    )

    return {
        "lead": {
            "id": lead.id,
            "name": lead.name,
            "contact": lead.contact,
            "channel": lead.channel,
            "service_interest": lead.service_interest,
            "urgency": lead.urgency,
            "score": lead.score.value if lead.score else None,
            "score_reasoning": lead.score_reasoning,
            "status": lead.status.value if lead.status else None,
            "insurance_status": lead.insurance_status,
            "prior_experience": lead.prior_experience,
            "qualification_step": lead.qualification_step or 0,
            "created_at": str(lead.created_at) if lead.created_at else None,
        },
        "conversations": [
            {
                "id": c.id,
                "sender": c.sender,
                "message": c.message,
                "channel": c.channel,
                "created_at": str(c.created_at) if c.created_at else None,
            }
            for c in conversations
        ],
    }


@router.post("/simulate")
async def simulate_message(req: SimulateMessageRequest, db: Session = Depends(get_db)):
    """Simulate an incoming message from any channel (for testing)."""
    msg_router = MessageRouter(db)
    result = await msg_router.handle_message(
        channel=req.channel,
        channel_user_id=req.channel_user_id,
        message_text=req.message_text,
    )
    return result


@router.post("/score")
async def score_lead(req: ScoreLeadRequest, db: Session = Depends(get_db)):
    """Manually trigger lead scoring."""
    service = ScoringService(db)
    return service.score_lead(req.lead_id)


@router.post("/book")
async def book_appointment(req: BookAppointmentRequest, db: Session = Depends(get_db)):
    """Book an appointment for a lead."""
    service = AppointmentService(db)
    return service.book_appointment(req.lead_id, req.slot_id)


@router.get("/availability/{specialty}")
async def check_availability(specialty: str, db: Session = Depends(get_db)):
    """Check doctor availability by specialty."""
    service = AppointmentService(db)
    return service.check_doctor_availability(specialty)
