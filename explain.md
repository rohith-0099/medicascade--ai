# 🏥 MediCascade AI — Complete Project Explanation

> **For Faculty Presentation — Understanding the Entire Project**

---

## 1. What Is MediCascade AI?

MediCascade AI is an **AI-powered clinical decision support system** that processes patient medical PDF reports and produces an evidence-based diagnostic report. It mimics a real hospital diagnostic workflow using a **4-layer cascade pipeline**:

1. **Intake** → Extract data from the PDF  
2. **Specialist Consultation** → Multiple AI agents analyze the data in parallel  
3. **Evidence Validation** → Cross-check findings against real medical literature  
4. **Report Generation** → Produce a doctor-ready PDF report with explanations  

Additionally, it includes an **MRI Brain Tumor Segmentation** module that uses deep learning to detect and visualize brain tumors in 3D.

**Key Innovation**: Instead of a single "black-box" AI model, we use a **team of specialized AI agents** (like a panel of doctors) that independently analyze the same patient data and then cross-validate each other's findings — making the system transparent and explainable.

---

## 2. Problem Statement

Modern AI in healthcare suffers from the **"Black Box" problem**:
- AI models give a prediction (e.g., "Tumor Detected") but fail to explain **why** or **where**
- Doctors cannot trust a number without evidence
- Single models struggle to correlate **multimodal data** (text symptoms + visual scans + lab values)

**Our solution**: A transparent, multi-agent pipeline where every decision is traceable back to the source data (full **provenance**), and every finding is validated against published medical evidence from PubMed, NICE, and WHO.

---

## 3. High-Level Architecture

```
┌─────────────────────────────────────────────────────┐
│                FRONTEND (React + Vite)               │
│     Browser at http://localhost:5173                 │
│     UploadSection → CascadePipeline → Dashboard     │
│     MRI 3D Viewer (Plotly.js Mesh3d)                │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP (API calls)
┌──────────────────────▼──────────────────────────────┐
│              BACKEND (FastAPI + Python)               │
│     Server at http://localhost:8000                   │
│                                                      │
│  POST /api/diagnose → 4-Layer Cascade Pipeline       │
│  ┌──────────────────────────────────────────────┐   │
│  │ Layer 0: PDF Processor (No AI, deterministic)│   │
│  │   pdfplumber → extract text, tables, images  │   │
│  │   Regex classifiers → categorize sections    │   │
│  │   Output: case.json (structured facts)       │   │
│  ├──────────────────────────────────────────────┤   │
│  │ Layer 1: 7 Specialist AI Agents (parallel)   │   │
│  │   notes, labs, medication, history, risk,    │   │
│  │   exposure, imaging                          │   │
│  │   Groq API (LLaMA 3.3 70B) + FDA drug data  │   │
│  │   Output: layer1_findings.json               │   │
│  ├──────────────────────────────────────────────┤   │
│  │ Layer 2: Evidence Validator                   │   │
│  │   Groq → OpenRouter → heuristic fallback     │   │
│  │   + PubMed abstracts + ICD-10 coding         │   │
│  │   Output: final_assessment.json              │   │
│  ├──────────────────────────────────────────────┤   │
│  │ Layer 3: Report Builder + XAI Narrative       │   │
│  │   Groq LLM → doctor-facing explanation       │   │
│  │   ReportLab → annotated PDF report           │   │
│  │   Output: MediCascade_Report_{id}.pdf        │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  POST /api/mri/analyze → MRI Brain Segmentation      │
│  ┌──────────────────────────────────────────────┐   │
│  │ Upload 4 NIfTI files (T1, T1CE, T2, FLAIR)  │   │
│  │ nnU-Net v2 → segmentation mask               │   │
│  │ Marching cubes → 3D mesh for Plotly           │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  SQLite Database (cases, feedback, audit_log)        │
└──────────────────────────────────────────────────────┘
```

---

## 4. Technology Stack

### Backend (Python)

