"""
Lab Test Analyzer - Layer 1 Specialist
Analyzes laboratory test results and flags abnormalities
"""
from utils.hf_client import hf_client
from config import settings
from schemas import SpecialistOpinion
from typing import Dict, Any


class LabAnalyzer:
    """Analyzes lab test results"""
    
    # Reference ranges for common lab tests
    NORMAL_RANGES = {
        "hemoglobin": {"min": 12.0, "max": 17.0, "unit": "g/dL"},
        "wbc": {"min": 4.0, "max": 11.0, "unit": "10^3/μL"},
        "rbc": {"min": 4.2, "max": 5.9, "unit": "10^6/μL"},
        "platelets": {"min": 150, "max": 400, "unit": "10^3/μL"},
        "glucose": {"min": 70, "max": 100, "unit": "mg/dL"},
        "cholesterol": {"min": 125, "max": 200, "unit": "mg/dL"},
        "triglycerides": {"min": 0, "max": 150, "unit": "mg/dL"},
        "sodium": {"min": 136, "max": 145, "unit": "mEq/L"},
        "potassium": {"min": 3.5, "max": 5.0, "unit": "mEq/L"},
        "creatinine": {"min": 0.6, "max": 1.2, "unit": "mg/dL"},
        "alt": {"min": 7, "max": 56, "unit": "U/L"},
        "ast": {"min": 10, "max": 40, "unit": "U/L"},
    }
    
    def __init__(self):
        self.model = settings.HF_LAB_MODEL
        self.hf = hf_client
    
    def analyze(self, lab_results: Dict[str, Any]) -> SpecialistOpinion:
        """
        Analyze lab test results
        
        Args:
            lab_results: Dictionary of test names to values
            
        Returns:
            SpecialistOpinion with findings
        """
        if not lab_results:
            return SpecialistOpinion(
                model_name="lab_analyzer",
                diagnosis="No lab results available",
                confidence=0.0,
                reasoning="No lab data provided"
            )
        
        # Step 1: Flag abnormal values
        abnormal_findings = self._flag_abnormalities(lab_results)
        
        # Step 2: Interpret abnormalities
        diagnosis, confidence, reasoning = self._interpret_abnormalities(abnormal_findings, lab_results)
        
        # Step 3: Extract conditions
        conditions = self._infer_conditions(abnormal_findings)
        
        return SpecialistOpinion(
            model_name="lab_analyzer",
            diagnosis=diagnosis,
            confidence=confidence,
            reasoning=reasoning,
            detected_conditions=conditions,
            key_findings=abnormal_findings
        )
    
    def _flag_abnormalities(self, lab_results: Dict[str, Any]) -> Dict[str, Any]:
        """Flag values outside normal ranges"""
        abnormalities = {}
        
        for test_name, value in lab_results.items():
            # Try to extract numeric value
            try:
                if isinstance(value, str):
                    # Extract first number from string
                    import re
                    numbers = re.findall(r'\d+\.?\d*', value)
                    if numbers:
                        numeric_value = float(numbers[0])
                    else:
                        continue
                else:
                    numeric_value = float(value)
                
                # Check against normal ranges
                test_lower = test_name.lower()
                for norm_test, ranges in self.NORMAL_RANGES.items():
                    if norm_test in test_lower:
                        if numeric_value < ranges["min"]:
                            abnormalities[test_name] = {
                                "value": numeric_value,
                                "normal_min": ranges["min"],
                                "normal_max": ranges["max"],
                                "unit": ranges["unit"],
                                "status": "LOW",
                                "deviation": (ranges["min"] - numeric_value) / ranges["min"] * 100
                            }
                        elif numeric_value > ranges["max"]:
                            abnormalities[test_name] = {
                                "value": numeric_value,
                                "normal_min": ranges["min"],
                                "normal_max": ranges["max"],
                                "unit": ranges["unit"],
                                "status": "HIGH",
                                "deviation": (numeric_value - ranges["max"]) / ranges["max"] * 100
                            }
                        break
            
            except (ValueError, TypeError):
                continue
        
        return abnormalities
    
    def _interpret_abnormalities(self, abnormalities: Dict[str, Any], all_labs: Dict[str, Any]) -> tuple:
        """Interpret what abnormalities might indicate"""
        if not abnormalities:
            return ("Normal lab results", 0.9, "All values within normal ranges")
        
        # Build interpretation prompt
        abnorm_text = "\n".join([
            f"- {test}: {data['value']} {data['unit']} ({data['status']}, normal: {data['normal_min']}-{data['normal_max']})"
            for test, data in abnormalities.items()
        ])
        
        prompt = f"""As a medical lab specialist, interpret these abnormal lab results:

{abnorm_text}

What condition(s) do these abnormalities suggest?
Provide:
1. Most likely diagnosis
2. Confidence (0-100%)
3. Clinical reasoning

Format:
DIAGNOSIS: [diagnosis]
CONFIDENCE: [number]%
REASONING: [explanation]"""
        
        # Try using HuggingFace model
        response = self.hf.query_text_generation(
            model=self.model,
            prompt=prompt,
            max_length=300,
            temperature=0.6
        )
        
        # Parse or use fallback
        if response and len(response) > 20:
            diagnosis, confidence, reasoning = self._parse_interpretation(response)
        else:
            diagnosis, confidence, reasoning = self._fallback_interpretation(abnormalities)
        
        return diagnosis, confidence, reasoning
    
    def _parse_interpretation(self, response: str) -> tuple:
        """Parse model response"""
        import re
        
        diagnosis = "Lab Abnormalities Detected"
        confidence = 0.7
        reasoning = response
        
        try:
            diag_match = re.search(r'DIAGNOSIS:\s*(.+?)(?:\n|$)', response, re.IGNORECASE)
            if diag_match:
                diagnosis = diag_match.group(1).strip()
            
            conf_match = re.search(r'CONFIDENCE:\s*(\d+)', response)
            if conf_match:
                confidence = float(conf_match.group(1)) / 100.0
            
            reas_match = re.search(r'REASONING:\s*(.+?)$', response, re.IGNORECASE | re.DOTALL)
            if reas_match:
                reasoning = reas_match.group(1).strip()
        
        except Exception as e:
            print(f"Parse error: {e}")
        
        return diagnosis, confidence, reasoning
    
    def _fallback_interpretation(self, abnormalities: Dict[str, Any]) -> tuple:
        """Rule-based interpretation"""
        patterns = {
            "anemia": ["hemoglobin", "rbc"],
            "infection": ["wbc"],
            "diabetes": ["glucose"],
            "hyperlipidemia": ["cholesterol", "triglycerides"],
            "kidney_disease": ["creatinine"],
            "liver_disease": ["alt", "ast"],
        }
        
        detected = []
        for condition, markers in patterns.items():
            if any(marker in test.lower() for test in abnormalities.keys() for marker in markers):
                detected.append(condition.replace("_", " ").title())
        
        if detected:
            diagnosis = f"Possible {detected[0]}"
            confidence = 0.65
            reasoning = f"Abnormal values detected in: {', '.join(abnormalities.keys())}"
        else:
            diagnosis = "Lab Abnormalities (Unknown Cause)"
            confidence = 0.5
            reasoning = "Unable to match abnormalities to specific condition"
        
        return diagnosis, confidence, reasoning
    
    def _infer_conditions(self, abnormalities: Dict[str, Any]) -> list:
        """Infer possible conditions from abnormalities"""
        conditions = []
        
        for test_name, data in abnormalities.items():
            test_lower = test_name.lower()
            
            if "hemoglobin" in test_lower and data["status"] == "LOW":
                conditions.append("Anemia")
            elif "glucose" in test_lower and data["status"] == "HIGH":
                conditions.append("Diabetes Mellitus")
            elif "cholesterol" in test_lower and data["status"] == "HIGH":
                conditions.append("Hyperlipidemia")
            elif "wbc" in test_lower and data["status"] == "HIGH":
                conditions.append("Infection or Inflammation")
            elif "creatinine" in test_lower and data["status"] == "HIGH":
                conditions.append("Kidney Disease")
            elif any(liver in test_lower for liver in ["alt", "ast"]) and data["status"] == "HIGH":
                conditions.append("Liver Disease")
        
        return list(set(conditions))


# Global instance
lab_analyzer = LabAnalyzer()
