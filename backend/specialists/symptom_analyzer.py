"""
Specialist 2 — Symptoms & Clinical Notes
Models: UFNLP/gatortron-medium (NER) + google/medgemma-4b-it (reasoning)
Purpose: Reads clinical text/notes and extracts symptoms, then reasons
         to a diagnosis — NO hardcoded keyword maps or condition tables.
"""

from utils.hf_client import hf_client
from schemas import SpecialistOpinion
from config import settings
import re
from typing import List, Dict, Optional

NER_MODEL     = settings.HF_SYMPTOM_MODEL   # UFNLP/gatortron-medium
REASON_MODEL  = settings.HF_TEXT_MODEL      # google/medgemma-4b-it
DISPLAY_NAME  = "GatorTron-medium NER + MedGemma-4B Reasoning"

SYSTEM_PROMPT = """You are a senior physician and clinical NLP specialist. \
You have trained in internal medicine, neurology, psychiatry, hepatology, and rare diseases. \
When you read clinical text, patient complaints, or doctor notes, you reason through the \
symptoms systematically to reach the most accurate diagnosis possible. \
You consider rare diseases when the symptom pattern cannot be explained by common conditions."""

SYMPTOM_ANALYSIS_TEMPLATE = """\
Analyze the following clinical text and determine the most likely diagnosis.

--- CLINICAL TEXT ---
{clinical_text}
--- END OF CLINICAL TEXT ---

{ner_hint}

Instructions:
1. Extract the key symptoms and signs described.
2. Consider the full clinical picture — including unusual or rare presentations.
3. Identify the single most likely primary diagnosis that explains all symptoms.
4. If symptoms span multiple organ systems (liver + brain + psychiatric), consider \
systemic or metabolic diseases.

Respond EXACTLY in this format:
Diagnosis: [full clinical diagnosis name]
Confidence: [0-100]
Key Symptoms: [comma-separated list of the most relevant symptoms found]
Reasoning: [2-3 sentences explaining why this diagnosis fits the clinical picture]
"""


