# 🏥 HealthFirst AI — Lead Conversion & Appointment Booking Agent

AI-Powered Lead Conversion Agent for healthcare providers. Captures leads from **WhatsApp**, **Instagram**, and **Web Chat**, qualifies them via conversational AI, scores them (Hot/Warm/Cold), books appointments autonomously, and provides real-time analytics.

## 🚀 Quick Start

### Backend (Python/FastAPI)

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Add your Gemini API key to .env
# GEMINI_API_KEY=your_key_here

# Run the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend (React/Vite)

```bash
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev
```

Open **http://localhost:5173** for the dashboard.

## 📡 API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/leads/` | GET | Get all leads |
| `/api/leads/pipeline` | GET | Get Kanban pipeline |
| `/api/leads/{id}` | GET | Get lead + conversations |
| `/api/leads/simulate` | POST | Simulate incoming message |
| `/api/leads/score` | POST | Trigger lead scoring |
| `/api/leads/book` | POST | Book appointment |
| `/api/analytics/conversion` | GET | Conversion analytics |
| `/api/analytics/improvement` | GET | AI improvement insights |
| `/api/appointments/` | GET | All appointments |
| `/api/webhooks/whatsapp` | POST | WhatsApp webhook |
| `/api/webhooks/instagram` | POST | Instagram webhook |
| `ws://localhost:8000/ws/chat/{id}` | WS | Web chat |

## 🧪 Testing Without API Keys

The backend works **without API keys** using keyword-based fallbacks. Add a **Gemini API key** to `.env` for full AI-powered conversations.

## 👥 Team Task Split

- **Person 1**: Backend core + AI engine (`services/`, `models/`)
- **Person 2**: Channel integrations (`channels/`, Meta setup)
- **Person 3**: Frontend dashboard (`frontend/src/pages/`)

## 🛠 Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy, SQLite, Google Gemini
- **Frontend**: React, Vite, Recharts, Vanilla CSS
- **Integrations**: WhatsApp Cloud API, Instagram Graph API, WebSocket
