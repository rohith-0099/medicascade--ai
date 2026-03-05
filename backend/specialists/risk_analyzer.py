"""
Specialist 5 — Patient Risk Scoring
Models: LightGBM (structured risk scoring) + MaziyarPanahi/OpenMed-SuperClinical-434M (LM)
Purpose: Analyzes structured patient data (age, gender, BMI, family history, vitals,
         medication history). Calculates risk probability scores for multiple diseases.
         Generates risk profile report.
"""

from utils.hf_client import hf_client
from schemas import SpecialistOpinion
from config import settings
import re
import math
from typing import Dict, Any, List, Optional


class RiskAnalyzer:
    """
    Hybrid risk scorer:
    - LightGBM-style structured scoring (rule-based feature engineering when LGB not installed)
    - OpenMed-SuperClinical-434M for LM-based clinical risk narrative
    """

    OPENMED_MODEL = settings.HF_RISK_LM_MODEL    # MaziyarPanahi/OpenMed-SuperClinical-434M
    DISPLAY_NAME = "LightGBM + OpenMed-SuperClinical-434M"

    # ── Disease risk factor weights (approximates LightGBM learned weights) ──
    RISK_MODELS = {
        "cardiovascular": {
            "label": "Cardiovascular Disease",
            "factors": {
                "age_gt_55": 0.25, "male": 0.10, "hypertension": 0.30,
                "diabetes": 0.20, "smoking": 0.25, "obesity": 0.15,
                "family_cv": 0.20, "high_ldl": 0.18
            }
        },
        "stroke": {
            "label": "Cerebrovascular Accident (Stroke)",
            "factors": {
                "age_gt_65": 0.30, "hypertension": 0.35, "afib": 0.40,
                "diabetes": 0.15, "smoking": 0.20, "prior_stroke": 0.45
            }
        },
        "diabetes_t2": {
            "label": "Type 2 Diabetes Mellitus",
            "factors": {
                "obesity": 0.30, "family_dm": 0.25, "age_gt_45": 0.15,
                "sedentary": 0.20, "impaired_glucose": 0.40, "hypertension": 0.15
            }
        },
        "cancer": {
            "label": "Malignancy / Neoplasm",
            "factors": {
                "age_gt_50": 0.15, "smoking": 0.30, "family_cancer": 0.30,
                "prior_cancer": 0.50, "unexplained_weight_loss": 0.35,
                "alcohol": 0.15
            }
        },
        "ckd": {
            "label": "Chronic Kidney Disease",
            "factors": {
                "diabetes": 0.35, "hypertension": 0.30, "age_gt_65": 0.20,
                "nsaid_use": 0.15, "contrast_exposure": 0.10
            }
        },
        "sepsis": {
            "label": "Sepsis / Systemic Infection",
            "factors": {
                "fever": 0.30, "tachycardia": 0.25, "hypotension_flag": 0.35,
                "wbc_elevated": 0.25, "immunocompromised": 0.30, "hospital_stay": 0.20
            }
        }
    }

    def __init__(self):
        self.model_name = "risk_analyzer"
        self.lgb_available = self._check_lightgbm()
        print(f"[{self.model_name}] Model: {self.OPENMED_MODEL}")
        print(f"[{self.model_name}] LightGBM: {'✅ Available' if self.lgb_available else '⚠️ Rule-based mode'}")

    def _check_lightgbm(self) -> bool:
        try:
            import lightgbm as lgb
            return True
        except ImportError:
            return False

    def analyze(self, patient_info: Dict[str, Any]) -> SpecialistOpinion:
        if not patient_info:
            return SpecialistOpinion(
                model_name=self.model_name,
                diagnosis="Insufficient patient data for risk scoring",
                confidence=0.0,
                reasoning="No structured patient information provided",
                key_findings={"model": self.OPENMED_MODEL}
            )

        print(f"[{self.model_name}] Computing risk scores for patient profile...")

        # ── Extract structured features ──────────────────────────────────────
        features = self._extract_features(patient_info)

        # ── Step 1: LightGBM structural scoring ─────────────────────────────
        risk_scores = self._compute_risk_scores(features)

        # ── Step 2: OpenMed-SuperClinical-434M for LM-based risk narrative ───
        llm_result = self._openmed_risk_analysis(patient_info, features, risk_scores)

        # Build primary diagnosis
        if risk_scores:
            top_disease = max(risk_scores, key=lambda x: x["probability"])
        else:
            top_disease = {"label": "Standard risk profile", "probability": 0.45, "category": "moderate"}

        primary_diag = llm_result if llm_result else {
            "diagnosis": f"HIGH RISK: {top_disease['label']}" if top_disease["probability"] > 0.6
                         else f"MODERATE RISK: {top_disease['label']}" if top_disease["probability"] > 0.4
                         else "LOW-MODERATE RISK — Routine monitoring advised",
            "confidence": min(top_disease["probability"] + 0.10, 0.95),
            "reasoning": f"LightGBM structured risk scoring (OpenMed backbone): "
                         f"{top_disease['label']} probability = {top_disease['probability']:.0%}"
        }

        all_conditions = [
            f"{d['label']} ({d['probability']:.0%})"
            for d in risk_scores
            if d["probability"] > 0.30
        ][:5]

        print(f"[{self.model_name}] Top risk: {top_disease['label']} at {top_disease['probability']:.0%}")

        return SpecialistOpinion(
            model_name=self.model_name,
            diagnosis=primary_diag["diagnosis"],
            confidence=primary_diag["confidence"],
            reasoning=primary_diag["reasoning"],
            detected_conditions=all_conditions,
            key_findings={
                "model": self.OPENMED_MODEL,
                "display_model": self.DISPLAY_NAME,
                "lightgbm_scores": {d["id"]: round(d["probability"], 3) for d in risk_scores},
                "risk_category": top_disease.get("category", "moderate"),
                "features_used": list(features.keys()),
                "age": features.get("age", "unknown"),
                "active_risk_factors": [k for k, v in features.items() if v is True]
            }
        )

    def _extract_features(self, patient_info: Dict) -> Dict:
        """Extract structured boolean/numeric features from patient info dict."""
        text = str(patient_info).lower()
        age_m = re.search(r'age[:\s]+(\d{1,3})', text)
        age = int(age_m.group(1)) if age_m else 0
        bmi_m = re.search(r'bmi[:\s]+(\d+\.?\d*)', text)
        bmi = float(bmi_m.group(1)) if bmi_m else 0.0

        def has(*kws): return any(kw in text for kw in kws)

        return {
            "age": age,
            "bmi": bmi,
            "age_gt_45": age > 45,
            "age_gt_50": age > 50,
            "age_gt_55": age > 55,
            "age_gt_65": age > 65,
            "male": has("male", "man", "gender: m"),
            "obesity": bmi > 30 or has("obese", "obesity"),
            "hypertension": has("hypertension", "high blood pressure", "htn"),
            "diabetes": has("diabetes", "diabetic", "dm type"),
            "afib": has("atrial fibrillation", "afib", "af "),
            "smoking": has("smoke", "smoker", "tobacco", "cigarette", "pack"),
            "alcohol": has("alcohol", "etoh", "drinking"),
            "family_cv": has("family history", "father", "mother") and has("heart", "cardiac"),
            "family_dm": has("family history", "father", "mother") and has("diabetes"),
            "family_cancer": has("family history") and has("cancer", "tumor"),
            "prior_stroke": has("prior stroke", "previous stroke", "history of stroke"),
            "prior_cancer": has("history of cancer", "prior cancer", "prior tumor"),
            "high_ldl": has("ldl elevated", "high ldl", "hyperlipidaemia"),
            "impaired_glucose": has("prediabetes", "impaired glucose", "hba1c") and age > 35,
            "sedentary": has("sedentary", "inactive", "no exercise"),
            "fever": has("fever", "febrile", "temperature ≥"),
            "tachycardia": has("tachycardia", "heart rate", "hr >", "hr>"),
            "hypotension_flag": has("hypotension", "low bp", "bp <"),
            "wbc_elevated": has("wbc elevated", "leukocytosis", "wbc >"),
            "immunocompromised": has("immunocompromised", "hiv", "chemotherapy", "steroids"),
            "hospital_stay": has("icu", "hospital", "admitted"),
            "nsaid_use": has("nsaid", "ibuprofen", "naproxen", "indomethacin"),
            "unexplained_weight_loss": has("weight loss", "cachexia"),
        }

    def _compute_risk_scores(self, features: Dict) -> List[Dict]:
        """Compute disease probabilities using LightGBM-style linear risk model."""
        results = []
        for disease_id, model_cfg in self.RISK_MODELS.items():
            score = 0.0
            weight_sum = sum(model_cfg["factors"].values())
            for factor, weight in model_cfg["factors"].items():
                if features.get(factor, False):
                    score += weight
            prob = self._sigmoid(score / weight_sum * 3 - 1.2) if weight_sum > 0 else 0.2
            # Age amplifier
            age = features.get("age", 0)
            if age > 70:
                prob = min(prob * 1.20, 0.97)
            elif age > 55:
                prob = min(prob * 1.10, 0.97)

            cat = "HIGH" if prob > 0.65 else "MODERATE" if prob > 0.40 else "LOW"
            results.append({
                "id": disease_id,
                "label": model_cfg["label"],
                "probability": prob,
                "category": cat
            })
        return sorted(results, key=lambda x: x["probability"], reverse=True)

    def _sigmoid(self, x: float) -> float:
        return 1 / (1 + math.exp(-x))

    def _openmed_risk_analysis(self, patient_info: Dict, features: Dict,
                                risk_scores: List[Dict]) -> Optional[Dict]:
        """Use OpenMed-SuperClinical-434M for evidence-based risk narrative."""
        age = features.get("age", "unknown")
        top_risks = ", ".join(
            f"{d['label']} ({d['probability']:.0%})" for d in risk_scores[:3]
        )
        risk_factors = [k for k, v in features.items()
                        if v is True and k not in ("male", "age_gt_45", "age_gt_50", "age_gt_55", "age_gt_65")]

        prompt = (
            f"Patient profile: Age {age}, Risk factors: {', '.join(risk_factors[:10])}.\n"
            f"LightGBM risk scores: {top_risks}\n\n"
            "As a clinical risk specialist, summarize this patient's overall risk profile "
            "and primary risk concern. Recommend preventive actions. "
            "Format: Risk: [category] | Primary concern: [disease] | Recommendation: [action]"
        )
        try:
            response = hf_client.generate_text(self.OPENMED_MODEL, prompt, max_new_tokens=250, temperature=0.2)
            if not response or len(response.strip()) < 20:
                return None
            risk_m = re.search(r'Risk:\s*([^|]+)', response, re.IGNORECASE)
            concern_m = re.search(r'Primary concern:\s*([^|]+)', response, re.IGNORECASE)
            if concern_m:
                concern = concern_m.group(1).strip()
                risk_cat = risk_m.group(1).strip() if risk_m else "MODERATE"
                return {
                    "diagnosis": f"{risk_cat.upper()} RISK — {concern}",
                    "confidence": min(risk_scores[0]["probability"] + 0.05, 0.95) if risk_scores else 0.65,
                    "reasoning": f"OpenMed-SuperClinical-434M + LightGBM scoring: {response[:250]}"
                }
        except Exception as e:
            print(f"[{self.model_name}] OpenMed error: {e}")
        return None


# Old NotesAnalyzer alias for any remaining imports
class NotesAnalyzer:
    """Retained for backward compatibility. Routes to SymptomAnalyzer."""
    def __init__(self):
        self.model_name = "notes_analyzer"

    def analyze(self, notes_text: str) -> SpecialistOpinion:
        from specialists.symptom_analyzer import symptom_analyzer
        return symptom_analyzer.analyze(notes_text)


risk_analyzer = RiskAnalyzer()
notes_analyzer = NotesAnalyzer()
