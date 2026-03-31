import os
import subprocess
from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    """
    Centralised runtime configuration for MediCascade.
    Values are read from the environment or backend/.env (see .env.example).
    """

    # ── External providers ──────────────────────────────────────────────────
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_VALIDATOR_MODEL: str = "meta-llama/llama-3.3-70b-instruct:free"

    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # Vision / OCR models (free, HF-hosted)
    HF_API_TOKEN: str = ""
    HF_VISION_MODEL: str = "google/medgemma-4b-it"
    # Back-compat aliases for legacy specialist modules
    HF_IMAGING_MODEL: str = "google/medgemma-4b-it"
    HF_LAB_MODEL: str = "google/medgemma-4b-it"
    HF_LITERATURE_MODEL: str = "google/medgemma-4b-it"
    HF_SYMPTOM_MODEL: str = "google/medgemma-4b-it"
    HF_RISK_LM_MODEL: str = "google/medgemma-4b-it"

    # ── Storage / I-O ───────────────────────────────────────────────────────
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024
    UPLOAD_DIR: str = "uploads"
    OUTPUT_DIR: str = "outputs"
    CASE_DIR: str = "outputs/cases"

    # ── Ollama local fallback (requires manual Ollama setup) ─────────────────
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"

    # ── Database ────────────────────────────────────────────────────────────
    DB_PATH: str = "outputs/medicascade.db"

    # ── Runtime knobs ───────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LAYER1_TIMEOUT: int = 90
    LAYER2_TIMEOUT: int = 120
    LAYER3_TIMEOUT: int = 90
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )


def check_ollama_available() -> bool:
    """Check whether the Ollama CLI is installed and responsive."""
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            timeout=3,
            check=False,
        )
        return result.returncode == 0
    except (FileNotFoundError, TimeoutError, subprocess.TimeoutExpired):
        return False


settings = Settings()

# Ensure required folders exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
os.makedirs(settings.CASE_DIR, exist_ok=True)
