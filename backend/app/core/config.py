from pathlib import Path
from typing import List
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Automatically detect backend directory and workspace root directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # backend/
ROOT_DIR = BASE_DIR.parent  # repository root/

# Load environment variables into os.environ if .env file exists
for candidate_env in [BASE_DIR / ".env", ROOT_DIR / ".env", Path(".env")]:
    if candidate_env.exists():
        load_dotenv(dotenv_path=candidate_env, override=False)


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Support Coach"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "sqlite:///./support_coach.db"

    # Security & Authentication
    SECRET_KEY: str = "infosys-ai-support-coach-jwt-secret-key-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # LLM Settings (Google Gemini)
    LLM_PROVIDER: str = "gemini"  # "gemini" or "mock"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gemini-3.5-flash"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.5-flash"

    # Hugging Face
    USE_HF_LOCAL_MODELS: bool = False

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    model_config = SettingsConfigDict(
        env_file=(str(BASE_DIR / ".env"), str(ROOT_DIR / ".env"), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
