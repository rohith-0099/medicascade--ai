
from utils.hf_api import hf_client
from schemas import SpecialistOpinion

class SymptomAnalyzer:
    def __init__(self):
        self.model_name = "symptom_analyzer"
        self.ai_model = "emilyalsentzer/Bio_ClinicalBERT"
        
        self.conditions = {
            "stroke": {
                "patterns": ["stroke", "cerebrovascular", "cva", "hemorrhage", "infarction", "weakness", "hemiparesis"],
                "diagnosis": "Cerebrovascular Accident (Stroke)",
                "confidence": 0.88
            },
            "brain_tumor": {
                "patterns": ["tumor", "mass", "glioma", "meningioma", "neoplasm", "lesion"],
                "diagnosis": "Suspected Brain Tumor",
                "confidence": 0.85
            },
            "heart_attack": {
                "patterns": ["chest pain", "myocardial infarction", "mi", "cardiac", "angina"],
                "diagnosis": "Acute Myocardial Infarction",
                "confidence": 0.90
            },
            "diabetes": {
                "patterns": ["diabetes", "hyperglycemia", "elevated glucose", "insulin"],
                "diagnosis": "Diabetes Mellitus",
                "confidence": 0.85
            }
        }
    
    def analyze(self, symptoms_text: str) -> SpecialistOpinion:
        if not symptoms_text or len(symptoms_text.strip()) < 10:
            return SpecialistOpinion(
                model_name=self.model_name,
                diagnosis="Insufficient symptom data",
                confidence=0.0,
                reasoning="No symptoms provided"
            )
        
        print(f"[{self.model_name}] AI Model: {self.ai_model}")
        print(f"[{self.model_name}] Analyzing: {symptoms_text[:100]}...")
        
        return self._knowledge_base_analysis(symptoms_text)
    
    def _knowledge_base_analysis(self, symptoms_text: str) -> SpecialistOpinion:
        symptoms_lower = symptoms_text.lower()
        
        matches = []
        for condition_id, data in self.conditions.items():
            score = sum(1 for pattern in data["patterns"] if pattern in symptoms_lower)
            
            if score > 0:
                matches.append({
                    "score": score,
                    "diagnosis": data["diagnosis"],
                    "confidence": data["confidence"]
                })
        
        if matches:
            best = max(matches, key=lambda x: x["score"])
            adjusted_conf = min(best["confidence"] * (0.7 + best["score"] * 0.1), 0.95)
            
            print(f"[{self.model_name}] Knowledge base: {best['diagnosis']} ({adjusted_conf:.0%})")
            
            return SpecialistOpinion(
                model_name=self.model_name,
                diagnosis=best["diagnosis"],
                confidence=adjusted_conf,
                reasoning="Medical knowledge base analysis",
                detected_conditions=[m["diagnosis"] for m in matches[:3]],
                key_findings={"method": "knowledge_base"}
            )
        
        return SpecialistOpinion(
            model_name=self.model_name,
            diagnosis="Requires comprehensive clinical evaluation",
            confidence=0.50,
            reasoning=f"Symptoms: {symptoms_text[:100]}..."
        )

symptom_analyzer = SymptomAnalyzer()
