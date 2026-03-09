"""AI Conversation Engine — powered by Google Gemini."""

import json
import google.generativeai as genai
from config import get_settings

settings = get_settings()


class AIEngine:
    def __init__(self):
        if settings.gemini_api_key:
            genai.configure(api_key=settings.gemini_api_key)
            self.model = genai.GenerativeModel("gemini-1.5-flash")
        else:
            self.model = None

    async def extract_lead_info(self, raw_message: str) -> dict:
        """Extract structured lead information from a raw message."""
        prompt = f"""Extract the following from this healthcare inquiry message. Return ONLY valid JSON.
Message: "{raw_message}"

Return JSON with these fields:
- name: patient name if mentioned, else null
- contact: phone/email if mentioned, else null
- service_interest: the medical service/treatment they need (e.g. "Orthopedics - Knee Replacement")
- urgency: "high", "medium", or "low" based on how urgent their need seems

JSON:"""
        if self.model:
            response = self.model.generate_content(prompt)
            try:
                text = response.text.strip()
                if text.startswith("```"):
                    text = text.split("\n", 1)[1].rsplit("```", 1)[0]
                return json.loads(text)
            except (json.JSONDecodeError, IndexError):
                return {"name": None, "contact": None, "service_interest": "General Inquiry", "urgency": "medium"}
        else:
            # Fallback: basic keyword extraction
            return self._fallback_extract(raw_message)

    async def classify_intent(self, message_text: str) -> dict:
        """Classify the intent of a message into service category and urgency."""
        prompt = f"""Classify this healthcare inquiry. Return ONLY valid JSON.
Message: "{message_text}"

Return JSON with:
- service_category: one of [Orthopedics, Cardiology, Pediatrics, Diagnostics, Dentistry, Ophthalmology, Obstetrics, Health Checkup, General]
- urgency_score: integer 1-10 (10 = emergency, 1 = just browsing)
- intent: one of [book_appointment, get_info, compare_options, emergency, general_inquiry]

JSON:"""
        if self.model:
            response = self.model.generate_content(prompt)
            try:
                text = response.text.strip()
                if text.startswith("```"):
                    text = text.split("\n", 1)[1].rsplit("```", 1)[0]
                return json.loads(text)
            except (json.JSONDecodeError, IndexError):
                return {"service_category": "General", "urgency_score": 5, "intent": "general_inquiry"}
        else:
            return {"service_category": "General", "urgency_score": 5, "intent": "general_inquiry"}

    async def generate_personalized_greeting(self, lead_name: str, service_interest: str, channel: str) -> str:
        """Generate a personalized opening message — NOT a generic 'How can I help?'"""
        prompt = f"""You are a friendly healthcare assistant at HealthFirst Hospital.
Generate a warm, personalized greeting for a new patient inquiry.

Patient name: {lead_name or "there"}
They are interested in: {service_interest}
They contacted via: {channel}

Rules:
- Do NOT say "How can I help you?" or any generic greeting
- Reference their specific service/interest
- Be warm but professional
- Keep it under 50 words
- If they mentioned urgency, acknowledge it

Greeting:"""
        if self.model:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        else:
            name = lead_name or "there"
            return (
                f"Hi {name}! 👋 Thank you for reaching out about {service_interest}. "
                f"I'm here to help you get the care you need. "
                f"Let me ask a few quick questions so I can find the best option for you."
            )

    async def generate_qualification_response(
        self, lead_context: dict, user_answer: str, question_number: int
    ) -> dict:
        """Generate the next adaptive qualification question based on context."""
        prompt = f"""You are a healthcare qualification assistant. Based on the conversation so far,
generate the next question to qualify this lead.

Lead context:
- Name: {lead_context.get('name', 'Unknown')}
- Service interest: {lead_context.get('service_interest', 'Unknown')}
- Urgency: {lead_context.get('urgency', 'Unknown')}
- Question number: {question_number} of 5
- Previous answer: "{user_answer}"

You need to understand:
1. What specific treatment/service they need
2. Timeline urgency
3. Insurance or self-pay status
4. Prior hospital experience

Generate the most relevant next question. Return ONLY valid JSON:
{{
  "question": "the next question to ask",
  "category": "what this question determines (service/urgency/insurance/experience)",
  "is_final": true/false (true if this is the last qualification question)
}}

JSON:"""
        if self.model:
            response = self.model.generate_content(prompt)
            try:
                text = response.text.strip()
                if text.startswith("```"):
                    text = text.split("\n", 1)[1].rsplit("```", 1)[0]
                return json.loads(text)
            except (json.JSONDecodeError, IndexError):
                return {
                    "question": "Could you tell me more about your timeline for this?",
                    "category": "urgency",
                    "is_final": question_number >= 4,
                }
        else:
            questions = [
                {"question": "What specific treatment or service are you looking for?", "category": "service", "is_final": False},
                {"question": "How soon do you need this? Is it urgent?", "category": "urgency", "is_final": False},
                {"question": "Will you be using insurance or paying out of pocket?", "category": "insurance", "is_final": False},
                {"question": "Have you visited our hospital before?", "category": "experience", "is_final": False},
                {"question": "Would you like me to check available appointment slots for you?", "category": "conversion", "is_final": True},
            ]
            idx = min(question_number, len(questions) - 1)
            return questions[idx]

    def _fallback_extract(self, message: str) -> dict:
        """Basic keyword-based extraction when AI is unavailable."""
        msg_lower = message.lower()

        service = "General Inquiry"
        if any(w in msg_lower for w in ["knee", "hip", "joint", "orthop", "bone", "fracture"]):
            service = "Orthopedics"
        elif any(w in msg_lower for w in ["heart", "cardiac", "chest pain", "cardio"]):
            service = "Cardiology"
        elif any(w in msg_lower for w in ["child", "pediatr", "baby", "kid", "fever"]):
            service = "Pediatrics"
        elif any(w in msg_lower for w in ["mri", "scan", "x-ray", "diagnos", "test", "blood"]):
            service = "Diagnostics"
        elif any(w in msg_lower for w in ["dental", "tooth", "teeth", "implant"]):
            service = "Dentistry"
        elif any(w in msg_lower for w in ["eye", "vision", "cataract", "ophthal"]):
            service = "Ophthalmology"
        elif any(w in msg_lower for w in ["pregnan", "materni", "obstet", "delivery"]):
            service = "Obstetrics"
        elif any(w in msg_lower for w in ["checkup", "check-up", "full body"]):
            service = "Health Checkup"

        urgency = "medium"
        if any(w in msg_lower for w in ["urgent", "immediately", "asap", "emergency", "tomorrow", "today"]):
            urgency = "high"
        elif any(w in msg_lower for w in ["browsing", "comparing", "just looking", "information"]):
            urgency = "low"

        return {
            "name": None,
            "contact": None,
            "service_interest": service,
            "urgency": urgency,
        }
