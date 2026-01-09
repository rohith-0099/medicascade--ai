"""
Clinical Notes Analyzer - Layer 1 Specialist
Extracts medical entities from doctor's notes and clinical documentation
"""
from utils.hf_client import hf_client
from utils.ollama_client import ollama_client
from config import settings
from schemas import SpecialistOpinion


class NotesAnalyzer:
    """Analyzes clinical notes and extracts medical information"""
    
    def __init__(self):
        self.model = settings.HF_NOTES_MODEL
        self.hf = hf_client
        self.ollama = ollama_client
    
    def analyze(self, clinical_notes: str) -> SpecialistOpinion:
        """
        Analyze clinical notes
        
        Args:
            clinical_notes: Clinical documentation text
            
        Returns:
            SpecialistOpinion with extracted information
        """
        if not clinical_notes or len(clinical_notes.strip()) < 10:
            return SpecialistOpinion(
                model_name="notes_analyzer",
                diagnosis="No clinical notes available",
                confidence=0.0,
                reasoning="No clinical documentation provided"
            )
        
        # Use Ollama for analysis (more reliable than HF for this task)
        prompt = f"""Analyze these clinical notes and extract key medical information:

{clinical_notes}

Provide:
1. Primary diagnosis mentioned
2. Key medical conditions noted
3. Treatment plan if mentioned
4. Confidence in diagnosis (0-100%)

Format:
PRIMARY: [diagnosis]
CONDITIONS: [list]
TREATMENT: [plan]
CONFIDENCE: [number]%"""
        
        response = self.ollama.generate(prompt, temperature=0.5)
        
        # Parse response
        diagnosis, confidence, reasoning, conditions = self._parse_response(response, clinical_notes)
        
        return SpecialistOpinion(
            model_name="notes_analyzer",
            diagnosis=diagnosis,
            confidence=confidence,
            reasoning=reasoning,
            detected_conditions=conditions,
            key_findings={"notes_length": len(clinical_notes)}
        )
    
    def _parse_response(self, response: str, original_text: str) -> tuple:
        """Parse Ollama response"""
        import re
        
        diagnosis = "Clinical Notes Reviewed"
        confidence = 0.65
        reasoning = response
        conditions = []
        
        try:
            prim_match = re.search(r'PRIMARY:\s*(.+?)(?:\n|$)', response, re.IGNORECASE)
            if prim_match:
                diagnosis = prim_match.group(1).strip()
            
            conf_match = re.search(r'CONFIDENCE:\s*(\d+)', response)
            if conf_match:
                confidence = float(conf_match.group(1)) / 100.0
            
            cond_match = re.search(r'CONDITIONS:\s*(.+?)(?:\n|$)', response, re.IGNORECASE)
            if cond_match:
                cond_text = cond_match.group(1)
                conditions = [c.strip() for c in cond_text.split(',') if c.strip()]
        
        except Exception as e:
            print(f"Notes parsing error: {e}")
        
        # If nothing extracted, use simple keyword extraction
        if not conditions:
            conditions = self._extract_keywords(original_text)
        
        return diagnosis, confidence, reasoning, conditions
    
    def _extract_keywords(self, text: str) -> list:
        """Extract medical condition keywords"""
        common_conditions = [
            "diabetes", "hypertension", "infection", "pneumonia",
            "cancer", "tumor", "arthritis", "asthma", "copd",
            "heart disease", "stroke", "kidney disease", "liver disease"
        ]
        
        text_lower = text.lower()
        found = [cond for cond in common_conditions if cond in text_lower]
        
        return list(set(found))


# Global instance
notes_analyzer = NotesAnalyzer()
