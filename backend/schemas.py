
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class PatientData(BaseModel):
    
    patient_info: Dict[str, Any] = Field(default_factory=dict)
    symptoms: str = ""
    lab_results: Dict[str, Any] = Field(default_factory=dict)
    clinical_notes: str = ""
    images: List[str] = Field(default_factory=list)
    raw_text: str = ""

class SpecialistOpinion(BaseModel):
    
    model_name: str
    diagnosis: str
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str = ""
    detected_conditions: List[str] = Field(default_factory=list)
    key_findings: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = {
        'protected_namespaces': ()  # Disable warning for model_name field
    }

class Layer1Output(BaseModel):
    
    specialist_opinions: List[SpecialistOpinion]
    processing_time: float
    timestamp: datetime = Field(default_factory=datetime.now)

class FinalDiagnosis(BaseModel):
    
    primary_diagnosis: str
    confidence: float = Field(ge=0.0, le=1.0)
    secondary_diagnoses: List[Dict[str, Any]] = Field(default_factory=list)
    reasoning: str
    cross_validation_score: float
    anomaly_detected: bool = False
    anomaly_description: str = ""
    conflicts_resolved: List[str] = Field(default_factory=list)

class Evidence(BaseModel):
    
    text: str
    location: str  # e.g., "Page 1, Symptoms section"
    relevance_score: float
    annotation_type: str  # "highlight", "box", "circle"

class AnnotatedReport(BaseModel):
    
    diagnosis: FinalDiagnosis
    evidence_items: List[Evidence]
    explanation_text: str
    annotated_pdf_path: str
    annotated_images_paths: List[str] = Field(default_factory=list)
    visualization_data: Dict[str, Any] = Field(default_factory=dict)

class DiagnosisResponse(BaseModel):
    
    success: bool
    patient_data: PatientData
    layer1_output: Layer1Output
    layer2_diagnosis: FinalDiagnosis
    layer3_report: AnnotatedReport
    total_processing_time: float
    timestamp: datetime = Field(default_factory=datetime.now)
