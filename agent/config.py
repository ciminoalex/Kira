"""
Configurazione centralizzata via pydantic-settings.
Legge variabili da .env o environment.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM
    ANTHROPIC_API_KEY: str = ""

    # Database
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "kira"
    POSTGRES_USER: str = "kira"
    POSTGRES_PASSWORD: str = ""

    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_ALLOWED_USER_IDS: str = ""

    # STT / TTS
    DEEPGRAM_API_KEY: str = ""
    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_VOICE_ID: str = ""

    # Supermemory
    SUPERMEMORY_API_KEY: str = ""
    SUPERMEMORY_CONTAINER_TAG: str = "kira_alessandro"

    # Gmail MCP (OAuth)
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REFRESH_TOKEN: str = ""

    # Web Search
    TAVILY_API_KEY: str = ""

    # Scheduler
    BRIEFING_TIME: str = "07:30"
    REMINDER_MINUTES_BEFORE: int = 15

    # Model Routing
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    DEFAULT_MODEL_TIER: str = "advanced"

    # Claude Code
    CLAUDE_CODE_WORKDIR: str = "/home/kira/workspace"
    CLAUDE_CODE_MAX_BUDGET: float = 5.0
    CLAUDE_CODE_TIMEOUT: int = 300

    # Telemetria
    AGNO_TELEMETRY: bool = False

    @property
    def db_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def async_db_url(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()
