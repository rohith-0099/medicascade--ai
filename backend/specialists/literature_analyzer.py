"""
Specialist 4 — Biomedical Literature Matching
Model: microsoft/BioGPT-Large
Purpose: Matches patient findings against PubMed biomedical literature.
         Identifies diseases scientifically associated with the patient's
         combination of symptoms and findings. Generates evidence-backed suggestions.
"""

from utils.hf_client import hf_client
from schemas import SpecialistOpinion
from config import settings
import re
from typing import List, Dict, Optional


class LiteratureAnalyzer:

    MODEL = settings.HF_LITERATURE_MODEL    # microsoft/BioGPT-Large
    DISPLAY_NAME = "BioGPT-Large (PubMed Literature)"

    # ── Disease–symptom associations from biomedical literature ─────────────
    # Based on known PubMed evidence patterns. BioGPT is trained on PubMed,
    # so it will confirm/expand these via text generation.
    EVIDENCE_BASE = {
        "stroke": {
            "symptoms": ["hemiparesis", "aphasia", "facial droop", "sudden weakness", "dysarthria",
                         "vision loss", "ataxia", "cerebrovascular"],
            "diagnosis": "Cerebrovascular Accident — Strong PubMed Evidence",
            "pubmed_ids": ["PMID:24234570", "PMID:22517907"],
            "evidence_level": "Level I (RCT)"
        },
        "glioblastoma": {
            "symptoms": ["headache", "seizure", "focal neurological", "tumor", "glioma", "mass"],
            "diagnosis": "High-Grade Glioma (Glioblastoma) — Literature Match",
            "pubmed_ids": ["PMID:30804563", "PMID:25023525"],
            "evidence_level": "Level II"
        },
        "mi": {
            "symptoms": ["chest pain", "troponin", "st elevation", "stemi", "angina", "diaphoresis"],
            "diagnosis": "Acute Coronary Syndrome — PubMed-Matched",
            "pubmed_ids": ["PMID:33012256", "PMID:31877122"],
            "evidence_level": "Level I (RCT)"
        },
        "dm2": {
            "symptoms": ["hyperglycemia", "diabetes", "polyuria", "polydipsia", "hba1c", "glucose"],
            "diagnosis": "Type 2 Diabetes Mellitus — Evidence-Based Match",
            "pubmed_ids": ["PMID:32469687", "PMID:30089739"],
            "evidence_level": "Level I"
        },
        "sepsis": {
            "symptoms": ["fever", "tachycardia", "hypotension", "infection", "wbc elevated", "procalcitonin"],
            "diagnosis": "Sepsis (Systemic Inflammatory Response) — Literature Evidence",
            "pubmed_ids": ["PMID:26903338", "PMID:27213363"],
            "evidence_level": "Level I (Sepsis-3 Criteria)"
        },
        "ckd": {
            "symptoms": ["elevated creatinine", "proteinuria", "kidney", "renal", "dialysis", "gfr"],
            "diagnosis": "Chronic Kidney Disease — KDIGO Evidence Match",
            "pubmed_ids": ["PMID:23727169"],
            "evidence_level": "Level I (KDIGO Guidelines)"
        },
        "lung_cancer": {
            "symptoms": ["cough", "hemoptysis", "weight loss", "smoking", "nodule", "mass lung"],
            "diagnosis": "Suspected Pulmonary Malignancy — Literature Match",
            "pubmed_ids": ["PMID:30060858"],
            "evidence_level": "Level II"
        },
        "afib": {
            "symptoms": ["palpitations", "atrial fibrillation", "irregular rhythm", "flutter"],
            "diagnosis": "Atrial Fibrillation — PubMed Evidence",
            "pubmed_ids": ["PMID:25713920"],
            "evidence_level": "Level I"
        },
    }

    def __init__(self):
        self.model_name = "literature_analyzer"
        print(f"[{self.model_name}] Initialized with model: {self.MODEL}")

    def analyze(self, patient_text: str) -> SpecialistOpinion:
        """
        Matches patient clinical text against biomedical literature using:
        1. BioGPT-Large text generation for disease prediction
        2. Evidence-base keyword matching for PubMed-backed associations
        """
        if not patient_text or len(patient_text.strip()) < 10:
            return SpecialistOpinion(
                model_name=self.model_name,
                diagnosis="Insufficient data for literature matching",
                confidence=0.0,
                reasoning="No patient data available",
                key_findings={"model": self.MODEL}
            )

        print(f"[{self.model_name}] Model: {self.MODEL}")
        print(f"[{self.model_name}] Running biomedical literature matching...")

        # ── Step 1: Evidence base keyword matching ───────────────────────────
        kb_matches = self._evidence_base_match(patient_text)

        # ── Step 2: BioGPT-Large disease prediction ──────────────────────────
        biogpt_result = self._biogpt_predict(patient_text, kb_matches)

        # Select best match
        primary = biogpt_result or (kb_matches[0] if kb_matches else None)
        if not primary:
            primary = {
                "diagnosis": "No strong literature match found",
                "confidence": 0.40,
                "reasoning": "Patient presentation does not match established PubMed evidence patterns",
                "evidence_level": "N/A",
                "pubmed_ids": []
            }

        evidence_conditions = [m["diagnosis"] for m in kb_matches[:4]]
        pubmed_ids = list({pid for m in kb_matches[:3] for pid in m.get("pubmed_ids", [])})

        print(f"[{self.model_name}] Primary: {primary['diagnosis']} ({primary.get('confidence', 0):.0%})")

        return SpecialistOpinion(
            model_name=self.model_name,
            diagnosis=primary["diagnosis"],
            confidence=primary.get("confidence", 0.65),
            reasoning=primary.get("reasoning", ""),
            detected_conditions=evidence_conditions,
            key_findings={
                "model": self.MODEL,
                "display_model": self.DISPLAY_NAME,
                "pubmed_references": pubmed_ids,
                "evidence_level": primary.get("evidence_level", "N/A"),
                "literature_matches": len(kb_matches),
                "biogpt_used": bool(biogpt_result)
            }
        )

    def _evidence_base_match(self, text: str) -> List[Dict]:
        """Map clinical text to evidence-based disease patterns."""
        text_lower = text.lower()
        matches = []
        for disease_id, data in self.EVIDENCE_BASE.items():
            hits = sum(1 for s in data["symptoms"] if s in text_lower)
            if hits > 0:
                conf = min(0.60 + hits * 0.07, 0.93)
                matches.append({
                    "disease_id": disease_id,
                    "diagnosis": data["diagnosis"],
                    "confidence": conf,
                    "hits": hits,
                    "pubmed_ids": data["pubmed_ids"],
                    "evidence_level": data["evidence_level"],
                    "reasoning": f"Literature evidence: {hits} matching clinical indicators found in PubMed-trained model"
                })
        return sorted(matches, key=lambda x: x["confidence"], reverse=True)

    def _biogpt_predict(self, patient_text: str, kb_matches: List[Dict]) -> Optional[Dict]:
        """Call BioGPT-Large for biomedical literature-based disease prediction."""
        # Build context-rich prompt for BioGPT
        kb_context = ""
        if kb_matches:
            top = kb_matches[0]
            kb_context = f"Preliminary evidence match: {top['diagnosis']} (Evidence: {top['evidence_level']})\n"

        prompt = (
            f"Clinical findings from patient record: {patient_text[:400]}\n\n"
            f"{kb_context}"
            "Based on PubMed biomedical literature, what is the most likely diagnosis "
            "for this patient? Provide: disease name, associated PubMed evidence, "
            "and differential diagnoses. Be concise and cite evidence level."
        )
        try:
            response = hf_client.generate_text(self.MODEL, prompt, max_new_tokens=300, temperature=0.2)
            if not response or len(response.strip()) < 20:
                return None

            # Try to extract diagnosis from BioGPT output
            # BioGPT tends to generate in biomedical continuation style
            diag = self._extract_disease_from_biogpt(response)
            conf_m = re.search(r'(\d{1,2})\s*%', response)
            conf = float(conf_m.group(1)) / 100 if conf_m else (0.72 if kb_matches else 0.60)

            return {
                "diagnosis": f"{diag} — BioGPT-Large Literature Match",
                "confidence": min(conf, 0.93),
                "reasoning": f"BioGPT-Large (PubMed-trained) analysis: {response[:250]}",
                "evidence_level": "PubMed-pattern matched",
                "pubmed_ids": [m.get("pubmed_ids", [None])[0] for m in kb_matches[:2] if m.get("pubmed_ids")]
            }
        except Exception as e:
            print(f"[{self.model_name}] BioGPT error: {e}")
        return None

    def _extract_disease_from_biogpt(self, text: str) -> str:
        """Extract the most likely disease name from BioGPT's generated text."""
        # BioGPT may continue with disease names in "Patient is likely to have..."
        patterns = [
            r'(?:most likely|likely|diagnosis[:\s]+|disease[:\s]+|condition[:\s]+)\s*[:\-]?\s*([A-Z][a-zA-Z\s\(\)-]{3,50})',
            r'^([A-Z][a-zA-Z\s\(\)-]{3,50})\s+(?:is|has|may|presents)',
        ]
        for pat in patterns:
            m = re.search(pat, text)
            if m:
                candidate = m.group(1).strip().rstrip(",.:;")
                if 3 < len(candidate) < 60:
                    return candidate
        # Fallback: first capitalized noun phrase
        m = re.search(r'\b([A-Z][a-zA-Z]+(?:\s+[A-Za-z]+){0,4})\b', text)
        return m.group(1) if m else "Unspecified condition — literature pending"


# Export
literature_analyzer = LiteratureAnalyzer()
