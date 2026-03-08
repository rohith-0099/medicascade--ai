"""
Specialist 5 — Patient Risk Scoring
Models: MaziyarPanahi/OpenMed-SuperClinical-434M (primary) + google/medgemma-4b-it (fallback)
Purpose: Analyzes patient profile text and clinical data to assess overall risk level
         and flag the highest-priority clinical concern.
         NO hardcoded risk tables, weight vectors, or sigmoid scoring formulas.
"""

from utils.hf_client import hf_client
from schemas import SpecialistOpinion
from config import settings
import re
from typing import Dict, Any, Optional

OPENMED_MODEL  = settings.HF_RISK_LM_MODEL    # MaziyarPanahi/OpenMed-SuperClinical-434M
FALLBACK_MODEL = settings.HF_TEXT_MODEL       # google/medgemma-4b-it
DISPLAY_NAME   = "OpenMed-SuperClinical-434M (Risk Assessment)"

SYSTEM_PROMPT = """You are a senior clinical risk specialist and consultant physician. \
You assess patient risk profiles from structured and unstructured medical data. \
You evaluate age, sex, comorbidities, medications, vital signs, lifestyle factors, \
and test results to determine the patient's overall risk level and primary clinical concern. \
You provide evidence-based risk assessments grounded in clinical guidelines."""

RISK_ANALYSIS_TEMPLATE = """\
Assess the clinical risk for the following patient based on their medical profile.

--- PATIENT PROFILE ---
{patient_text}
--- END OF PROFILE ---

Instructions:
1. Identify the patient's key risk factors from the text above.
2. Determine the overall risk level (LOW / MODERATE / HIGH / CRITICAL).
3. Identify the single most urgent clinical concern or likely diagnosis.
4. Recommend the most important next clinical action.

Respond EXACTLY in this format:
Risk Level: [LOW / MODERATE / HIGH / CRITICAL]
Primary Concern: [most urgent diagnosis or clinical problem]
Confidence: [0-100]
Risk Factors: [comma-separated key risk factors identified]
Recommendation: [most important next step]
Reasoning: [2-3 sentence clinical explanation]
"""


