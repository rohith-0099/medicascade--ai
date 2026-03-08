
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ── Layer 0: structured case facts + provenance ─────────────────────────────

class Provenance(BaseModel):
    pdf_id: str
    page: int
    bbox: Optional[List[float]] = None  # [x0, y0, x1, y1] in PDF coordinate space
    text_span: Optional[str] = None     # minimal string slice used to derive the value


class Fact(BaseModel):
    label: str
    value: Any
    unit: Optional[str] = None
    provenance: Optional[Provenance] = None


class CaseFacts(BaseModel):
    demographics: List[Fact] = Field(default_factory=list)
    notes: List[Fact] = Field(default_factory=list)
    labs: List[Fact] = Field(default_factory=list)
    vitals: List[Fact] = Field(default_factory=list)
    meds: List[Fact] = Field(default_factory=list)
    history: List[Fact] = Field(default_factory=list)
    images: List[str] = Field(default_factory=list)  # base64 PNGs


class CaseDocument(BaseModel):
    case_id: str
    pdf_id: str
    source_pdf: str
    ingested_at: datetime
    facts: CaseFacts
    raw_text: str = ""
    tables: List[Dict[str, Any]] = Field(default_factory=list)
    provenance_map: List[Provenance] = Field(default_factory=list)
    case_json_path: Optional[str] = None
    images_dir: Optional[str] = None


class Layer0Result(BaseModel):
    case: CaseDocument
    patient_view: "PatientData"              # compatibility bridge for existing modules
    case_json_path: str
    images_dir: Optional[str] = None


# ── Layer 1: specialist views ───────────────────────────────────────────────

class SpecialistView(BaseModel):
    agent: str           # e.g., "notes", "labs", "medication"
    role: str            # human-readable description
    model: str
    confidence: float = Field(ge=0.0, le=1.0)
    findings: Dict[str, Any] = Field(default_factory=dict)
    evidence: List[Provenance] = Field(default_factory=list)


class Layer1Findings(BaseModel):
    case_id: str
    views: List[SpecialistView]
    candidate_diagnoses: List[Dict[str, Any]] = Field(default_factory=list)
    red_flags: List[str] = Field(default_factory=list)
    abnormal_labs: List[Dict[str, Any]] = Field(default_factory=list)
    symptom_timeline: List[Dict[str, Any]] = Field(default_factory=list)
    risk_factors: List[str] = Field(default_factory=list)
    aggregated_summary: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    findings_json_path: Optional[str] = None


# ── Layer 2: validator output ───────────────────────────────────────────────

class EvidenceSnippet(BaseModel):
    source: str            # PubMed / NICE / WHO
    title: str
    url: str
    snippet: str


class FinalAssessment(BaseModel):
    case_id: str
    final_problem_list: List[str] = Field(default_factory=list)
    final_differentials: List[Dict[str, Any]] = Field(default_factory=list)
    final_red_flags: List[str] = Field(default_factory=list)
    supported_findings: List[str] = Field(default_factory=list)
    uncertain_findings: List[str] = Field(default_factory=list)
    contradicted_findings: List[str] = Field(default_factory=list)
    missing_data: List[str] = Field(default_factory=list)
    evidence_pack: List[EvidenceSnippet] = Field(default_factory=list)
    highlight_targets: List[Provenance] = Field(default_factory=list)
    decision_log: str = ""
    primary_diagnosis: Optional[str] = None
    confidence: float = 0.0
    final_assessment_path: Optional[str] = None


# ── MRI 3D segmentation output (nnU-Net + Plotly) ───────────────────────────

class MriPlotlyMesh(BaseModel):
    x: List[float] = Field(default_factory=list)
    y: List[float] = Field(default_factory=list)
    z: List[float] = Field(default_factory=list)
    i: List[int] = Field(default_factory=list)
    j: List[int] = Field(default_factory=list)
    k: List[int] = Field(default_factory=list)
    vertex_count: int = 0
    face_count: int = 0


class MriTumorStat(BaseModel):
    volume_cc: float = 0.0
    voxel_count: int = 0


class MriAnalyzeResponse(BaseModel):
    request_id: str
    meshes: Dict[str, Optional[MriPlotlyMesh]] = Field(default_factory=dict)
    stats: Dict[str, MriTumorStat] = Field(default_factory=dict)
    processing_time: float = 0.0
    volume_shape: List[int] = Field(default_factory=list)
    voxel_spacing: List[float] = Field(default_factory=list)


# ── Compatibility models (existing pipeline) ────────────────────────────────

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

    model_config = {"protected_namespaces": ()}


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
    critical_points: List[Dict[str, str]] = Field(default_factory=list)


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


# Resolve forward reference
Layer0Result.model_rebuild()
