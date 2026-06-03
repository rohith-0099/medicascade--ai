
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

# Layer 0: structured case facts + provenance

class Provenance(BaseModel):
    pdf_id: str
    page: int
    bbox: list[float] | None = None  # [x0, y0, x1, y1] in PDF coordinate space
    text_span: str | None = None     # minimal string slice used to derive the value


class Fact(BaseModel):
    label: str
    value: Any
    unit: str | None = None
    provenance: Provenance | None = None


class CaseFacts(BaseModel):
    demographics: list[Fact] = Field(default_factory=list)
    notes: list[Fact] = Field(default_factory=list)
    labs: list[Fact] = Field(default_factory=list)
    vitals: list[Fact] = Field(default_factory=list)
    meds: list[Fact] = Field(default_factory=list)
    history: list[Fact] = Field(default_factory=list)
    images: list[str] = Field(default_factory=list)  # base64 PNGs


class CaseDocument(BaseModel):
    case_id: str
    pdf_id: str
    source_pdf: str
    ingested_at: datetime
    facts: CaseFacts
    raw_text: str = ""
    tables: list[dict[str, Any]] = Field(default_factory=list)
    provenance_map: list[Provenance] = Field(default_factory=list)
    case_json_path: str | None = None
    images_dir: str | None = None


class Layer0Result(BaseModel):
    case: CaseDocument
    patient_view: "PatientData"              # compatibility bridge for existing modules
    case_json_path: str
    images_dir: str | None = None


# Layer 1: specialist views

class SpecialistView(BaseModel):
    agent: str           # e.g., "notes", "labs", "medication"
    role: str            # human-readable description
    model: str
    confidence: float = Field(ge=0.0, le=1.0)
    status: str = "completed"
    reason: str | None = None
    fallback_used: bool = False
    fallback_reason: str | None = None
    findings: dict[str, Any] = Field(default_factory=dict)
    evidence: list[Provenance] = Field(default_factory=list)


class Layer1Findings(BaseModel):
    case_id: str
    views: list[SpecialistView]
    candidate_diagnoses: list[dict[str, Any]] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)
    abnormal_labs: list[dict[str, Any]] = Field(default_factory=list)
    symptom_timeline: list[dict[str, Any]] = Field(default_factory=list)
    risk_factors: list[str] = Field(default_factory=list)
    aggregated_summary: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    findings_json_path: str | None = None


# Layer 2: validator output

class EvidenceSnippet(BaseModel):
    source: str            # PubMed / NICE / WHO
    title: str
    url: str
    snippet: str


class FinalAssessment(BaseModel):
    case_id: str
    final_problem_list: list[str] = Field(default_factory=list)
    final_differentials: list[dict[str, Any]] = Field(default_factory=list)
    final_red_flags: list[str] = Field(default_factory=list)
    supported_findings: list[str] = Field(default_factory=list)
    uncertain_findings: list[str] = Field(default_factory=list)
    contradicted_findings: list[str] = Field(default_factory=list)
    missing_data: list[str] = Field(default_factory=list)
    evidence_pack: list[EvidenceSnippet] = Field(default_factory=list)
    highlight_targets: list[Provenance] = Field(default_factory=list)
    decision_log: str = ""
    primary_diagnosis: str | None = None
    confidence: float = 0.0
    final_assessment_path: str | None = None


# Compatibility models (existing pipeline)

class PatientData(BaseModel):
    patient_info: dict[str, Any] = Field(default_factory=dict)
    symptoms: str = ""
    lab_results: dict[str, Any] = Field(default_factory=dict)
    clinical_notes: str = ""
    images: list[str] = Field(default_factory=list)
    raw_text: str = ""


class FinalDiagnosis(BaseModel):
    primary_diagnosis: str
    confidence: float = Field(ge=0.0, le=1.0)
    secondary_diagnoses: list[dict[str, Any]] = Field(default_factory=list)
    reasoning: str
    cross_validation_score: float
    anomaly_detected: bool = False
    anomaly_description: str = ""
    conflicts_resolved: list[str] = Field(default_factory=list)
    critical_points: list[dict[str, str]] = Field(default_factory=list)


class Evidence(BaseModel):
    text: str
    location: str  # e.g., "Page 1, Symptoms section"
    relevance_score: float
    annotation_type: str  # "highlight", "box", "circle"


class AnnotatedReport(BaseModel):
    diagnosis: FinalDiagnosis
    evidence_items: list[Evidence]
    explanation_text: str
    annotated_pdf_path: str
    annotated_images_paths: list[str] = Field(default_factory=list)
    visualization_data: dict[str, Any] = Field(default_factory=dict)


# Resolve forward reference
Layer0Result.model_rebuild()
