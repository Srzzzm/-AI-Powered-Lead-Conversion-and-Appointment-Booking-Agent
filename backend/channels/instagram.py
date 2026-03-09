"""Instagram Messaging API webhook handler."""

from fastapi import APIRouter, Request, Response, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from config import get_settings
from channels.router import MessageRouter

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])
settings = get_settings()


@router.get("/instagram")
async def verify_instagram_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    """Instagram webhook verification (GET request from Meta)."""
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        return Response(content=hub_challenge, media_type="text/plain")
    return Response(content="Verification failed", status_code=403)


@router.post("/instagram")
async def receive_instagram_message(request: Request, db: Session = Depends(get_db)):
    """Handle incoming Instagram DMs."""
    body = await request.json()

    try:
        entry = body.get("entry", [{}])[0]
        messaging = entry.get("messaging", [{}])[0]
        sender_id = messaging.get("sender", {}).get("id", "")
        message = messaging.get("message", {})
        text = message.get("text", "")

        if text:
            msg_router = MessageRouter(db)
            await msg_router.handle_message(
                channel="instagram",
                channel_user_id=sender_id,
                message_text=text,
            )

    except (KeyError, IndexError) as e:
        print(f"Error parsing Instagram message: {e}")

    return {"status": "ok"}


async def send_instagram_dm(recipient_id: str, text: str):
    """Send a DM via Instagram Graph API."""
    import httpx

    url = "https://graph.facebook.com/v18.0/me/messages"
    headers = {
        "Authorization": f"Bearer {settings.instagram_page_access_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": text},
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        return response.json()
