# Layer 1 AI Model Configuration

## Specialist → AI Model Mapping

### 1. Symptom Analyzer
**Model:** `emilyalsentzer/Bio_ClinicalBERT` ✅ WORKING
- Most popular ClinicalBERT implementation
- Trained on clinical notes and MIMIC-III data
- Best for symptom-to-diagnosis mapping
- URL: https://huggingface.co/emilyalsentzer/Bio_ClinicalBERT

### 2. Lab Analyzer
**Model:** `dmis-lab/biobert-base-cased-v1.1`
- BioBERT - specialized for biomedical text
- Interprets lab values and medical terminology
- URL: https://huggingface.co/dmis-lab/biobert-base-cased-v1.1

### 3. Notes Analyzer
**Model:** `google/flan-t5-base`
- FLAN-T5 - excellent for medical reasoning
- Extracts clinical information from notes
- URL: https://huggingface.co/google/flan-t5-base

### 4. Risk Analyzer
**Model:** `distilbert/distilbert-base-uncased`
- Fast and efficient risk classification
- Analyzes patient demographics and history
- URL: https://huggingface.co/distilbert/distilbert-base-uncased

### 5. Scan Analyzer
**Model:** `microsoft/BiomedCLIP-PubMedBERT_256-vit_base_patch16_224`
- BiomedCLIP - vision + language model
- Analyzes medical images with clinical context
- URL: https://huggingface.co/microsoft/BiomedCLIP-PubMedBERT_256-vit_base_patch16_224
- **Backup:** MedSAM (OpenCV-based detection)

---

## Layer 3: Explainable AI (XAI)

**XAI Model:** Ollama `llama3.2:latest` (local, free)
- **Purpose:** Generate transparent clinical reasoning explanations
- **Technique:** Chain-of-thought reasoning

**XAI Features:**
1. **5-Step Clinical Reasoning Chain:**
   - Key findings identified
   - Diagnostic logic explanation
   - Supporting evidence analysis
   - Differential diagnosis reasoning
   - Confidence level justification

2. **Evidence-based explanations** showing which findings led to diagnosis
3. **Feature importance** highlighting critical data points  
4. **Alternative diagnoses** with reasoning for ruling them out
5. **Transparent AI decision-making** for clinical validation

**Fallback:** Enhanced template-based explanations (instant)

## Architecture
**Layer 1:** 5 different medical AI models run in parallel
**Layer 2:** Cross-validates using weighted voting
**Layer 3:** Generates doctor-readable reports

All models are **specialized for medical data** - not generic AI!