class SymptomAnalyzer:

    def __init__(self):
        self.model_name = "symptom_analyzer"
        print(f"[{self.model_name}] Initialized — Pure AI mode")
        print(f"[{self.model_name}] NER: {NER_MODEL} | Reasoning: {REASON_MODEL}")

    def analyze(self, symptoms_text: str) -> SpecialistOpinion:
        """Pure AI symptom analysis — no keyword maps, no condition tables."""

        if not symptoms_text or len(symptoms_text.strip()) < 10:
            return self._empty_result("No clinical text provided")

        print(f"[{self.model_name}] Analyzing {len(symptoms_text)} chars of clinical text...")

        # ── Step 1: GatorTron NER — real trained model, extract clinical entities ──
        ner_entities = self._run_gatortron_ner(symptoms_text)
        ner_hint     = self._build_ner_hint(ner_entities)

        # ── Step 2: MedGemma-4B reasons to a diagnosis from the full text ─────
        result = self._ask_medgemma(symptoms_text, ner_hint)

        if result:
            print(f"[{self.model_name}] AI Diagnosis: {result['diagnosis']} ({result['confidence']:.0%})")
            return SpecialistOpinion(
                model_name=self.model_name,
                diagnosis=result["diagnosis"],
                confidence=result["confidence"],
                reasoning=result["reasoning"],
                detected_conditions=result.get("detected_conditions", [result["diagnosis"]]),
                key_findings={
                    "model":        NER_MODEL,
                    "display_model": DISPLAY_NAME,
                    "ner_entities": [e.get("word", "") for e in ner_entities[:10]],
                    "key_symptoms": result.get("key_symptoms", []),
                }
            )

        # ── Fallback: use NER entities if LLM fails ───────────────────────────
        if ner_entities:
            ner_labels = [e.get("word", "") for e in ner_entities if e.get("score", 0) > 0.5]
            diagnosis = ", ".join(ner_labels[:3]) if ner_labels else "Clinical entities detected"
            print(f"[{self.model_name}] MedGemma unavailable — using NER fallback")
            return SpecialistOpinion(
                model_name=self.model_name,
                diagnosis=f"Clinical findings: {diagnosis}",
                confidence=0.45,
                reasoning=f"GatorTron NER extracted {len(ner_entities)} clinical entities. MedGemma reasoning unavailable.",
                detected_conditions=ner_labels[:5],
                key_findings={"model": NER_MODEL, "display_model": DISPLAY_NAME,
                              "ner_entities": ner_labels}
            )

        return self._empty_result("AI analysis unavailable — check HF API token")

    # ── GatorTron NER (real trained model) ───────────────────────────────────

    def _run_gatortron_ner(self, text: str) -> List[Dict]:
        """Run GatorTron NER — this IS an AI model, not hardcoded logic."""
        try:
            entities = hf_client.ner(NER_MODEL, text[:512])
            merged   = self._merge_entity_spans(entities)
            print(f"[{self.model_name}] GatorTron NER: {len(merged)} clinical entities")
            return merged
        except Exception as e:
            print(f"[{self.model_name}] GatorTron NER error: {e}")
            return []

    def _merge_entity_spans(self, entities: List[Dict]) -> List[Dict]:
        """Merge B-/I- BIO tag spans into full entity phrases."""
        if not entities:
            return []
        merged, current = [], None
        for ent in entities:
            tag   = ent.get("entity_group") or ent.get("entity", "O")
            word  = ent.get("word", "")
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

    def _build_ner_hint(self, entities: List[Dict]) -> str:
        """Convert NER output into a readable hint for MedGemma."""
        if not entities:
            return ""
        disease_tags = {"DISEASE", "PROBLEM", "SYMPTOM", "DIAGNOSIS", "CONDITION", "SIGN"}
        relevant = [
            e["word"] for e in entities
            if any(t in e.get("entity_group", "").upper() for t in disease_tags)
            and e.get("score", 0) > 0.5
        ]
        if not relevant:
            return ""
        return f"\nGatorTron NER identified these clinical entities: {', '.join(relevant[:10])}\n"

    # ── MedGemma-4B reasoning ─────────────────────────────────────────────────

    def _ask_medgemma(self, clinical_text: str, ner_hint: str) -> Optional[Dict]:
        """Ask MedGemma-4B to reason from clinical text to a diagnosis."""
        truncated = clinical_text[:2000] if len(clinical_text) > 2000 else clinical_text
        prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            + SYMPTOM_ANALYSIS_TEMPLATE.format(
                clinical_text=truncated,
                ner_hint=ner_hint
            )
        )
        try:
            response = hf_client.generate_text(
                REASON_MODEL, prompt,
                max_new_tokens=350,
                temperature=0.15
            )
            if not response or len(response.strip()) < 20:
                return None
            return self._parse_response(response)
        except Exception as e:
            print(f"[{self.model_name}] MedGemma error: {e}")
            return None

    def _parse_response(self, response: str) -> Optional[Dict]:
        diag_m = re.search(r'Diagnosis:\s*([^\n]+)',    response, re.IGNORECASE)
        conf_m = re.search(r'Confidence:\s*(\d+)',      response, re.IGNORECASE)
        symp_m = re.search(r'Key Symptoms:\s*([^\n]+)', response, re.IGNORECASE)
        reas_m = re.search(r'Reasoning:\s*(.+)',        response, re.IGNORECASE | re.DOTALL)

        if not diag_m:
            lines = [l.strip() for l in response.split('\n') if len(l.strip()) > 10]
            if lines:
                return {
                    "diagnosis": lines[0].lstrip("*-•").strip()[:120],
                    "confidence": 0.55,
                    "reasoning": f"MedGemma-4B analysis: {response[:300]}",
                    "key_symptoms": [],
                    "detected_conditions": [],
                }
            return None

        diagnosis  = diag_m.group(1).strip().rstrip('.')
        confidence = float(conf_m.group(1)) / 100 if conf_m else 0.68

        key_symptoms_text = symp_m.group(1).strip() if symp_m else ""
        key_symptoms = [s.strip() for s in key_symptoms_text.split(',') if s.strip()]

        reasoning = reas_m.group(1).strip()[:400] if reas_m else f"MedGemma-4B: {diagnosis}"

        return {
            "diagnosis":           diagnosis,
            "confidence":          min(max(confidence, 0.0), 1.0),
            "reasoning":           f"GatorTron NER + MedGemma-4B: {reasoning}",
            "key_symptoms":        key_symptoms,
            "detected_conditions": [diagnosis] + key_symptoms[:3],
        }

    def _empty_result(self, reason: str) -> SpecialistOpinion:
        return SpecialistOpinion(
            model_name=self.model_name,
            diagnosis=reason,
            confidence=0.0,
            reasoning=reason,
            detected_conditions=[],
            key_findings={"model": NER_MODEL, "display_model": DISPLAY_NAME}
        )


symptom_analyzer = SymptomAnalyzer()


class NotesAnalyzer(SymptomAnalyzer):
    """Alias — clinical notes go through the same AI pipeline."""
    def __init__(self):
        super().__init__()
        self.model_name = "notes_analyzer"

notes_analyzer = NotesAnalyzer()
