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
| `/api/leads/pipeline` | GET | Get Kanban pipeline (by stage) |
| `/api/leads/{id}` | GET | Get lead + conversations |
| `/api/leads/simulate` | POST | Simulate incoming message |
| `/api/leads/score` | POST | Trigger lead scoring (Hot/Warm/Cold) |
| `/api/leads/book` | POST | Book appointment (given slot id) |
| `/api/leads/availability/{specialty}` | GET | Check doctor availability by specialty |
| `/api/analytics/conversion` | GET | Conversion analytics (by channel/service/score) |
| `/api/analytics/improvement` | GET | AI improvement insights + active strategies |
| `/api/appointments/` | GET | All appointments |
| `/api/webhooks/whatsapp` | POST | WhatsApp webhook |
| `/api/webhooks/instagram` | POST | Instagram webhook |
| `ws://localhost:8000/ws/chat/{id}` | WS | Web chat |

## 🧩 Spec → Implementation Mapping (Simulated Tools)

These functions from the problem statement are implemented as services/endpoints:

- **`capture_lead(channel, raw_message)`**  
  - **Backend**: `LeadCaptureService.capture_lead`  
  - **Used by**: `MessageRouter.handle_message`, `/api/leads/simulate`

- **`classify_intent(message_text)`**  
  - **Backend**: `LeadCaptureService.classify_intent` → `AIEngine.classify_intent`

- **`ask_qualification_question(lead_id, question_number, context)`**  
  - **Backend**: `QualificationService.ask_qualification_question`  
  - Uses `questions.json` + `ConversationStrategy` for adaptive flows.

- **`score_lead(lead_id, qualification_answers)`**  
  - **Backend**: `ScoringService.score_lead`  
  - **Endpoint**: `POST /api/leads/score`

- **`check_doctor_availability(specialty, date_range)`**  
  - **Backend**: `AppointmentService.check_doctor_availability` (mock `doctors.json`)  
  - **Endpoint**: `GET /api/leads/availability/{specialty}`

- **`book_appointment(lead_id, slot_id)`**  
  - **Backend**: `AppointmentService.book_appointment`  
  - **Endpoint**: `POST /api/leads/book`

- **`add_to_nurture_sequence(lead_id, sequence_type)`**  
  - **Backend**: `NurtureService.add_to_nurture_sequence` (warm/cold flows)  
  - Used automatically for **Warm/Cold** leads in `MessageRouter._handle_scored_lead`.

- **`log_interaction(lead_id, stage, outcome)`**  
  - **Backend**: `InteractionLog` model  
  - Logged from capture, qualification, scoring, booking, and nurturing services.

- **`get_conversion_analytics(date_range)`**  
  - **Backend**: `ImprovementService.get_conversion_analytics`  
  - **Endpoint**: `GET /api/analytics/conversion`

Additionally, the **adaptive learning loop** is implemented via:

- `ImprovementService.analyze_improvement_opportunities`  
  - Combines `mock_data/historical.json` + live `InteractionLog` data  
  - Identifies top question sequences and updates `ConversationStrategy` rows  
  - Exposed in the UI on the **AI Insights** page.

`QualificationService` then reads the active `ConversationStrategy` to drive the default 3–5 question qualification flow, so after enough interactions (≥20) the system **automatically updates** its default question sequence.

## 🧪 Testing Without API Keys

The backend works **without API keys** using keyword-based fallbacks. Add a **Gemini API key** to `.env` for full AI-powered conversations.

## 🎬 Suggested Demo Flow

1. **Simulate 3–4 Hot/Warm/Cold leads** from the **Simulate Lead** page:  
   - Watch personalized greetings + 3–5 qualification questions.  
   - Observe leads moving across stages in the **Pipeline Dashboard**.
2. For a **Hot** lead, let the agent auto-book an appointment:  
   - See confirmation details and preparation instructions.  
3. For **Warm/Cold** leads, show:  
   - Enrolment into appropriate nurture flows in **Conversations** and **Dashboard**.  
4. Open **Analytics** to show:  
   - Conversion by channel, by service, and score distribution.  
5. Open **AI Insights**:  
   - Explain response time impact and top question sequences, and mention that after enough interactions the system updates its active `ConversationStrategy` automatically.

## 👥 Team Task Split

- **Person 1**: Backend core + AI engine (`services/`, `models/`)
- **Person 2**: Channel integrations (`channels/`, Meta setup)
- **Person 3**: Frontend dashboard (`frontend/src/pages/`)

## 🛠 Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy, SQLite, Google Gemini
- **Frontend**: React, Vite, Recharts, Vanilla CSS
- **Integrations**: WhatsApp Cloud API, Instagram Graph API, WebSocket
