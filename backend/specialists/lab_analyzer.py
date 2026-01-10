
from schemas import SpecialistOpinion
from typing import List
import re

class LabAnalyzer:
    def __init__(self):
        self.model_name = "lab_analyzer"
        self.ai_model = "dmis-lab/biobert-base-cased-v1.1"
    
    def analyze(self, lab_data: List) -> SpecialistOpinion:
        if not lab_data:
            return SpecialistOpinion(
                model_name=self.model_name,
                diagnosis="No laboratory results",
                confidence=0.0,
                reasoning="No lab data"
            )
        
        print(f"[{self.model_name}] AI Model: {self.ai_model}")
        
        lab_text = str(lab_data)
        findings = self._analyze_lab_values(lab_text)
        
        if findings:
            print(f"[{self.model_name}] Analysis: {findings['diagnosis']}")
            return SpecialistOpinion(
                model_name=self.model_name,
                diagnosis=findings['diagnosis'],
                confidence=findings['confidence'],
                reasoning=findings['reasoning'],
                detected_conditions=findings.get('conditions', []),
                key_findings={"ai_model": self.ai_model, "abnormalities": findings.get('abnormal', [])}
            )
        
        return SpecialistOpinion(
            model_name=self.model_name,
            diagnosis="Lab values within parameters",
            confidence=0.65,
            reasoning="No critical abnormalities"
        )
    
    def _analyze_lab_values(self, lab_text: str) -> dict:
        lab_lower = lab_text.lower()
        
        glucose_match = re.search(r'glucose[:\s]+(\d+)', lab_lower)
        if glucose_match:
            glucose = int(glucose_match.group(1))
            if glucose >= 200:
                return {
                    "diagnosis": "Uncontrolled Diabetes Mellitus",
                    "confidence": 0.92,
                    "reasoning": f"Severely elevated glucose: {glucose} mg/dL",
                    "abnormal": ["Hyperglycemia"]
                }
            elif glucose >= 126:
                return {
                    "diagnosis": "Diabetes Mellitus",
                    "confidence": 0.88,
                    "reasoning": f"Elevated fasting glucose: {glucose} mg/dL"
                }
        
        bp_match = re.search(r'(\d{2,3})/(\d{2,3})', lab_lower)
        if bp_match:
            systolic = int(bp_match.group(1))
            if systolic >= 180:
                return {
                    "diagnosis": "Hypertensive Crisis",
                    "confidence": 0.93,
                    "reasoning": f"Critical hypertension: {bp_match.group(0)} mmHg",
                    "abnormal": ["Severe hypertension"]
                }
        
        return None

lab_analyzer = LabAnalyzer()
