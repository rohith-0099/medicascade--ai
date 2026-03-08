# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm   # required NLP model

# Run backend (development)
uvicorn main:app --reload --port 8000
# or
python main.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev       # dev server at http://localhost:5173
npm run build     # production build
```

### System dependencies
```bash
sudo apt-get install -y tesseract-ocr poppler-utils
```

## Environment

Copy `backend/.env.example` to `backend/.env` and fill in:

| Variable | Purpose |
|---|---|
| `GROQ_API_KEY` | Layer 1 & 3 text specialists (llama-3.3-70b-versatile) |
| `OPENROUTER_API_KEY` | Layer 2 validator (qwen/qwen-2.5-72b-instruct:free, hardcoded) |
| `HF_API_TOKEN` | MedGemma vision model for imaging specialist (optional) |

The backend reads `.env` from the `backend/` directory via `pydantic-settings`. All settings are in `backend/config.py`.

## Architecture

MediCascade is a **4-layer cascade pipeline** exposed as a FastAPI backend (`backend/main.py`) with a React/Vite frontend (`frontend/`). The Vite dev server proxies `/api` and `/outputs` to `localhost:8000`.

### API Endpoints
- `POST /api/diagnose` — main clinical pipeline: accepts a patient PDF (+ optional scan image). Response includes `icd10_code`, `icd10_description`, `drug_safety`.
- `POST /api/mri/analyze` — 4-modality NIfTI segmentation (T1/T1CE/T2/FLAIR → PyTorch UNet3D)
- `POST /api/mri/analyze-3d` — 3D mesh generation from FLAIR + segmentation NIfTI files
- `GET /api/report/{case_id}` — download generated PDF report
- `GET /api/case/{case_id}` — retrieve structured case JSON
- `GET /api/history` — paginated list of all processed cases (`?limit=20&offset=0`)
- `GET /api/stats` — aggregate stats: total cases, avg confidence, top diagnoses
- `POST /api/feedback/{case_id}` — clinician feedback (`?rating=1-5&comment=...`)
- `GET /api/fhir/{case_id}` — FHIR R4 DiagnosticReport export (EHR integration)

### Pipeline Layers

**Layer 0** (`layers/layer0_pdf_processor.py`): Deterministic intake — no AI. Extracts text/tables/images from PDFs using pdfplumber + Tesseract OCR, classifies sections with heuristics, builds a structured `CaseDocument` with `CaseFacts` and provenance, saves `case.json` to `outputs/cases/{case_id}/`.

**Layer 1** (`layers/layer1_specialists.py`): 5–6 specialist agents run in parallel via `ThreadPoolExecutor`. Each agent calls Groq (llama-3.3-70b) with a domain-specific JSON prompt. Agents: `notes`, `labs`, `medication`, `history_genetics`, `exposure`, `imaging` (MedGemma via HF, only if images exist). Results merge into `Layer1Findings` with `candidate_diagnoses`, `red_flags`, `abnormal_labs`, `symptom_timeline`, `risk_factors`.

**Layer 2** (`layers/layer2_validator.py`): Evidence validation using OpenRouter (qwen-2.5-72b, hardcoded — env override is ignored). Falls back to Groq, then heuristics. Classifies Layer 1 findings into `supported`/`uncertain`/`contradicted`, retrieves evidence snippets.

**Layer 3** (`layers/layer3_annotator.py`): Generates the final doctor-facing PDF report using ReportLab + Groq for XAI narrative. Annotates critical values and highlights.

### Data Models (`backend/schemas.py`)

Key Pydantic models in pipeline order:
- `CaseDocument` → `CaseFacts` (demographics, labs, vitals, meds, history, images)
- `Layer0Result` → wraps `CaseDocument` + legacy `PatientData` compatibility bridge
- `Layer1Findings` → list of `SpecialistView` objects + aggregated contract fields
- `FinalAssessment` → Layer 2 output with evidence pack and highlight targets
- `AnnotatedReport` → Layer 3 output with PDF path and XAI explanation

### MRI 3D Subsystem (`backend/mri/`)

Separate subsystem for brain tumor segmentation:
- `unet3d.py` — PyTorch 3D UNet architecture
- `predict.py` — inference wrapper using `backend/kagglemodel/best_model.pth`
- `preprocess.py` — NIfTI normalization and skull stripping (hd-bet optional via `MRI_USE_HDBET`)
- `mesh_export.py` — marching cubes mesh generation for tumor regions

Mesh generation for the `/api/mri/analyze-3d` endpoint is implemented directly in `main.py` (not via the mri module) and includes Laplacian smoothing.

### Frontend Components (`frontend/src/components/`)

- `UploadSection.jsx` — PDF + scan file upload
- `CascadePipeline.jsx` — animated pipeline progress visualization
- `ResultsDashboard.jsx` — renders diagnosis, evidence, specialist views
- `MriTumorView.jsx` — 2D slice viewer for MRI results
- `Brain3DViewer.jsx` — Three.js/react-three-fiber 3D mesh viewer
- `AIDebugView.jsx` — raw layer output inspector

### Output Storage

All generated artifacts are stored under `outputs/`:
- `outputs/cases/{case_id}/case.json` — structured case facts
- `outputs/cases/{case_id}/layer1_findings.json` — specialist outputs
- `outputs/cases/{case_id}/MediCascade_Report_{case_id}.pdf` — final annotated report
- `outputs/meshes/` — 3D mesh data for MRI analysis

Static files under `outputs/` are served by FastAPI's `StaticFiles` mount at `/outputs`.

### New Utilities (`backend/utils/` — added for societal impact)

- `pubmed_client.py` — Real PubMed abstract fetching via NIH eUtils (free, no key). Used by Layer 2 to replace placeholder links with genuine evidence snippets. In-process cache prevents duplicate NIH calls.
- `drug_checker.py` — FDA OpenFDA drug label lookup (free, no key). Called by the Layer 1 medication agent to add boxed warnings, interactions, and contraindications from the FDA database.
- `icd_mapper.py` — Local ICD-10-CM lookup table covering ~100 common diagnoses. Performs exact → partial → keyword matching. Used in Layer 3 and `/api/diagnose` response.

### Database (`backend/database.py`)

SQLite persistence (no external service). Initialised at startup via `init_db()`. Tables: `cases` (every processed case with ICD-10 code, confidence, drug warnings), `feedback` (clinician ratings 1-5), `audit_log`.

### Utilities (`backend/utils/`)

- `pdf_extractor.py` — smart PDF extraction (text-first, falls back to image OCR)
- `data_classifier.py` — section classification and lab/patient info extraction
- `hf_client.py` — HuggingFace Inference API client for MedGemma
- `pdf_annotator.py` — ReportLab-based annotated PDF generation
- `image_annotator.py` — OpenCV-based scan annotation with highlights
- `critical_annotator.py` — critical value detection and markup
