from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Afterthought"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # AI Engine
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    FORCE_OFFLINE_AI: bool = False

    # Voice Engine (ElevenLabs)
    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_VOICE_ID: str = "21m00Tcm4TlvDq8ikWAM"
    ELEVENLABS_MODEL_ID: str = "eleven_turbo_v2_5"
    ELEVENLABS_STT_MODEL_ID: str = "scribe_v1"

    # Workspace Connector
    USE_MOCK_WORKSPACE: bool = True

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./afterthought.db"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def gemini_enabled(self) -> bool:
        return bool(self.GEMINI_API_KEY.strip()) and not self.FORCE_OFFLINE_AI

    @property
    def elevenlabs_enabled(self) -> bool:
        return bool(self.ELEVENLABS_API_KEY.strip())

    @property
    def MOCK_MODE(self) -> bool:
        """Backwards-compatible indicator for offline AI mode."""
        return not self.gemini_enabled


settings = Settings()
