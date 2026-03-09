"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # AI
    gemini_api_key: str = ""

    # WhatsApp
    meta_app_secret: str = ""
    whatsapp_access_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_verify_token: str = "healthcare_lead_agent_verify"

    # Instagram
    instagram_page_access_token: str = ""

    # Database
    database_url: str = "sqlite:///./leads.db"

    # CORS
    cors_origins: str = "http://localhost:5173"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
