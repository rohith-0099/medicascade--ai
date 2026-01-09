"""
Configuration settings for the Universal AI Disease Prediction Engine
"""
import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    HUGGINGFACE_TOKEN: Optional[str] = os.getenv("HUGGINGFACE_TOKEN", "")
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"
    
    # HuggingFace Models - Updated to working models
    HF_SYMPTOM_MODEL: str = "microsoft/BioGPT-Large"
    HF_LAB_MODEL: str = "emilyalsentzer/Bio_ClinicalBERT"
    HF_NOTES_MODEL: str = "microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext"
    HF_VISION_MODEL: str = "google/vit-base-patch16-224"
    
    # File Upload Settings
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    UPLOAD_DIR: str = "uploads"
    OUTPUT_DIR: str = "outputs"
    
    # Processing Settings
    LAYER1_TIMEOUT: int = 30  # seconds per model
    LAYER2_TIMEOUT: int = 60
    LAYER3_TIMEOUT: int = 45
    
    # Anomaly Detection
    ANOMALY_CONTAMINATION: float = 0.1
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# Create necessary directories
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