| Technology | Version | What It Does |
|:---|:---|:---|
| **Python** | 3.10+ | Programming language |
| **FastAPI** | 0.109.0 | Web framework for REST API |
| **Uvicorn** | 0.27.0 | ASGI server (runs FastAPI) |
| **Pydantic** | 2.5.3 | Data validation & schemas |
| **pydantic-settings** | 2.1.0 | Environment variable configuration |
| **SQLite3** | built-in | Database (no external setup needed) |
| **pdfplumber** | 0.10.3 | Extracts text and tables from PDFs |
| **PyPDF2** | 3.0.1 | Fallback PDF text extraction |
| **pytesseract** | 0.3.10 | OCR — reads text from scanned/image PDFs |
| **Tesseract** | system pkg | OCR engine (installed via apt) |
| **spaCy** | 3.7.4 | NLP — clinical named entity recognition |
| **Groq SDK** | 1.0.0 | Client for Groq LLM API (LLaMA models) |
| **ReportLab** | 4.0.9 | Generates the final annotated PDF report |
| **OpenCV** | 4.9.0 | Image annotation (highlights on scans) |
| **nibabel** | 5.2.1 | Reads NIfTI medical brain images |
| **scikit-image** | 0.25.0 | Marching cubes for 3D mesh generation |
| **scipy** | 1.12.0 | Gaussian filtering for mesh smoothing |
| **PyTorch** | (via nnunetv2) | Deep learning framework for MRI model |
| **nnU-Net v2** | latest | Pre-trained brain tumor segmentation model |

### Frontend (JavaScript)

| Technology | Version | What It Does |
|:---|:---|:---|
| **React** | 18.2.0 | UI component framework |
| **Vite** | 5.0.11 | Fast build tool & dev server |
| **TailwindCSS** | 3.4.1 | Utility-first CSS framework |
| **Plotly.js** | 3.4.0 | 3D mesh visualization (brain viewer) |
| **react-plotly.js** | 2.6.0 | React wrapper for Plotly |
| **Recharts** | 2.10.3 | Charts for statistics |
| **Axios** | 1.6.5 | HTTP client for API calls |

### AI Models Used (All Free Tier)

| Component | Model | Provider | Purpose |
|:---|:---|:---|:---|
| Notes specialist | llama-3.3-70b-versatile | Groq | Analyze clinical notes |
| Labs specialist | llama-3.3-70b-versatile | Groq | Interpret lab results |
| Medication specialist | llama-3.3-70b-versatile | Groq | Drug safety checks |
| History/Genetics | qwen3-32b | Groq | Comorbidities & inherited risk |
| Risk stratification | llama-3.3-70b-versatile | Groq | Risk scoring |
| Exposure specialist | llama-3.1-8b-instant | Groq | Environmental risk factors |
| Imaging specialist | llama-3.3-70b-versatile | Groq | Radiology interpretation (vision) |
| Layer 2 validator | llama-3.3-70b-versatile | Groq | Evidence validation (primary) |
| Layer 2 fallback | meta-llama/llama-3.3-70b | OpenRouter | Validation fallback |
| XAI narrative | llama-3.3-70b-versatile | Groq | Write doctor-facing explanation |
| Offline fallback | llama3.2 | Ollama (local) | Works without internet |
| Vision model | google/medgemma-4b-it | HuggingFace | Medical image analysis (optional) |
| MRI segmentation | nnU-Net v2 (BraTS 2021) | Local PyTorch | Brain tumor segmentation |

### External Data Sources (Free, No API Key Needed)

| Source | Purpose |
|:---|:---|
| **PubMed NIH eUtils** | Fetches real peer-reviewed medical article abstracts |
| **FDA OpenFDA** | Drug labels, boxed warnings, interactions |
| **ICD-10-CM** | Standard medical diagnosis codes (local lookup ~130 diagnoses) |

---

## 5. Complete File-by-File Explanation

### Root Directory

```
medicascade--ai/
├── CLAUDE.md             ← Developer guide (commands, architecture overview)
├── README.md             ← Project overview with screenshots
├── LICENSE               ← MIT license
├── setup.sh              ← Automated setup script (installs everything)
├── .gitignore            ← Git ignore rules
├── .env.example          ← Template for environment variables
```

- **`CLAUDE.md`** — Contains the full architecture documentation: all API endpoints, pipeline layers, data models, utilities, MRI subsystem, and database schema. Written as a developer reference.
- **`README.md`** — Public-facing project overview with problem statement, solution, tech stack, screenshots, and getting started instructions.
- **`setup.sh`** — Bash script that automates the entire setup: checks system dependencies (Tesseract, Ollama), installs Python and Node packages, pulls the LLM model, creates required directories.

---

### Backend — Core Files

#### `backend/main.py` — The API Server (440 lines)

