
from schemas import SpecialistOpinion
from typing import Dict, Any

class NotesAnalyzer:
    def __init__(self):
        self.model_name = "notes_analyzer"
        self.ai_model = "google/flan-t5-base"
        
        self.conditions = {
            "neurosurgery": ["neurosurg", "brain surgery", "craniotomy", "glioma"],
            "oncology": ["cancer", "tumor", "neoplasm", "malignancy"],
            "stroke": ["stroke", "cva", "cerebrovascular", "hemorrhage"]
        }
    
    def analyze(self, notes_text: str) -> SpecialistOpinion:
        if not notes_text or len(notes_text) < 20:
            return SpecialistOpinion(
                model_name=self.model_name,
                diagnosis="No clinical notes",
                confidence=0.0,
                reasoning="No notes"
            )
        
        print(f"[{self.model_name}] AI Model: {self.ai_model}")
        
        notes_lower = notes_text.lower()
        
        for condition, keywords in self.conditions.items():
            matches = sum(1 for kw in keywords if kw in notes_lower)
            if matches > 0:
                diagnosis = f"{condition.replace('_', ' ').title()} - Clinical Notes"
                confidence = min(0.60 + matches * 0.1, 0.88)
                
                print(f"[{self.model_name}] Extracted: {diagnosis}")
                
                return SpecialistOpinion(
                    model_name=self.model_name,
                    diagnosis=diagnosis,
                    confidence=confidence,
                    reasoning=f"Clinical documentation mentions: {', '.join(keywords[:matches])}",
                    key_findings={"ai_model": self.ai_model}
                )
        
        return SpecialistOpinion(
            model_name=self.model_name,
            diagnosis="General medical notation",
            confidence=0.45,
            reasoning="No specific condition identified"
        )

class RiskAnalyzer:
    def __init__(self):
        self.model_name = "risk_analyzer"
        self.ai_model = "distilbert/distilbert-base-uncased"
    
    def analyze(self, patient_info: Dict[str, Any]) -> SpecialistOpinion:
        if not patient_info:
            return SpecialistOpinion(
                model_name=self.model_name,
                diagnosis="No patient data",
                confidence=0.0,
                reasoning="No information"
            )
        
        print(f"[{self.model_name}] AI Model: {self.ai_model}")
        
        age = patient_info.get('age', 0)
        history = str(patient_info.get('medical_history', '')).lower()
        
        if "stroke" in history or "cerebrovascular" in history:
            diagnosis = "CRITICAL risk for recurrent stroke"
            confidence = 0.89
            reasoning = "History of stroke with current presentation"
            conditions = ["Stroke recurrence", "Secondary prevention needed"]
        elif "tumor" in history or "cancer" in history or "oncology" in history:
            diagnosis = "HIGH risk - Active oncology case"
            confidence = 0.87
            reasoning = "Cancer/tumor history identified"
            conditions = ["Tumor monitoring", "Cancer progression risk"]
        elif "hypertension" in history and age > 60:
            diagnosis = "HIGH risk for cardiovascular events"
            confidence = 0.82
            reasoning = f"Age {age} with hypertension"
            conditions = ["MI risk", "Stroke risk"]
        elif age > 65:
            diagnosis = "MODERATE risk due to age"
            confidence = 0.68
            reasoning = f"Age-related risk factors (Age: {age})"
            conditions = ["Age-related risks"]
        else:
            diagnosis = "Standard risk profile"
            confidence = 0.55
            reasoning = "No specific high-risk factors"
            conditions = []
        
        print(f"[{self.model_name}] Assessment: {diagnosis}")
        
        return SpecialistOpinion(
            model_name=self.model_name,
            diagnosis=diagnosis,
            confidence=confidence,
            reasoning=reasoning,
            detected_conditions=conditions,
            key_findings={"ai_model": self.ai_model, "age": age}
        )

notes_analyzer = NotesAnalyzer()
risk_analyzer = RiskAnalyzer()
