"""
HealthFirst AI Lead Conversion Agent — FastAPI Application
Main entry point that wires up all routes, webhooks, and WebSocket handlers.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from database import init_db
from config import get_settings
from api.leads import router as leads_router
from api.analytics import router as analytics_router
from api.appointments import router as appointments_router
from channels.whatsapp import router as whatsapp_router
from channels.instagram import router as instagram_router
from channels.webchat import router as webchat_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    init_db()
    print("🏥 HealthFirst AI Lead Agent started!")
    print("📊 Dashboard API: http://localhost:8000/api/leads/")
    print("💬 WebSocket Chat: ws://localhost:8000/ws/chat/{session_id}")
    print("📈 Analytics: http://localhost:8000/api/analytics/conversion")
    yield


app = FastAPI(
    title="HealthFirst AI Lead Conversion Agent",
    description="AI-Powered Lead Conversion and Appointment Booking Agent for Healthcare",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(leads_router)
app.include_router(analytics_router)
app.include_router(appointments_router)

# Register webhook routers
app.include_router(whatsapp_router)
app.include_router(instagram_router)

# Register WebSocket router
app.include_router(webchat_router)


@app.get("/")
async def root():
    return {
        "service": "HealthFirst AI Lead Conversion Agent",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "leads": "/api/leads/",
            "pipeline": "/api/leads/pipeline",
            "simulate": "/api/leads/simulate",
            "analytics": "/api/analytics/conversion",
            "improvement": "/api/analytics/improvement",
            "appointments": "/api/appointments/",
            "whatsapp_webhook": "/api/webhooks/whatsapp",
            "instagram_webhook": "/api/webhooks/instagram",
            "webchat_ws": "ws://localhost:8000/ws/chat/{session_id}",
        },
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
