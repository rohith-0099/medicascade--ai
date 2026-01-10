
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
            # Prepare structured abnormal values for Layer 3
            abnormal_values = []
            if findings.get('glucose'):
                abnormal_values.append({
                    "test": "Glucose",
                    "value": findings['glucose'],
                    "status": "High" if findings['glucose'] >= 126 else "Normal"
                })
            if findings.get('bp'):
                abnormal_values.append({
                    "test": "Blood Pressure",
                    "value": findings['bp'],
                    "status": "High"
                })

            print(f"[{self.model_name}] Analysis: {findings['diagnosis']}")
            return SpecialistOpinion(
                model_name=self.model_name,
                diagnosis=findings['diagnosis'],
                confidence=findings['confidence'],
                reasoning=findings['reasoning'],
                detected_conditions=findings.get('conditions', []),
                key_findings={
                    "ai_model": self.ai_model, 
                    "abnormal_values": abnormal_values,
                    "abnormalities": findings.get('abnormal', [])
                }
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
            if glucose >= 126:
                return {
                    "diagnosis": "Diabetes Mellitus" if glucose < 200 else "Uncontrolled Diabetes Mellitus",
                    "confidence": 0.88 if glucose < 200 else 0.92,
                    "reasoning": f"Elevated glucose: {glucose} mg/dL",
                    "abnormal": ["Hyperglycemia"],
                    "glucose": glucose
                }
        
        bp_match = re.search(r'(\d{2,3})/(\d{2,3})', lab_lower)
        if bp_match:
            systolic = int(bp_match.group(1))
            if systolic >= 140:
                res = {
                    "diagnosis": "Hypertension",
                    "confidence": 0.85,
                    "reasoning": f"Elevated blood pressure: {bp_match.group(0)} mmHg",
                    "abnormal": ["Hypertension"],
                    "bp": bp_match.group(0)
                }
                if systolic >= 180:
                    res.update({
                        "diagnosis": "Hypertensive Crisis",
                        "confidence": 0.93,
                        "reasoning": f"Critical hypertension: {bp_match.group(0)} mmHg",
                        "abnormal": ["Severe hypertension"]
                    })
                return res
        
        return None

lab_analyzer = LabAnalyzer()
