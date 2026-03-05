
import os
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional

class Settings(BaseSettings):

    # ── HuggingFace — set in .env ─────────────────────────────────────────
    # Copy .env.example → .env and fill in your token. DO NOT hardcode here.
    HF_API_TOKEN: str = ""
    HUGGINGFACE_TOKEN: str = ""  # alias for backward-compat

    # ── OLLAMA (local fallback) ─────────────────────
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"

    # ── Layer 1: Specialist Models ──────────────────
    # Specialist 1 — Medical Imaging (MedGemma 27B → use 4B via API)
    HF_VISION_MODEL: str = "google/medgemma-4b-it"
    HF_IMAGING_MODEL: str = "google/medgemma-4b-it"

    # Specialist 2 — Symptoms & Clinical Notes
    HF_SYMPTOM_MODEL: str = "UFNLP/gatortron-medium"

    # Specialist 3 — Lab Results
    HF_LAB_MODEL: str = "google/medgemma-4b-it"

    # Specialist 4 — Biomedical Literature Matching
    HF_LITERATURE_MODEL: str = "microsoft/BioGPT-Large"

    # Specialist 5 — Patient Risk Scoring
    HF_RISK_LM_MODEL: str = "MaziyarPanahi/OpenMed-SuperClinical-434M"

    # ── Layer 2: Cross-Validation (MedGemma 27B text) ──
    HF_VALIDATOR_MODEL: str = "google/medgemma-4b-it"

    # ── Layer 3: XAI Explanation (MedGemma 4B + SHAP + Grad-CAM) ──
    HF_EXPLAINER_MODEL: str = "google/medgemma-4b-it"

    # ── Legacy ──────────────────────────────────────
    HF_TEXT_MODEL: str = "google/medgemma-4b-it"
    HF_NOTES_MODEL: str = "UFNLP/gatortron-medium"

    # ── External APIs ───────────────────────────────
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""

    # ── System ──────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    ANOMALY_DETECTION_CONTAMINATION: float = 0.1
    CONFIDENCE_THRESHOLD: float = 0.7
    ANOMALY_CONTAMINATION: float = 0.1

    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024
    UPLOAD_DIR: str = "uploads"
    OUTPUT_DIR: str = "outputs"

    LAYER1_TIMEOUT: int = 60
    LAYER2_TIMEOUT: int = 90
    LAYER3_TIMEOUT: int = 60

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra='ignore'
    )

settings = Settings()

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
