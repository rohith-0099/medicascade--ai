"""
Specialist 3 — Lab Results
Model: google/medgemma-4b-it
Purpose: Interprets blood tests, CBC, glucose, liver function, kidney values.
         Identifies abnormal values, flags critical results.
         Generates lab interpretation report.
"""

from utils.hf_client import hf_client
from schemas import SpecialistOpinion
from config import settings
import re
from typing import List, Dict, Optional


# ── Normal reference ranges ────────────────────────────────────────────────
LAB_REFERENCE = {
    "glucose":      {"low": 70,   "high": 100,  "unit": "mg/dL", "critical_high": 400},
    "hba1c":        {"low": 4.0,  "high": 5.7,  "unit": "%",     "prediabetic": 6.5},
    "creatinine":   {"low": 0.6,  "high": 1.2,  "unit": "mg/dL", "critical_high": 5.0},
    "bun":          {"low": 7,    "high": 20,   "unit": "mg/dL"},
    "hemoglobin":   {"low": 12.0, "high": 17.5, "unit": "g/dL"},
    "wbc":          {"low": 4.0,  "high": 11.0, "unit": "K/uL"},
    "platelets":    {"low": 150,  "high": 400,  "unit": "K/uL"},
    "sodium":       {"low": 136,  "high": 145,  "unit": "mEq/L"},
    "potassium":    {"low": 3.5,  "high": 5.0,  "unit": "mEq/L", "critical_high": 6.5},
    "alt":          {"low": 0,    "high": 40,   "unit": "U/L"},
    "ast":          {"low": 0,    "high": 40,   "unit": "U/L"},
    "troponin":     {"low": 0,    "high": 0.04, "unit": "ng/mL", "critical_high": 0.5},
    "ldl":          {"low": 0,    "high": 100,  "unit": "mg/dL"},
    "hdl":          {"low": 40,   "high": 999,  "unit": "mg/dL"},
    "tsh":          {"low": 0.4,  "high": 4.0,  "unit": "mIU/L"},
}


