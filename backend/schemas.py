"""
Pydantic schemas for data validation across all layers
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class PatientData(BaseModel):
    """Extracted patient information from Layer 0"""
    patient_info: Dict[str, Any] = Field(default_factory=dict)
    symptoms: str = ""
    lab_results: Dict[str, Any] = Field(default_factory=dict)
    clinical_notes: str = ""
    images: List[str] = Field(default_factory=list)  # Base64 encoded images
    raw_text: str = ""


class SpecialistOpinion(BaseModel):
    """Output from a single Layer 1 specialist model"""
    model_name: str
    diagnosis: str
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str = ""
    detected_conditions: List[str] = Field(default_factory=list)
    key_findings: Dict[str, Any] = Field(default_factory=dict)


class Layer1Output(BaseModel):
    """Aggregated output from all Layer 1 specialists"""
    specialist_opinions: List[SpecialistOpinion]
    processing_time: float
    timestamp: datetime = Field(default_factory=datetime.now)


class FinalDiagnosis(BaseModel):
    """Layer 2 validated diagnosis"""
    primary_diagnosis: str
    confidence: float = Field(ge=0.0, le=1.0)
    secondary_diagnoses: List[Dict[str, Any]] = Field(default_factory=list)
    reasoning: str
    cross_validation_score: float
    anomaly_detected: bool = False
    anomaly_description: str = ""
    conflicts_resolved: List[str] = Field(default_factory=list)


class Evidence(BaseModel):
    """Evidence item for Layer 3 explanation"""
    text: str
    location: str  # e.g., "Page 1, Symptoms section"
    relevance_score: float
    annotation_type: str  # "highlight", "box", "circle"


class AnnotatedReport(BaseModel):
    """Final output from Layer 3"""
    diagnosis: FinalDiagnosis
    evidence_items: List[Evidence]
    explanation_text: str
    annotated_pdf_path: str
    annotated_images_paths: List[str] = Field(default_factory=list)
    visualization_data: Dict[str, Any] = Field(default_factory=dict)


class DiagnosisResponse(BaseModel):
    """Complete API response"""
    success: bool
    patient_data: PatientData
    layer1_output: Layer1Output
    layer2_diagnosis: FinalDiagnosis
    layer3_report: AnnotatedReport
    total_processing_time: float
    timestamp: datetime = Field(default_factory=datetime.now)
