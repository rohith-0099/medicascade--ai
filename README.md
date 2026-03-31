# MediCascade AI
> "From Black-Box to Glass-Box" - a multi-layer clinical decision support pipeline for transparent, evidence-backed medical AI outputs.

## Overview
MediCascade AI processes a patient PDF through four layers:

1. Layer 0 intake extracts structured facts, provenance, and embedded images.
2. Layer 1 runs 7 specialist agents in parallel.
3. Layer 2 validates the candidate diagnoses against external evidence.
4. Layer 3 generates a clinician-facing report with explanations, ICD-10 coding, and safety notes.

The goal is not to hide uncertainty. The system now explicitly reports when a capability is unavailable, when deterministic fallbacks were used, and where manual review is still required.

## Layer Breakdown

### Layer 0 - Multimodal Intake
- PDF extraction for notes, labs, vitals, medications, history, and embedded images
- Provenance tracking for auditable downstream highlights

### Layer 1 - Specialist Agents
The system has 7 specialist agents:

| Agent | Purpose | Runtime / Model |
| :--- | :--- | :--- |
| `notes` | Symptom timeline and clinician impressions | Groq text model with OpenRouter/Ollama/deterministic fallback |
| `labs` | Abnormal lab interpretation and patterns | Groq text model with OpenRouter/Ollama/deterministic fallback |
| `medication` | Medication extraction, allergies, FDA safety checks | Groq text model + OpenFDA safety enrichment |
| `history_genetics` | Comorbidities, family history, inherited risk | Groq/OpenRouter/Ollama/deterministic fallback |
| `risk` | Risk stratification and prognosis | Groq/OpenRouter/Ollama/deterministic fallback |
| `exposure` | Occupational and environmental exposures | Groq/OpenRouter/Ollama/deterministic fallback |
| `imaging` | Radiology-style scan review | Requires `HF_API_TOKEN` for actual image analysis. Falls back to text-only mode without it. |

### Layer 2 - Evidence Validator
- Consolidates the 7 agent outputs
- Retrieves lightweight evidence from PubMed, NICE, and WHO
- Falls back deterministically if external model providers are unavailable

### Layer 3 - Explainable Report
- Annotated PDF report
- ICD-10 mapping with manual-review disclaimer when unmatched
- FDA drug safety section when medication warnings are available

## Technology Stack

| Component | Tech Choices |
| :--- | :--- |
| Backend | Python 3.10+ (developed and tested on Python 3.12), FastAPI, Uvicorn |
| Frontend | React, Vite, TailwindCSS |
| LLM Providers | Groq, OpenRouter, Ollama |
| Vision Model | Hugging Face MedGemma (`google/medgemma-4b-it`) |
| PDF / Reporting | PyPDF2, pdfplumber, ReportLab |
| MRI | nnU-Net v2, nibabel, scikit-image, PyTorch |

## Getting Started

### Prerequisites
- Node.js and npm
- Python 3.10+ (developed and tested on Python 3.12)
- Tesseract OCR (`sudo apt install tesseract-ocr poppler-utils`)
- Optional: Groq/OpenRouter API keys for online model access
- Optional: `HF_API_TOKEN` for actual imaging analysis with MedGemma
- Optional: Ollama for local fallback

### Installation
```bash
git clone https://github.com/your-username/medicascade-ai.git
cd medicascade-ai

cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

cd ../frontend
npm install
```

### Run the App
```bash
cd backend
./venv/bin/uvicorn main:app --reload
```

```bash
cd frontend
npm run dev
```

Open `http://localhost:5173`.

## Offline Fallback
Ollama fallback requires manual installation: https://ollama.ai - run `ollama pull llama3.2` before going offline. Without Ollama, the system uses built-in deterministic heuristics as final fallback and will never return empty results.

## MRI Performance
The MRI path uses single-fold inference with mirroring disabled. This is a theoretical ~40x fewer forward passes vs full 5-fold + 8-orientation ensemble. Actual inference time varies by hardware (typically 1-5 minutes on consumer GPU, 5-15 minutes on CPU).

## Limitations
- Local ICD-10 lookup covers ~130 common diagnoses. Uncommon conditions return `Z03.89` (unclassified) and require manual coding.
- Imaging agent requires `HF_API_TOKEN` for actual vision analysis.
- Ollama fallback requires manual installation and model download.
- FDA rate limit is 40 requests/minute; the backend now throttles and retries under parallel load.
- MRI speedup claims are theoretical; actual time depends on hardware.
- FHIR export is JSON-formatted and not schema-validated.

See [KNOWN_LIMITATIONS.md](KNOWN_LIMITATIONS.md) for the concise project limitations list.

## Disclaimer
This project is a research prototype and not a certified medical device. Always require clinician review before using any output for diagnosis or treatment decisions.
