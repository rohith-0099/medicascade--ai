
import os
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional

class Settings(BaseSettings):

    HF_API_TOKEN: str = ""
    HUGGINGFACE_TOKEN: str = ""  # Backward compatibility
    
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_BASE_URL: str = "http://localhost:11434"  # Backward compatibility
    OLLAMA_MODEL: str = "llama3.2:3b"
    
    LOG_LEVEL: str = "INFO"
    
    ANOMALY_DETECTION_CONTAMINATION: float = 0.1
    CONFIDENCE_THRESHOLD: float =0.7
    
    HF_VISION_MODEL: str = "google/medgemma-4b-it"
    HF_TEXT_MODEL: str = "google/gemma-2-9b-it"
    HF_SYMPTOM_MODEL: str = "google/gemma-2-9b-it"
    HF_LAB_MODEL: str = "google/gemma-2-9b-it"
    HF_NOTES_MODEL: str = "google/gemma-2-9b-it"
    
    GROQ_API_KEY: str = ""
    
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024
    UPLOAD_DIR: str = "uploads"
    OUTPUT_DIR: str = "outputs"
    
    LAYER1_TIMEOUT: int = 30
    LAYER2_TIMEOUT: int = 60
    LAYER3_TIMEOUT: int = 45
    
    ANOMALY_CONTAMINATION: float = 0.1
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra='ignore'  # Ignore extra fields in .env
    )

settings = Settings()

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
