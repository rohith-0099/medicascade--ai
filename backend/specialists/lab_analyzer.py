"""
Specialist 3 — Lab Results
Model: google/medgemma-4b-it
Purpose: Reads lab reports and identifies all abnormal values, patterns,
         and the most likely clinical diagnosis — NO hardcoded rules.
         The AI model reads the lab text exactly as a doctor would.
"""

from utils.hf_client import hf_client
from schemas import SpecialistOpinion
from config import settings
import re
from typing import Dict, Any, Optional

MODEL = settings.HF_LAB_MODEL          # google/medgemma-4b-it
DISPLAY_NAME = "MedGemma-4B (Lab Interpretation)"

SYSTEM_PROMPT = """You are an expert clinical pathologist and diagnostician. \
You have deep knowledge of all medical conditions including common and rare diseases \
such as Wilson's Disease, metabolic disorders, haematological malignancies, \
autoimmune conditions, endocrine disorders, and infectious diseases. \
When you read a lab report, you identify ALL abnormal values, recognize diagnostic patterns, \
and determine the single most likely primary diagnosis. You do not rely on checklists — \
you reason like a senior consultant physician."""

LAB_ANALYSIS_TEMPLATE = """\
Analyze the following patient laboratory data and provide a clinical diagnosis.

--- LAB REPORT ---
{lab_text}
--- END OF LAB REPORT ---

Instructions:
1. Identify every abnormal value in the report.
2. Recognize any diagnostic patterns (e.g., low ceruloplasmin + high urine copper = Wilson's Disease, \
elevated troponin + CK-MB = myocardial injury, high HbA1c + glucose = diabetes).
3. Consider rare diseases if the pattern demands it — do NOT default to common diagnoses \
when the biochemical evidence points elsewhere.
4. State the single most likely primary diagnosis.

Respond EXACTLY in this format:
Diagnosis: [full diagnosis name]
Confidence: [0-100]
Key Findings: [comma-separated list of the 3-5 most important abnormal values]
Reasoning: [2-3 sentence clinical explanation of why this is the diagnosis]
"""


class LabAnalyzer:

    def __init__(self):
        self.model_name = "lab_analyzer"
        print(f"[{self.model_name}] Initialized — Pure AI mode (MedGemma-4B)")
        print(f"[{self.model_name}] Model: {MODEL}")

    def analyze(self, lab_data: Any) -> SpecialistOpinion:
        """Pure AI lab interpretation — no hardcoded rules."""

        # ── Prepare text ─────────────────────────────────────────────────────
        if not lab_data:
            return self._empty_result("No laboratory data provided")

        lab_text = lab_data if isinstance(lab_data, str) else str(lab_data)
        lab_text = lab_text.strip()

        if len(lab_text) < 10:
            return self._empty_result("Lab data too short to analyze")

        print(f"[{self.model_name}] Sending {len(lab_text)} chars to MedGemma-4B...")

        # ── Ask MedGemma-4B ───────────────────────────────────────────────────
        result = self._ask_medgemma(lab_text)

        if result:
            print(f"[{self.model_name}] AI Diagnosis: {result['diagnosis']} ({result['confidence']:.0%})")
            return SpecialistOpinion(
                model_name=self.model_name,
                diagnosis=result["diagnosis"],
                confidence=result["confidence"],
                reasoning=result["reasoning"],
                detected_conditions=result.get("detected_conditions", [result["diagnosis"]]),
                key_findings={
                    "model":         MODEL,
                    "display_model": DISPLAY_NAME,
                    "key_findings":  result.get("key_findings", []),
                    "ai_raw":        result.get("raw", "")[:300],
                }
            )

        # ── Graceful fallback (model unavailable) ─────────────────────────────
        print(f"[{self.model_name}] MedGemma unavailable — returning safe fallback")
        return self._empty_result(
            "Lab analysis unavailable — AI model did not respond. "
            "Please re-upload the document or check the HF API token."
        )

    # ── Internal: call MedGemma-4B ────────────────────────────────────────────

    def _ask_medgemma(self, lab_text: str) -> Optional[Dict]:
        """Send lab text to MedGemma-4B and parse the structured response."""

        # Truncate very long reports but keep key values
        truncated = lab_text[:2500] if len(lab_text) > 2500 else lab_text

        prompt = f"{SYSTEM_PROMPT}\n\n{LAB_ANALYSIS_TEMPLATE.format(lab_text=truncated)}"

        try:
            response = hf_client.generate_text(
                MODEL, prompt,
                max_new_tokens=400,
                temperature=0.1   # Low temperature → deterministic, clinical
            )

            if not response or len(response.strip()) < 20:
                print(f"[{self.model_name}] Empty response from MedGemma")
                return None

            return self._parse_response(response)

        except Exception as e:
            print(f"[{self.model_name}] MedGemma error: {e}")
            return None

    def _parse_response(self, response: str) -> Optional[Dict]:
        """Extract structured fields from MedGemma's formatted response."""

        diag_m  = re.search(r'Diagnosis:\s*([^\n]+)',    response, re.IGNORECASE)
        conf_m  = re.search(r'Confidence:\s*(\d+)',      response, re.IGNORECASE)
        key_m   = re.search(r'Key Findings:\s*([^\n]+)', response, re.IGNORECASE)
        reas_m  = re.search(r'Reasoning:\s*(.+)',        response, re.IGNORECASE | re.DOTALL)

        if not diag_m:
            # Try to extract any reasonable diagnosis from the response
            # The model may not have followed the format exactly
            lines = [l.strip() for l in response.split('\n') if len(l.strip()) > 10]
            if lines:
                # Use first substantive line as diagnosis
                diag = lines[0].lstrip("*-•").strip()
                return {
                    "diagnosis": diag[:120],
                    "confidence": 0.60,
                    "reasoning":  f"MedGemma-4B analysis: {response[:300]}",
                    "key_findings": [],
                    "detected_conditions": [diag[:120]],
                    "raw": response
                }
            return None

        diagnosis = diag_m.group(1).strip().rstrip('.')
        confidence = float(conf_m.group(1)) / 100 if conf_m else 0.70

        key_findings_text = key_m.group(1).strip() if key_m else ""
        key_findings = [kf.strip() for kf in key_findings_text.split(',') if kf.strip()]

        reasoning = ""
        if reas_m:
            reasoning = reas_m.group(1).strip()[:400]
        if not reasoning:
            reasoning = f"MedGemma-4B clinical lab interpretation: {diagnosis}"

        return {
            "diagnosis":           diagnosis,
            "confidence":          min(max(confidence, 0.0), 1.0),
            "reasoning":           f"MedGemma-4B (lab specialist): {reasoning}",
            "key_findings":        key_findings,
            "detected_conditions": [diagnosis] + key_findings[:3],
            "raw":                 response
        }

    def _empty_result(self, reason: str) -> SpecialistOpinion:
        return SpecialistOpinion(
            model_name=self.model_name,
            diagnosis=reason,
            confidence=0.0,
            reasoning=reason,
            detected_conditions=[],
            key_findings={"model": MODEL, "display_model": DISPLAY_NAME}
        )


lab_analyzer = LabAnalyzer()