class RiskAnalyzer:

    def __init__(self):
        self.model_name = "risk_analyzer"
        print(f"[{self.model_name}] Initialized — Pure AI risk assessment mode")
        print(f"[{self.model_name}] Primary: {OPENMED_MODEL}")
        print(f"[{self.model_name}] Fallback: {FALLBACK_MODEL}")

    def analyze(self, patient_info: Dict[str, Any]) -> SpecialistOpinion:
        """Pure AI patient risk assessment — no hardcoded scoring formulas."""

        if not patient_info:
            return self._empty_result("No patient data provided for risk assessment")

        # ── Build a readable patient profile string ───────────────────────────
        patient_text = self._build_patient_text(patient_info)

        if len(patient_text.strip()) < 15:
            return self._empty_result("Insufficient patient data for risk assessment")

        print(f"[{self.model_name}] Running AI risk assessment on patient profile...")

        # ── Try OpenMed first, fall back to MedGemma ─────────────────────────
        result = self._ask_openmed(patient_text) or self._ask_medgemma(patient_text)

        if result:
            print(f"[{self.model_name}] Risk: {result['risk_level']} | Concern: {result['concern']}")
            diagnosis = f"{result['risk_level']} RISK — {result['concern']}"
            return SpecialistOpinion(
                model_name=self.model_name,
                diagnosis=diagnosis,
                confidence=result["confidence"],
                reasoning=result["reasoning"],
                detected_conditions=result.get("risk_factors", [result["concern"]])[:5],
                key_findings={
                    "model":         OPENMED_MODEL,
                    "display_model": DISPLAY_NAME,
                    "risk_level":    result["risk_level"],
                    "risk_factors":  result.get("risk_factors", []),
                    "recommendation": result.get("recommendation", ""),
                    "primary_concern": result["concern"],
                }
            )

        return self._empty_result("Risk assessment unavailable — AI model did not respond")

    # ── Build patient profile text ────────────────────────────────────────────

    def _build_patient_text(self, patient_info: Dict) -> str:
        """Convert patient_info dict to a clean readable paragraph for the AI."""
        if isinstance(patient_info, str):
            return patient_info[:2500]

        parts = []
        # Priority fields first
        for key in ["name", "age", "sex", "gender", "dob", "medical_history",
                    "symptoms", "medications", "vitals", "conditions"]:
            val = patient_info.get(key, "")
            if val:
                parts.append(f"{key.replace('_', ' ').title()}: {str(val)[:300]}")

        # Remaining fields
        for k, v in patient_info.items():
            if k.lower() not in [p.split(':')[0].lower().replace(' ', '_') for p in parts] and v:
                parts.append(f"{k}: {str(v)[:300]}")

        return "\n".join(parts)[:2500]

    # ── OpenMed inference ─────────────────────────────────────────────────────

    def _ask_openmed(self, patient_text: str) -> Optional[Dict]:
        """Primary: OpenMed-SuperClinical-434M for risk assessment."""
        prompt = f"{SYSTEM_PROMPT}\n\n{RISK_ANALYSIS_TEMPLATE.format(patient_text=patient_text)}"
        try:
            response = hf_client.generate_text(
                OPENMED_MODEL, prompt,
                max_new_tokens=350,
                temperature=0.15
            )
            if not response or len(response.strip()) < 20:
                return None
            result = self._parse_response(response)
            if result:
                result["reasoning"] = f"OpenMed-SuperClinical-434M: {result['reasoning']}"
            return result
        except Exception as e:
            print(f"[{self.model_name}] OpenMed error: {e}")
            return None

    # ── MedGemma fallback ─────────────────────────────────────────────────────

    def _ask_medgemma(self, patient_text: str) -> Optional[Dict]:
        """Fallback: MedGemma-4B for risk assessment if OpenMed fails."""
        prompt = f"{SYSTEM_PROMPT}\n\n{RISK_ANALYSIS_TEMPLATE.format(patient_text=patient_text)}"
        try:
            response = hf_client.generate_text(
                FALLBACK_MODEL, prompt,
                max_new_tokens=350,
                temperature=0.15
            )
            if not response or len(response.strip()) < 20:
                return None
            result = self._parse_response(response)
            if result:
                result["reasoning"] = f"MedGemma-4B (risk fallback): {result['reasoning']}"
            return result
        except Exception as e:
            print(f"[{self.model_name}] MedGemma fallback error: {e}")
            return None

    # ── Parse response ────────────────────────────────────────────────────────

    def _parse_response(self, response: str) -> Optional[Dict]:
        risk_m    = re.search(r'Risk Level:\s*([^\n]+)',    response, re.IGNORECASE)
        concern_m = re.search(r'Primary Concern:\s*([^\n]+)', response, re.IGNORECASE)
        conf_m    = re.search(r'Confidence:\s*(\d+)',       response, re.IGNORECASE)
        factors_m = re.search(r'Risk Factors:\s*([^\n]+)', response, re.IGNORECASE)
        rec_m     = re.search(r'Recommendation:\s*([^\n]+)', response, re.IGNORECASE)
        reas_m    = re.search(r'Reasoning:\s*(.+)',         response, re.IGNORECASE | re.DOTALL)

        if not (risk_m or concern_m):
            # Unstructured — try to pull something useful
            lines = [l.strip() for l in response.split('\n') if len(l.strip()) > 15]
            if lines:
                return {
                    "risk_level":     "MODERATE",
                    "concern":        lines[0].lstrip("*-•").strip()[:120],
                    "confidence":     0.55,
                    "risk_factors":   [],
                    "recommendation": "",
                    "reasoning":      response[:300],
                }
            return None

        risk_level = (risk_m.group(1).strip().upper() if risk_m else "MODERATE")
        # Normalize risk level
        for keyword in ["CRITICAL", "HIGH", "MODERATE", "LOW"]:
            if keyword in risk_level:
                risk_level = keyword
                break

        concern    = concern_m.group(1).strip().rstrip('.') if concern_m else "Clinical risk identified"
        confidence = float(conf_m.group(1)) / 100 if conf_m else 0.65

        risk_factors_text = factors_m.group(1).strip() if factors_m else ""
        risk_factors = [f.strip() for f in risk_factors_text.split(',') if f.strip()]

        recommendation = rec_m.group(1).strip() if rec_m else ""
        reasoning      = reas_m.group(1).strip()[:400] if reas_m else f"AI risk assessment: {concern}"

        return {
            "risk_level":     risk_level,
            "concern":        concern,
            "confidence":     min(max(confidence, 0.0), 1.0),
            "risk_factors":   risk_factors,
            "recommendation": recommendation,
            "reasoning":      reasoning,
        }

    def _empty_result(self, reason: str) -> SpecialistOpinion:
        return SpecialistOpinion(
            model_name=self.model_name,
            diagnosis=reason,
            confidence=0.0,
            reasoning=reason,
            detected_conditions=[],
            key_findings={"model": OPENMED_MODEL, "display_model": DISPLAY_NAME}
        )


# ── Backward-compat aliases ───────────────────────────────────────────────────

class NotesAnalyzer:
    """Retained for backward compatibility. Routes to SymptomAnalyzer."""
    def __init__(self):
        self.model_name = "notes_analyzer"

    def analyze(self, notes_text: str) -> SpecialistOpinion:
        from specialists.symptom_analyzer import symptom_analyzer
        return symptom_analyzer.analyze(notes_text)


risk_analyzer  = RiskAnalyzer()
notes_analyzer = NotesAnalyzer()
