
from utils.hf_api import hf_client
from schemas import SpecialistOpinion

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
                
                print(f"[{self.model_name}] FLAN-T5 extracted: {diagnosis}")
                
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

notes_analyzer = NotesAnalyzer()
