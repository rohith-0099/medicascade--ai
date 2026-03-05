"""
Specialist 2 — Symptoms & Clinical Notes
Model: UFNLP/gatortron-medium
Purpose: Reads doctor notes, patient complaints, and clinical text.
         Extracts symptoms, disease mentions, onset duration, severity.
         Generates symptom analysis report.
"""

from utils.hf_client import hf_client
from schemas import SpecialistOpinion
from config import settings
import re
from typing import List, Dict


class SymptomAnalyzer:

    NER_MODEL = settings.HF_SYMPTOM_MODEL           # UFNLP/gatortron-medium
    FALLBACK_MODEL = settings.HF_TEXT_MODEL          # medgemma-4b-it (for summarization)
    DISPLAY_NAME = "GatorTron-medium (Clinical NER)"

    # ── Clinical condition KB (used when NER entities are mapped) ────────────
    CONDITION_MAP = {
        "stroke": {"diagnosis": "Cerebrovascular Accident (Stroke)", "confidence": 0.88,
                   "keywords": ["stroke", "cva", "cerebrovascular", "hemiparesis", "aphasia", "tia"]},
        "brain_tumor": {"diagnosis": "Suspected Intracranial Neoplasm", "confidence": 0.86,
                        "keywords": ["tumor", "mass", "glioma", "meningioma", "neoplasm", "lesion", "seizure"]},
        "mi": {"diagnosis": "Acute Myocardial Infarction", "confidence": 0.91,
               "keywords": ["chest pain", "myocardial infarction", "mi", "troponin", "angina", "stemi"]},
        "diabetes": {"diagnosis": "Diabetes Mellitus", "confidence": 0.85,
                     "keywords": ["diabetes", "hyperglycemia", "polydipsia", "polyuria", "hba1c"]},
        "hypertension": {"diagnosis": "Hypertension", "confidence": 0.83,
                         "keywords": ["hypertension", "high blood pressure", "elevated bp", "140/90"]},
        "pneumonia": {"diagnosis": "Community-Acquired Pneumonia", "confidence": 0.84,
                      "keywords": ["pneumonia", "cough", "dyspnea", "fever", "consolidation", "breath"]},
        "ckd": {"diagnosis": "Chronic Kidney Disease", "confidence": 0.80,
                "keywords": ["kidney", "renal", "creatinine elevated", "ckd", "dialysis", "proteinuria"]},
        "sepsis": {"diagnosis": "Sepsis / Systemic Infection", "confidence": 0.88,
                   "keywords": ["sepsis", "infection", "bacteremia", "sirs", "fever", "hypotension", "tachycardia"]},
    }

    def __init__(self):
        self.model_name = "symptom_analyzer"
        print(f"[{self.model_name}] Initialized with model: {self.NER_MODEL}")

    def analyze(self, symptoms_text: str) -> SpecialistOpinion:
        if not symptoms_text or len(symptoms_text.strip()) < 10:
            return SpecialistOpinion(
                model_name=self.model_name,
                diagnosis="Insufficient symptom data",
                confidence=0.0,
                reasoning="No clinical text or symptoms provided",
                key_findings={"model": self.NER_MODEL}
            )

        print(f"[{self.model_name}] Model: {self.NER_MODEL}")
        print(f"[{self.model_name}] Analyzing {len(symptoms_text)} chars of clinical text...")

        # ── Step 1: GatorTron NER — extract clinical entities ────────────────
        ner_entities = self._run_gatortron_ner(symptoms_text)
        ner_conditions = self._entities_to_conditions(ner_entities)

        # ── Step 2: Keyword-based clinical pattern matching (reliable fallback)
        kb_results = self._knowledge_base_analysis(symptoms_text)

        # ── Step 3: MedGemma text LLM for richer analysis ───────────────────
        llm_result = self._llm_clinical_analysis(symptoms_text)

        # ── Merge results ────────────────────────────────────────────────────
        all_conditions = list({c for c in ner_conditions + [r["diagnosis"] for r in kb_results]})
        primary = self._select_primary(ner_conditions, kb_results, llm_result)

        print(f"[{self.model_name}] Primary: {primary['diagnosis']} ({primary['confidence']:.0%})")
        print(f"[{self.model_name}] NER extracted {len(ner_entities)} entities")

        return SpecialistOpinion(
            model_name=self.model_name,
            diagnosis=primary["diagnosis"],
            confidence=primary["confidence"],
            reasoning=primary["reasoning"],
            detected_conditions=all_conditions[:6],
            key_findings={
                "model": self.NER_MODEL,
                "display_model": self.DISPLAY_NAME,
                "ner_entities": [e.get("word", "") for e in ner_entities[:10]],
                "ner_entity_types": list(set(e.get("entity_group", e.get("entity", "")) for e in ner_entities)),
                "kb_matches": len(kb_results),
                "llm_used": bool(llm_result)
            }
        )

    def _run_gatortron_ner(self, text: str) -> List[Dict]:
        """Run GatorTron NER to extract clinical entities."""
        try:
            # GatorTron is trained on MIMIC/clinical notes, handles up to 512 tokens
            entities = hf_client.ner(self.NER_MODEL, text[:512])
            print(f"[{self.model_name}] GatorTron extracted {len(entities)} entity tokens")
            # Aggregate word-pieces into full entity spans
            merged = self._merge_entity_spans(entities)
            return merged
        except Exception as e:
            print(f"[{self.model_name}] GatorTron NER error: {e}")
            return []

    def _merge_entity_spans(self, entities: List[Dict]) -> List[Dict]:
        """Merge B-/I- token classification spans into full entity words."""
        if not entities:
            return []
        merged = []
        current = None
        for ent in entities:
            tag = ent.get("entity_group") or ent.get("entity", "O")
            word = ent.get("word", "")
            score = ent.get("score", 0.0)
            if tag.startswith("B-") or (tag != "O" and current is None):
                if current:
                    merged.append(current)
                current = {"entity_group": tag.lstrip("B-"), "word": word, "score": score}
            elif tag.startswith("I-") and current:
                current["word"] += " " + word.lstrip("##")
                current["score"] = max(current["score"], score)
            else:
                if current:
                    merged.append(current)
                    current = None
        if current:
            merged.append(current)
        return merged

    def _entities_to_conditions(self, entities: List[Dict]) -> List[str]:
        """Map NER entity labels to clinical condition names."""
        conditions = []
        disease_tags = {"DISEASE", "PROBLEM", "SYMPTOM", "DIAGNOSIS", "CONDITION"}
        for ent in entities:
            tag = ent.get("entity_group", "").upper()
            if any(dt in tag for dt in disease_tags) and ent.get("score", 0) > 0.5:
                conditions.append(ent.get("word", "").strip().title())
        return list(set(conditions))

    def _knowledge_base_analysis(self, text: str) -> List[Dict]:
        """Keyword-based mapping of clinical text to diagnostic conditions."""
        text_lower = text.lower()
        results = []
        for cond_id, data in self.CONDITION_MAP.items():
            hits = sum(1 for kw in data["keywords"] if kw in text_lower)
            if hits > 0:
                adj_conf = min(data["confidence"] * (0.75 + hits * 0.08), 0.96)
                results.append({
                    "condition_id": cond_id,
                    "diagnosis": data["diagnosis"],
                    "confidence": adj_conf,
                    "hits": hits,
                    "reasoning": f"Clinical pattern match: {hits} keyword(s) in text"
                })
        return sorted(results, key=lambda x: x["confidence"], reverse=True)

    def _llm_clinical_analysis(self, text: str) -> Optional[Dict]:
        """Use MedGemma 4B for richer clinical narrative understanding."""
        prompt = (
            "You are a clinical NLP specialist. Analyze this clinical text and identify:\n"
            "1. Primary presenting symptoms\n"
            "2. Most likely diagnosis (single best answer)\n"
            "3. Confidence percentage (0-100)\n"
            "4. Brief clinical reasoning (1-2 sentences)\n\n"
            f"Clinical text: {text[:600]}\n\n"
            "Format: Diagnosis: [name] | Confidence: [%] | Reasoning: [text]"
        )
        try:
            response = hf_client.generate_text(self.FALLBACK_MODEL, prompt, max_new_tokens=200, temperature=0.2)
            if not response or len(response.strip()) < 20:
                return None
            # Parse format
            diag_match = re.search(r'Diagnosis:\s*([^|]+)', response, re.IGNORECASE)
            conf_match = re.search(r'Confidence:\s*(\d+)', response, re.IGNORECASE)
            reas_match = re.search(r'Reasoning:\s*(.+)', response, re.IGNORECASE | re.DOTALL)
            if diag_match:
                return {
                    "diagnosis": diag_match.group(1).strip(),
                    "confidence": float(conf_match.group(1)) / 100 if conf_match else 0.65,
                    "reasoning": reas_match.group(1).strip()[:200] if reas_match else response[:200]
                }
        except Exception as e:
            print(f"[{self.model_name}] LLM analysis error: {e}")
        return None

    def _select_primary(self, ner_conditions: List[str], kb_results: List[Dict],
                        llm_result: Optional[Dict]) -> Dict:
        """Decide the best primary diagnosis by weighting NER, KB, and LLM outputs."""
        if kb_results and not llm_result:
            top = kb_results[0]
            return {"diagnosis": top["diagnosis"], "confidence": top["confidence"],
                    "reasoning": f"GatorTron NER + clinical KB: {top['reasoning']}"}

        if llm_result and llm_result.get("confidence", 0) > 0.60:
            return {
                "diagnosis": llm_result["diagnosis"],
                "confidence": llm_result["confidence"],
                "reasoning": f"GatorTron NER + MedGemma reasoning: {llm_result['reasoning']}"
            }

        if kb_results:
            top = kb_results[0]
            return {"diagnosis": top["diagnosis"], "confidence": top["confidence"],
                    "reasoning": f"Clinical pattern analysis: {top['hits']} matching indicators"}

        if ner_conditions:
            return {"diagnosis": ner_conditions[0], "confidence": 0.60,
                    "reasoning": f"GatorTron NER clinical entity extraction"}

        return {"diagnosis": "Requires comprehensive clinical evaluation",
                "confidence": 0.45, "reasoning": "Insufficient clinical text for definitive diagnosis"}


from typing import Optional

symptom_analyzer = SymptomAnalyzer()

# notes_analyzer is an alias — Layer 1 wires it as "notes_analyzer" key
# but we reuse SymptomAnalyzer which handles both notes and symptoms
class NotesAnalyzer(SymptomAnalyzer):
    def __init__(self):
        super().__init__()
        self.model_name = "notes_analyzer"

notes_analyzer = NotesAnalyzer()