This is the **entry point** of the entire backend. It:
- Creates a FastAPI application with CORS enabled
- Defines all API endpoints (10 total)
- Orchestrates the 4-layer cascade pipeline for `/api/diagnose`
- Handles MRI upload and segmentation for `/api/mri/analyze`
- Serves generated files (PDFs, JSONs) via static file mount

**Main flow in `/api/diagnose`**:
```python
# 1. Accept PDF upload + optional scan image
# 2. Layer 0 → Extract and structure the PDF data
layer0 = layer0_processor.process(upload_path, scan_path)

# 3. Layer 1 → Run 7 specialist agents in parallel
layer1 = layer1_specialists.process(layer0.case)

# 4. Layer 2 → Validate findings against evidence
layer2 = layer2_validator.process(layer0.case, layer1)

# 5. Layer 3 → Generate annotated PDF report
layer3 = layer3_annotator.process(layer0.case, layer1, layer2)

# 6. Map ICD-10 code, save to database, return response
```

**API Endpoints**:

| Method | Endpoint | What It Does |
|:---|:---|:---|
| `GET /` | Root — returns version info |
| `GET /health` | Health check — shows active models and storage paths |
| `POST /api/diagnose` | **Main pipeline** — upload PDF → get diagnosis |
| `POST /api/mri/analyze` | Upload 4 NIfTI brain scans → get 3D segmentation |
| `GET /api/report/{case_id}` | Download generated PDF report |
| `GET /api/case/{case_id}` | Get structured case data (JSON) |
| `GET /api/history` | Paginated list of all processed cases |
| `POST /api/feedback/{case_id}` | Submit clinician feedback (rating 1-5) |
| `GET /api/stats` | Aggregate statistics (total cases, avg confidence) |
| `GET /api/fhir/{case_id}` | Export case as FHIR R4 DiagnosticReport (for EHR systems) |

#### `backend/config.py` — Configuration (61 lines)

- Uses `pydantic-settings` to read environment variables from `backend/.env`
- Defines all configurable values: API keys, model names, storage paths, timeouts
- Creates required directories on import (`uploads/`, `outputs/`, `outputs/cases/`)

#### `backend/schemas.py` — Data Models (198 lines)

Defines all **Pydantic data structures** used throughout the pipeline:

- **`CaseDocument`** — The structured representation of a patient's medical record, with `CaseFacts` (demographics, labs, vitals, meds, history, images) and provenance tracking
- **`Layer0Result`** — Output of Layer 0 (case + compatibility bridge)
- **`SpecialistView`** — Single specialist agent's output (agent name, role, model, confidence, findings)
- **`Layer1Findings`** — Combined output of all specialists (candidate diagnoses, red flags, abnormal labs, symptom timeline, risk factors)
- **`FinalAssessment`** — Layer 2 output (primary diagnosis, confidence, supported/uncertain/contradicted findings, evidence pack, highlight targets)
- **`AnnotatedReport`** — Layer 3 output (PDF path, XAI explanation text, evidence items)
- **`MriAnalyzeResponse`** — MRI segmentation output (meshes, stats, volume shape)

#### `backend/database.py` — SQLite Database (158 lines)

- **No external database setup needed** — uses Python's built-in `sqlite3`
- Three tables: `cases`, `feedback`, `audit_log`
- Functions: `init_db()`, `save_case()`, `get_case()`, `get_case_history()`, `get_stats()`, `save_feedback()`
- Every processed case is stored with its diagnosis, confidence, ICD-10 code, processing time, and drug warnings

---

### Backend — Pipeline Layers

#### `backend/layers/layer0_pdf_processor.py` — Layer 0: Document Intake (312 lines)

**What it does**: Converts any hospital PDF into structured data. **No AI is used here** — it's entirely deterministic (regex + heuristics).

**How it works**:
1. Uses `pdfplumber` to extract text and tables from the PDF
2. Falls back to `Tesseract OCR` if the PDF is scanned/image-based
3. Classifies extracted text into sections: demographics, symptoms, lab results, clinical notes, medications, history
4. Extracts specific values with regex: blood pressure, heart rate, temperature, SpO2
5. Builds a `CaseDocument` with full **provenance** — every fact tracks which page and text span it came from
6. Saves everything as `case.json` in `outputs/cases/{case_id}/`

**Key concept — Provenance**: Every extracted fact records:
- `pdf_id` — which PDF it came from
- `page` — which page number
- `text_span` — the exact text that was used to derive the value

