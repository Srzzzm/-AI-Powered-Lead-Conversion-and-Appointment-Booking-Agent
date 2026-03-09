"""WhatsApp Business Cloud API webhook handler."""

import hmac
import hashlib
from fastapi import APIRouter, Request, Response, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from config import get_settings
from channels.router import MessageRouter

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])
settings = get_settings()


@router.get("/whatsapp")
async def verify_whatsapp_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    """WhatsApp webhook verification (GET request from Meta)."""
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        return Response(content=hub_challenge, media_type="text/plain")
    return Response(content="Verification failed", status_code=403)


@router.post("/whatsapp")
async def receive_whatsapp_message(request: Request, db: Session = Depends(get_db)):
    """Handle incoming WhatsApp messages."""
    body = await request.json()

    try:
        entry = body.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})

        # Check if this is a message (not a status update)
        messages = value.get("messages", [])
        if not messages:
            return {"status": "ok"}  # Status update, acknowledge

        for message in messages:
            sender = message.get("from", "")
            msg_type = message.get("type", "text")

            if msg_type == "text":
                text = message.get("text", {}).get("body", "")
            else:
                text = f"[{msg_type} message received]"

            # Route to message handler
            msg_router = MessageRouter(db)
            await msg_router.handle_message(
                channel="whatsapp",
                channel_user_id=sender,
                message_text=text,
            )

    except (KeyError, IndexError) as e:
        print(f"Error parsing WhatsApp message: {e}")

    return {"status": "ok"}


async def send_whatsapp_message(to: str, text: str):
    """Send a message via WhatsApp Cloud API."""
    import httpx

    url = f"https://graph.facebook.com/v18.0/{settings.whatsapp_phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {settings.whatsapp_access_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        return response.json()
