import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Afterthought"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # AI Engine
    GEMINI_API_KEY: str = ""
    
    # Voice Engine
    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_VOICE_ID: str = "21m00Tcm4TlvDq8ikWAM"
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./afterthought.db"
    
    # Running Mode
    MOCK_MODE: bool = True

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

# Automatically fall back to mock mode if no Gemini key is provided
if not settings.GEMINI_API_KEY:
    settings.MOCK_MODE = True