This allows Layer 3 to later highlight exactly where in the original PDF each finding came from.

#### `backend/layers/layer1_specialists.py` — Layer 1: Specialist Agents (843 lines)

**What it does**: Runs **7 independent AI specialist agents in parallel**, each analyzing the same patient data from a different clinical perspective — like a panel of doctors.

**The 7 specialists**:

| Agent | Role | What It Analyzes |
|:---|:---|:---|
| `notes` | Symptom timeline + impressions | Clinical notes, symptoms |
| `labs` | Lab interpretation | Blood work, metabolic panels |
| `medication` | Drug safety + interactions | Current medications, allergies + **FDA drug data** |
| `history_genetics` | Comorbidities + inherited risk | Medical history, family history |
| `risk` | Risk stratification | Overall risk profile (cardiovascular, metabolic, renal, oncologic) |
| `exposure` | Environmental/occupational risks | Work/environment exposures |
| `imaging` | Radiology interpretation | Medical scan images (if provided) |

**How it works**:
1. All agents run **in parallel** using Python's `ThreadPoolExecutor` (faster than sequential)
2. Each agent sends the relevant patient data to a Groq LLM with a specialized prompt
3. The LLM returns structured JSON (e.g., `{abnormal_labs: [...], patterns: [...]}`)
4. The medication agent additionally calls the **FDA OpenFDA API** to get real boxed warnings and drug interactions
5. Results are aggregated into `Layer1Findings` with: candidate diagnoses, red flags, abnormal labs, symptom timeline, risk factors
6. Saved as `layer1_findings.json`

**Fallback strategy**: Groq API → Ollama local LLM → deterministic heuristics (always works, even offline)

#### `backend/layers/layer2_validator.py` — Layer 2: Evidence Validation (699 lines)

**What it does**: Acts as a "truth checker." Takes the specialist findings and validates them against external evidence sources.

**How it works**:
1. **Evidence retrieval**: For the top candidate diagnoses, it:
   - Fetches **real PubMed abstracts** via NIH eUtils (free API, ~3 req/sec)
   - Generates links to **NICE** (UK clinical guidelines) and **WHO** publications
2. **Validator LLM call**: Sends the case facts + Layer 1 findings + retrieved evidence to an LLM, asking it to classify each finding as:
   - ✅ **Supported** — evidence confirms this finding
   - ❓ **Uncertain** — not enough evidence
   - ❌ **Contradicted** — evidence disagrees
3. **Deterministic safety guards**: Even if the LLM fails, rule-based logic checks critical lab values (HbA1c ≥ 10%, troponin > 0.04, eGFR < 60, etc.) and ensures they're always flagged
4. **ICD-10 coding**: Maps the diagnosis to a standard ICD-10-CM code
5. Saved as `final_assessment.json`

**Fallback chain**: Groq LLM → OpenRouter free model → deterministic heuristics

#### `backend/layers/layer3_annotator.py` — Layer 3: Report Generation (360 lines)

**What it does**: Generates the final doctor-facing PDF report with XAI (Explainable AI) narrative.

**How it works**:
1. **XAI Narrative**: Sends the final assessment to Groq LLM, asking it to write a structured explanation:
   - Clinical summary
   - Why the primary diagnosis is most likely
   - Differential reasoning
   - Red-flag interpretation
   - Evidence grounding (with PubMed source names)
   - Uncertainty and missing data
   - Recommended next tests/actions
2. **PDF Generation**: Uses ReportLab to build a professional annotated PDF containing:
   - Patient summary (demographics, vitals)
   - Urgent red flags
   - Primary diagnosis with confidence score + ICD-10 code
   - Differential diagnoses with ICD codes
   - FDA drug safety warnings
   - Evidence links (PubMed, NICE, WHO)
   - Layer 1 and Layer 2 findings
   - XAI reasoning narrative
   - Critical value highlights (linked back to source PDF pages)
   - Data flow trace showing the full pipeline
3. Saved as `MediCascade_Report_{case_id}.pdf`

---

### Backend — Utilities (`backend/utils/`)