class LabAnalyzer:

    MODEL = settings.HF_LAB_MODEL    # google/medgemma-4b-it
    DISPLAY_NAME = "MedGemma-4B (Lab Interpretation)"

    def __init__(self):
        self.model_name = "lab_analyzer"
        print(f"[{self.model_name}] Initialized with model: {self.MODEL}")

    def analyze(self, lab_data) -> SpecialistOpinion:
        lab_text = str(lab_data) if lab_data else ""
        if not lab_text or len(lab_text.strip()) < 5:
            return SpecialistOpinion(
                model_name=self.model_name,
                diagnosis="No laboratory data provided",
                confidence=0.0,
                reasoning="No lab results were found in the patient record",
                key_findings={"model": self.MODEL}
            )

        print(f"[{self.model_name}] Model: {self.MODEL}")
        print(f"[{self.model_name}] Analyzing lab values...")

        # ── Step 1: Rule-based parsing of known lab patterns ─────────────────
        parsed_values = self._parse_lab_values(lab_text)
        rule_findings = self._rule_based_interpretation(parsed_values)

        # ── Step 2: MedGemma 4B for clinical lab interpretation ──────────────
        llm_result = self._medgemma_lab_analysis(lab_text, parsed_values, rule_findings)

        # ── Build output ─────────────────────────────────────────────────────
        primary = llm_result or (rule_findings[0] if rule_findings else None)
        if not primary:
            primary = {"diagnosis": "Lab values appear within normal limits",
                       "confidence": 0.65, "reasoning": "No significant abnormalities detected"}

        # Compile all abnormal values for XAI (Layer 3)
        abnormal_list = [
            {"test": v["name"], "value": v["value"], "unit": v["unit"],
             "status": v["status"], "reference": v.get("ref", "")}
            for v in parsed_values if v["status"] != "NORMAL"
        ]

        all_conditions = list({f.get("diagnosis", "") for f in rule_findings})
        if llm_result:
            all_conditions.insert(0, llm_result["diagnosis"])

        print(f"[{self.model_name}] Primary: {primary['diagnosis']} ({primary.get('confidence', 0):.0%})")
        print(f"[{self.model_name}] Abnormal values: {len(abnormal_list)}")

        return SpecialistOpinion(
            model_name=self.model_name,
            diagnosis=primary["diagnosis"],
            confidence=primary.get("confidence", 0.70),
            reasoning=primary["reasoning"],
            detected_conditions=all_conditions[:5],
            key_findings={
                "model": self.MODEL,
                "display_model": self.DISPLAY_NAME,
                "abnormal_values": abnormal_list,
                "critical_flags": [v["name"] for v in parsed_values if v.get("critical", False)],
                "total_values_parsed": len(parsed_values)
            }
        )

    def _parse_lab_values(self, text: str) -> List[Dict]:
        """Extract numeric lab values from text using regex patterns."""
        parsed = []
        text_lower = text.lower()

        patterns = [
            # glucose 145 mg/dL or glucose: 145
            (r'glucose[:\s]+(\d+\.?\d*)', "glucose", "mg/dL"),
            (r'hba1c[:\s]+(\d+\.?\d*)', "hba1c", "%"),
            (r'creatinine[:\s]+(\d+\.?\d*)', "creatinine", "mg/dL"),
            (r'bun[:\s]+(\d+\.?\d*)', "bun", "mg/dL"),
            (r'hemoglobin[:\s]+(\d+\.?\d*)', "hemoglobin", "g/dL"),
            (r'hgb[:\s]+(\d+\.?\d*)', "hemoglobin", "g/dL"),
            (r'wbc[:\s]+(\d+\.?\d*)', "wbc", "K/uL"),
            (r'platelets?[:\s]+(\d+)', "platelets", "K/uL"),
            (r'sodium[:\s]+(\d+)', "sodium", "mEq/L"),
            (r'potassium[:\s]+(\d+\.?\d*)', "potassium", "mEq/L"),
            (r'\balt[:\s]+(\d+)', "alt", "U/L"),
            (r'\bast[:\s]+(\d+)', "ast", "U/L"),
            (r'troponin[:\s]+(\d+\.?\d*)', "troponin", "ng/mL"),
            (r'ldl[:\s]+(\d+)', "ldl", "mg/dL"),
            (r'hdl[:\s]+(\d+)', "hdl", "mg/dL"),
            (r'tsh[:\s]+(\d+\.?\d*)', "tsh", "mIU/L"),
        ]

        for pat, name, unit in patterns:
            m = re.search(pat, text_lower)
            if m:
                val = float(m.group(1))
                ref = LAB_REFERENCE.get(name, {})
                status = "NORMAL"
                is_critical = False

                if ref:
                    if val > ref.get("critical_high", float("inf")):
                        status = "CRITICAL HIGH"
                        is_critical = True
                    elif val > ref["high"]:
                        status = "HIGH"
                    elif val < ref["low"]:
                        status = "LOW"

                parsed.append({
                    "name": name.upper(), "value": val, "unit": unit,
                    "status": status, "critical": is_critical,
                    "ref": f"{ref.get('low',0)}-{ref.get('high',0)} {unit}" if ref else ""
                })

        return parsed

    def _rule_based_interpretation(self, parsed_values: List[Dict]) -> List[Dict]:
        """Map abnormal lab values to diagnostic conditions."""
        findings = []
        value_map = {v["name"].lower(): v for v in parsed_values}

        def val(name): return value_map.get(name, {}).get("value")
        def status(name): return value_map.get(name, {}).get("status", "NORMAL")

        g = val("glucose"); hba = val("hba1c")
        if g and g >= 200:
            findings.append({"diagnosis": "Uncontrolled Diabetes Mellitus", "confidence": 0.93,
                              "reasoning": f"Glucose: {g} mg/dL — severely elevated"})
        elif g and g >= 126:
            findings.append({"diagnosis": "Diabetes Mellitus (Diagnostic Threshold)", "confidence": 0.89,
                              "reasoning": f"Fasting glucose {g} mg/dL ≥ 126 mg/dL diagnostic criterion"})
        elif hba and hba >= 6.5:
            findings.append({"diagnosis": "Diabetes Mellitus (HbA1c)", "confidence": 0.87,
                              "reasoning": f"HbA1c {hba}% ≥ 6.5% — diagnostic for DM"})
        elif hba and hba >= 5.7:
            findings.append({"diagnosis": "Pre-Diabetes", "confidence": 0.80,
                              "reasoning": f"HbA1c {hba}% — pre-diabetic range"})

        t = val("troponin")
        if t and t >= 0.5:
            findings.append({"diagnosis": "Acute Myocardial Infarction (Elevated Troponin)", "confidence": 0.94,
                              "reasoning": f"Troponin {t} ng/mL — significantly elevated, consistent with MI"})
        elif t and t > 0.04:
            findings.append({"diagnosis": "Myocardial Injury (Troponin Positive)", "confidence": 0.85,
                              "reasoning": f"Troponin {t} ng/mL — above normal threshold"})

        cr = val("creatinine")
        if cr and cr >= 5.0:
            findings.append({"diagnosis": "End-Stage Kidney Disease", "confidence": 0.93,
                              "reasoning": f"Creatinine {cr} mg/dL — severely impaired renal function"})
        elif cr and cr >= 2.0:
            findings.append({"diagnosis": "Chronic Kidney Disease (Stage 3-4)", "confidence": 0.86,
                              "reasoning": f"Creatinine {cr} mg/dL — moderately elevated"})

        hb = val("hemoglobin")
        if hb and hb < 8.0:
            findings.append({"diagnosis": "Severe Anaemia", "confidence": 0.91,
                              "reasoning": f"Hemoglobin {hb} g/dL — transfusion threshold"})
        elif hb and hb < 12.0:
            findings.append({"diagnosis": "Anaemia", "confidence": 0.83,
                              "reasoning": f"Hemoglobin {hb} g/dL — below reference range"})

        wbc = val("wbc")
        if wbc:
            if wbc > 20:
                findings.append({"diagnosis": "Leukocytosis — Possible Infection/Haematological Disease", "confidence": 0.85,
                                  "reasoning": f"WBC {wbc} K/uL — markedly elevated"})
            elif wbc < 2.0:
                findings.append({"diagnosis": "Leukopenia — Immunocompromised", "confidence": 0.82,
                                  "reasoning": f"WBC {wbc} K/uL — critically low"})

        alt = val("alt"); ast = val("ast")
        if alt and alt > 200:
            findings.append({"diagnosis": "Acute Hepatocellular Injury", "confidence": 0.88,
                              "reasoning": f"ALT {alt} U/L — severely elevated liver enzymes"})
        elif alt and alt > 40:
            findings.append({"diagnosis": "Liver Dysfunction (Elevated Transaminases)", "confidence": 0.78,
                              "reasoning": f"ALT {alt} U/L — mildly to moderately elevated"})

        k = val("potassium")
        if k and k >= 6.5:
            findings.append({"diagnosis": "Critical Hyperkalaemia", "confidence": 0.96,
                              "reasoning": f"Potassium {k} mEq/L — life-threatening, cardiac risk"})

        return sorted(findings, key=lambda x: x["confidence"], reverse=True)

    def _medgemma_lab_analysis(self, lab_text: str, parsed: List[Dict],
                                rule_findings: List[Dict]) -> Optional[Dict]:
        """Use MedGemma 4B to interpret lab results with clinical reasoning."""
        # Build structured labs summary for prompt
        if parsed:
            lab_summary = "\n".join(
                f"- {v['name']}: {v['value']} {v['unit']} [{v['status']}]"
                for v in parsed
            )
        else:
            lab_summary = lab_text[:500]

        rule_note = f"Rule-based diagnosis: {rule_findings[0]['diagnosis']}" if rule_findings else "No rule-based match."

        prompt = (
            f"You are an expert clinical pathologist. Interpret these laboratory results:\n\n"
            f"{lab_summary}\n\n"
            f"{rule_note}\n\n"
            "Task: Provide the primary clinical diagnosis based on these labs. "
            "Add any critical flags, patterns (e.g., metabolic acidosis, DKA, sepsis markers), or urgent concerns.\n"
            "Format: Diagnosis: [name] | Confidence: [0-100] | Reasoning: [brief clinical explanation]"
        )
        try:
            response = hf_client.generate_text(self.MODEL, prompt, max_new_tokens=250, temperature=0.15)
            if not response or len(response.strip()) < 20:
                return None
            diag_m = re.search(r'Diagnosis:\s*([^|]+)', response, re.IGNORECASE)
            conf_m = re.search(r'Confidence:\s*(\d+)', response, re.IGNORECASE)
            reas_m = re.search(r'Reasoning:\s*(.+?)(?:\||$)', response, re.IGNORECASE | re.DOTALL)
            if diag_m:
                return {
                    "diagnosis": diag_m.group(1).strip(),
                    "confidence": float(conf_m.group(1)) / 100 if conf_m else 0.72,
                    "reasoning": f"MedGemma-4B lab interpretation: {(reas_m.group(1).strip()[:200] if reas_m else response[:200])}"
                }
        except Exception as e:
            print(f"[{self.model_name}] MedGemma error: {e}")
        return None


lab_analyzer = LabAnalyzer()
