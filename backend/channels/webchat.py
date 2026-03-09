"""WebSocket-based web chat handler."""

import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from database import get_db, SessionLocal
from channels.router import MessageRouter

router = APIRouter(tags=["webchat"])

# Track active connections
active_connections: dict[str, WebSocket] = {}


@router.websocket("/ws/chat/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for the web chat widget."""
    await websocket.accept()
    active_connections[session_id] = websocket

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            text = message.get("text", "")

            if text:
                db = SessionLocal()
                try:
                    msg_router = MessageRouter(db)
                    response = await msg_router.handle_message(
                        channel="webchat",
                        channel_user_id=session_id,
                        message_text=text,
                    )
                    # Send response back via WebSocket
                    await websocket.send_text(json.dumps({
                        "type": "agent_message",
                        "text": response.get("agent_response", ""),
                        "lead_id": response.get("lead_id"),
                        "status": response.get("status"),
                    }))
                finally:
                    db.close()

    except WebSocketDisconnect:
        del active_connections[session_id]


async def send_webchat_message(session_id: str, text: str):
    """Send a message to a web chat user."""
    ws = active_connections.get(session_id)
    if ws:
        await ws.send_text(json.dumps({
            "type": "agent_message",
            "text": text,
        }))