| File | Lines | What It Does |
|:---|:---|:---|
| `pdf_extractor.py` | ~190 | Smart PDF extraction: tries text-first with pdfplumber, falls back to image-based OCR with pytesseract. Extracts embedded images from PDFs. |
| `data_classifier.py` | ~150 | Classifies extracted text into medical sections (demographics, symptoms, labs, notes, etc.) using regex pattern matching. Extracts patient info (name, age, gender) and lab values. |
| `drug_checker.py` | ~110 | Queries **FDA OpenFDA API** (free, no key needed) for drug label data. Returns boxed warnings, drug-drug interactions, and contraindications for given medication names. |
| `pubmed_client.py` | ~100 | Fetches **real PubMed abstracts** via NIH eUtils API (free, 3 req/sec). Searches by diagnosis term, returns article title, journal, year, PMID, URL, and abstract snippet. Uses in-process caching. |
| `icd_mapper.py` | ~320 | Local ICD-10-CM lookup table covering ~130 common diagnoses. Performs exact → partial → keyword matching. Maps diagnoses like "Type 2 Diabetes" to "E11.65". |
| `pdf_annotator.py` | ~520 | ReportLab-based PDF generation engine. Builds the multi-section annotated diagnostic report with tables, color coding, evidence links, and professional formatting. |
| `critical_annotator.py` | ~420 | Critical value detection and markup. Identifies dangerously abnormal lab values and annotates them with red highlights in the report. |
| `image_annotator.py` | ~120 | OpenCV-based scan annotation. Draws highlights and circles on medical scan images to visually mark areas of concern. |
| `hf_client.py` | ~310 | HuggingFace Inference API client. Used to call MedGemma (Google's medical vision model) for image analysis. Optional — only used when HF_API_TOKEN is configured. |

---

### Backend — MRI 3D Brain Tumor Segmentation (`backend/mri/`)

This is a **separate subsystem** for brain tumor detection and 3D visualization.

#### `backend/mri/predictor.py` — nnU-Net Predictor (193 lines)

- Wraps the **nnU-Net v2** framework — a self-configuring medical image segmentation model
- Uses pre-trained weights from the **BraTS 2021 Challenge** (brain tumor segmentation competition)
- Model size: 1.1 GB (5 folds × ~220MB each, but only uses 1 fold for speed)
- **Singleton pattern** with thread-safe locking — model loads once and is reused
- Auto-extracts the model ZIP file on first use

**Input**: 4 MRI modalities as 3D numpy arrays (T1, T1CE, T2, FLAIR)  
**Output**: Segmentation mask with labels:
- `0` = background
- `1` = peritumoral edema
- `2` = necrotic tumor core  
- `4` = enhancing tumor

**Performance optimizations** (for consumer GPU like RTX 3050, 4GB):
- Uses **single fold** instead of 5-fold ensemble → 5× speedup
- **Disabled test-time mirroring** (8 orientations → 1) → 8× speedup
- Net effect: ~40× fewer forward passes, inference time ~1-2 minutes (was 10-15 minutes)

#### `backend/mri/mesh_generator.py` — 3D Mesh Generation (241 lines)

Converts the segmentation mask into 3D mesh data that can be rendered in the browser:

1. **Brain surface**: Marching cubes on raw FLAIR volume (downsampled 2×, Gaussian smooth σ=1.5)
2. **Tumor surfaces**: Marching cubes on binary masks per tumor label (Gaussian smooth σ=1.2)
3. **Laplacian smoothing** — makes surfaces look organic (brain: 15 iterations, tumors: 8)
4. **Face decimation** — limits polygon count for browser performance (brain: max 60K faces, tumors: max 50K)
5. Outputs Plotly Mesh3d format: `{x, y, z, i, j, k, vertex_count, face_count}`

---

### Frontend (`frontend/src/`)

#### `frontend/src/App.jsx` — Main Application (30K+ lines)

- **Single-page application** with sidebar navigation
- Two view modes: **Clinical** (PDF diagnosis) and **MRI** (3D brain viewer)
- Orchestrates the entire user workflow: upload → loading → results display
- 14-stage animated thinking log simulates real pipeline progress during processing
- Pipeline progress bar showing 4 layers (L0 → L1 → L2 → L3)
- Case history sidebar with statistics

#### `frontend/src/components/`

| Component | What It Does |
|:---|:---|
| **`UploadSection.jsx`** | Drag-and-drop PDF upload + optional scan image upload. Validates file types. |
| **`CascadePipeline.jsx`** | Animated pipeline progress visualization showing each layer processing in sequence with status indicators. |
| **`LoadingProgress.jsx`** | Rich loading states with animated thinking messages, simulating the pipeline stages. |
| **`ResultsDashboard.jsx`** | Renders the complete diagnosis results: primary diagnosis with confidence, differential diagnoses, evidence items, specialist views, red flags, abnormal labs, and drug safety information. |
| **`MriTumorView.jsx`** | Full 3D brain tumor viewer using Plotly Mesh3d. Upload 4 NIfTI files, renders brain + 3 tumor types as toggleable mesh layers with adjustable opacity. Shows volume statistics. |
| **`AIDebugView.jsx`** | Raw layer output inspector — shows the JSON data from each pipeline layer for debugging and transparency. |

#### `frontend/src/index.css` — Global Styles (21K+ lines)

- Deep black background (`#050b18`) with cyan grid pattern
- Cyan neon accent (`#00d4ff`) + purple secondary (`#7c3aed`)
- Premium fonts: Space Grotesk (headings) + JetBrains Mono (code/labels)
- Dark glassmorphic cards (semi-transparent backgrounds)
- Smooth animations and hover effects

#### Build Optimization
- Plotly.js (4.8MB) is split into a separate lazy chunk — main bundle is only 159KB
- MriTumorView is lazy-loaded via `React.lazy()` — only loads when user navigates to MRI view

---

### Synthetic Data Generator (`synthetic_data/`)

#### `synthetic_data/generate_synthetic_data.py` — Test Data Generator (580 lines)

Generates **5 realistic patient PDF records** for testing the pipeline:

| Case # | Condition | Key Data |
|:---|:---|:---|
| 1 | Type 2 Diabetes | HbA1c 8.7%, fasting glucose 214 mg/dL |
| 2 | Acute Myocardial Infarction (STEMI) | Troponin 8.42 ng/mL, ST elevation on ECG |
| 3 | Glioblastoma (Brain Tumor) | 4.8 cm mass, 7mm midline shift |
| 4 | Chronic Kidney Disease Stage 3b | eGFR 31, creatinine 2.8 |
| 5 | Community-Acquired Pneumonia | WBC 18,400, CRP 142, chest X-ray consolidation |

Uses ReportLab to create professional-looking PDFs with hospital headers, patient info tables, lab results with abnormal flags, clinical notes, and preliminary diagnoses.

---

### Other Important Files

#### `claude-updates/updates.md` — Detailed Development Log (625 lines)

Complete project documentation including:
- Full architecture diagram
- All API endpoint details with response shapes
- Data model specifications
- AI models used with providers
- MRI subsystem documentation
- Database schema
- Environment variables
- All changes made during development
- Key design decisions

#### `backend/.env.example` — Environment Variable Template

```bash
GROQ_API_KEY=           # Free at console.groq.com (required)
OPENROUTER_API_KEY=     # Free at openrouter.ai (fallback validator)
HF_API_TOKEN=           # Free at huggingface.co (optional, for MedGemma vision)
```

---

## 6. How the Complete Pipeline Works (Step by Step)

### Step 1: User Uploads a Patient PDF

The user opens the web UI at `http://localhost:5173`, drags a patient PDF report onto the upload area, and optionally attaches a scan image (X-Ray, CT, MRI). They click "Analyze."

### Step 2: Layer 0 — Document Intake (No AI)

1. `pdfplumber` extracts all text and tables from the PDF
2. If the PDF is scanned/image-based, `pytesseract` (Tesseract OCR) converts images to text
3. Regex-based classifiers categorize the text into sections: demographics, lab results, symptoms, clinical notes, medications, history
4. Vital signs (BP, HR, Temperature, SpO2) are extracted with specific regex patterns
5. A unique `case_id` is generated
6. Everything is structured into a `CaseDocument` and saved as `case.json`

**Output**: `outputs/cases/{case_id}/case.json` — structured facts with provenance

### Step 3: Layer 1 — Specialist Agents (AI + FDA)

7 specialist agents run **simultaneously** using `ThreadPoolExecutor`:

1. **Notes agent**: Reads clinical notes → extracts symptom timeline, exam findings, impressions
2. **Labs agent**: Reads lab results → identifies abnormal values, patterns, risk flags
3. **Medication agent**: Reads medications → checks interactions + queries FDA OpenFDA for real boxed warnings
4. **History agent**: Reads medical history → identifies comorbidities, family history, inherited risks
5. **Risk agent**: Reads full text → stratifies cardiovascular, metabolic, renal, oncologic risk
6. **Exposure agent**: Reads full text → identifies occupational/environmental risk factors
7. **Imaging agent** (if images exist): Sends scan to Groq Vision → radiology findings

Each agent sends its data to a Groq LLM (LLaMA 3.3 70B) with a domain-specific prompt asking for structured JSON output.

Results are merged into the **Layer 1 contract**: candidate diagnoses (ranked by confidence), red flags, abnormal labs, symptom timeline, risk factors.

**Output**: `outputs/cases/{case_id}/layer1_findings.json`

### Step 4: Layer 2 — Evidence Validation (AI + PubMed + FDA)

1. For the top candidate diagnoses, fetches **real PubMed abstracts** via NIH eUtils API
2. Generates links to NICE guidelines and WHO publications
3. Sends all of this (case facts + Layer 1 findings + retrieved evidence) to a validator LLM
4. The LLM classifies each finding as `supported`, `uncertain`, or `contradicted`
5. **Deterministic safety guards** always run (regardless of LLM success):
   - Checks critical thresholds (HbA1c ≥ 10%, troponin > 0.04, eGFR < 60, etc.)
   - Ensures the correct diagnosis and confidence are never dropped
6. Maps the diagnosis to a standard **ICD-10-CM code** using local lookup

**Output**: `outputs/cases/{case_id}/final_assessment.json`

### Step 5: Layer 3 — Report Generation (AI + ReportLab)

1. Sends the final assessment to Groq LLM for a structured **XAI narrative** (7 sections: clinical summary, diagnosis reasoning, differentials, red flags, evidence, uncertainty, next steps)
2. Collects FDA drug safety warnings from the medication specialist
3. Uses **ReportLab** to generate a professional annotated PDF:
   - Patient demographics and vitals
   - Urgent red flags (highlighted in red)
   - Primary diagnosis with confidence score and ICD-10 code
   - Differential diagnoses with reasoning
   - FDA drug safety warnings
   - Evidence links (PubMed articles with real abstracts)
   - XAI explanation narrative
   - Critical value highlights traced to source PDF pages
   - Complete data flow trace

**Output**: `outputs/cases/{case_id}/MediCascade_Report_{case_id}.pdf`

### Step 6: Results Displayed in Browser

The frontend receives the full response JSON and renders:
- Primary diagnosis with confidence meter
- Specialist agent views (7 cards)
- Evidence items with source links
- Differential diagnoses
- Red flags and abnormal labs
- Drug safety warnings
- Download link for the full PDF report

---

## 7. How the MRI 3D Pipeline Works

### Step 1: User Uploads 4 NIfTI Brain Scans

In the MRI view, the user uploads 4 files:
- **T1** — structural anatomy
- **T1CE** — contrast-enhanced (highlights tumor)
- **T2** — fluid-sensitive
- **FLAIR** — suppresses CSF, shows edema

### Step 2: nnU-Net Segmentation

1. All 4 volumes are loaded with `nibabel` and validated (must be 3D, same shape)
2. Stacked into a 4-channel array: `(4, D, H, W)`
3. Fed into the **nnU-Net v2** pre-trained model (BraTS 2021 weights)
4. Model outputs a segmentation mask labeling each voxel as: background, edema, necrotic core, or enhancing tumor

### Step 3: 3D Mesh Generation

1. **Brain mesh**: Marching cubes on the raw FLAIR volume → downsampled → Gaussian smooth → Laplacian smooth → decimated
2. **Tumor meshes** (3 types): Marching cubes on smoothed binary masks → Laplacian smooth → decimated
3. All meshes converted to Plotly format: vertex coordinates (x,y,z) + triangle face indices (i,j,k)

### Step 4: 3D Visualization in Browser

The frontend receives the mesh data and renders it with **react-plotly.js**:
- Semi-transparent brain surface
- Color-coded tumor regions (red = necrotic, yellow = edema, purple = enhancing)
- Toggle each layer on/off
- Adjustable brain opacity (0-100%)
- Volume statistics in cm³

---

## 8. Database Design

```sql
-- Every processed case
CREATE TABLE cases (
    case_id            TEXT PRIMARY KEY,
    source_pdf         TEXT,
    ingested_at        TEXT,
    primary_diagnosis  TEXT,
    icd10_code         TEXT,        -- Standard medical code (e.g., "E11.65")
    icd10_description  TEXT,
    confidence         REAL,        -- 0.0 to 1.0
    processing_time    REAL,        -- seconds
    pdf_path           TEXT,        -- path to generated report PDF
    layer1_json        TEXT,        -- JSON string of specialist findings
    layer2_json        TEXT,        -- JSON string of validated assessment
    drug_warnings      TEXT,        -- JSON array of FDA warnings
    created_at         TEXT
);

-- Clinician feedback
CREATE TABLE feedback (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id    TEXT NOT NULL,
    rating     INTEGER CHECK(rating BETWEEN 1 AND 5),
    comment    TEXT,
    created_at TEXT
);

-- Audit trail
CREATE TABLE audit_log (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id    TEXT,
    event      TEXT,        -- "case_saved", "feedback_submitted"
    detail     TEXT,
    created_at TEXT
);
```

---

## 9. Key Design Decisions (Good Talking Points for Presentation)

1. **Multi-agent architecture** — Instead of one model, we use 7 specialist agents like a panel of doctors. This provides better accuracy through diverse perspectives and built-in cross-validation.

2. **Full provenance tracking** — Every extracted fact records its source page and text span. This makes the system **auditable** — a doctor can always trace a finding back to the original PDF.

3. **Deterministic fallbacks at every layer** — If all APIs fail (no internet, rate limits), rule-based heuristic logic still produces a diagnosis. The system **never crashes or returns empty results**.

4. **100% free-tier APIs** — Groq, OpenRouter, PubMed NIH eUtils, and FDA OpenFDA all have free tiers. No paid subscriptions needed.

5. **Real evidence, not hallucinations** — Layer 2 fetches actual PubMed abstracts (not generated text) and real FDA drug warnings. Evidence is traceable and verifiable.

6. **XAI (Explainable AI)** — Layer 3 generates a structured explanation of why the diagnosis was chosen, what evidence supports it, and what's uncertain. Solves the "black box" problem.

7. **ICD-10 coding** — Maps diagnoses to international standard medical codes, enabling integration with EHR (Electronic Health Record) systems.

8. **FHIR R4 export** — The `/api/fhir/{case_id}` endpoint exports cases in FHIR format — the international standard for health data exchange, used by Epic, Cerner, and other hospital systems.

9. **No external database** — SQLite requires zero setup. Good for a research prototype/hackathon.

10. **Consumer GPU optimization** — The MRI model uses single-fold inference and no mirroring, giving a 40× speedup to run on a laptop GPU.

---

## 10. How to Run the Project

### Prerequisites
- Python 3.10+
- Node.js & npm
- Tesseract OCR (`sudo apt install tesseract-ocr poppler-utils`)
- A Groq API key (free at [console.groq.com](https://console.groq.com))

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
cp .env.example .env   # Edit and add your GROQ_API_KEY
uvicorn main:app --reload --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev   # Opens at http://localhost:5173
```

### Generate Test Data
```bash
cd synthetic_data
python generate_synthetic_data.py   # Creates 5 sample patient PDFs
```

### MRI Model Setup
Download the nnU-Net model (1.1 GB) from [Zenodo](https://zenodo.org/records/11582627) and place it at `backend/nnunet_model/Dataset002_BRATS19.zip`. It auto-extracts on first use.

---

## 11. Societal Impact & Use Cases

1. **Rural Healthcare**: Enables preliminary diagnostic support in areas without specialist doctors
2. **Emergency Triage**: Quickly identifies critical conditions (STEMI, brain tumors) that need immediate intervention
3. **Medical Education**: Serves as a teaching tool for understanding multi-modal diagnostic reasoning
4. **Drug Safety**: Automatically checks FDA databases for boxed warnings and dangerous drug interactions
5. **Transparency**: Unlike black-box AI, every decision can be traced and explained — building trust with clinicians
6. **Standards Compliance**: FHIR R4 export enables integration with existing hospital information systems

---

## 12. Quick Summary for Presentation

> **One-liner**: MediCascade AI is a multi-agent clinical decision support system that processes patient PDFs through 4 AI layers (intake → specialist consultation → evidence validation → report generation) to produce transparent, evidence-based diagnostic reports with real PubMed citations, ICD-10 codes, and FDA drug safety checks — solving the "black box" problem in medical AI.

**Key numbers to mention**:
- 4 pipeline layers
- 7 specialist AI agents running in parallel
- 10 API endpoints
- 3 external evidence sources (PubMed, FDA, NICE/WHO)
- ~130 ICD-10-CM diagnoses supported
- 5 synthetic test cases included
- 100% free-tier APIs
- Works offline with Ollama fallback
