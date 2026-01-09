"""
Symptom Analyzer - Layer 1 Specialist
Analyzes patient symptoms and predicts potential diseases
"""
from utils.hf_client import hf_client
from config import settings
from schemas import SpecialistOpinion
import re


class SymptomAnalyzer:
    """Analyzes symptoms using medical LLM"""
    
    def __init__(self):
        self.model = settings.HF_SYMPTOM_MODEL
        self.hf = hf_client
    
    def analyze(self, symptoms_text: str, patient_info: dict = None) -> SpecialistOpinion:
        """
        Analyze symptoms and predict diseases
        
        Args:
            symptoms_text: Patient symptoms description
            patient_info: Optional patient demographic info (age, gender, etc.)
            
        Returns:
            SpecialistOpinion with diagnosis
        """
        if not symptoms_text or len(symptoms_text.strip()) < 5:
            return SpecialistOpinion(
                model_name="symptom_analyzer",
                diagnosis="Insufficient symptom data",
                confidence=0.0,
                reasoning="No symptoms provided"
            )
        
        # Build context with patient info
        context = ""
        if patient_info:
            age = patient_info.get("age", "unknown")
            gender = patient_info.get("gender", "unknown")
            context = f"Patient: {age} years old, {gender}\n"
        
        # Create medical prompt
        prompt = f"""{context}Symptoms: {symptoms_text}

As a medical AI assistant, analyze these symptoms and provide:
1. Most likely diagnosis
2. Confidence level (0-100%)
3. Key symptoms that support this diagnosis
4. List other possible conditions

Format your response as:
PRIMARY DIAGNOSIS: [diagnosis]
CONFIDENCE: [number]%
KEY SYMPTOMS: [list]
OTHER CONDITIONS: [list]"""
        
        # Query HuggingFace model
        response = self.hf.query_text_generation(
            model=self.model,
            prompt=prompt,
            max_length=400,
            temperature=0.7
        )
        
        # Parse response
        diagnosis, confidence, reasoning, conditions = self._parse_response(response)
        
        # Only use fallback if AI completely failed to respond
        if not response or len(response.strip()) < 10:
            print("⚠️  HuggingFace API unavailable - using fallback")
            diagnosis, confidence, reasoning, conditions = self._fallback_analysis(symptoms_text)
        
        return SpecialistOpinion(
            model_name="symptom_analyzer",
            diagnosis=diagnosis,
            confidence=confidence,
            reasoning=reasoning,
            detected_conditions=conditions,
            key_findings={"symptoms": symptoms_text}
        )
    
    def _parse_response(self, response: str) -> tuple:
        """Parse structured response from model"""
        diagnosis = "Unknown"
        confidence = 0.5
        reasoning = response
        conditions = []
        
        try:
            # Extract diagnosis
            diag_match = re.search(r'PRIMARY DIAGNOSIS:\s*(.+?)(?:\n|$)', response, re.IGNORECASE)
            if diag_match:
                diagnosis = diag_match.group(1).strip()
            
            # Extract confidence
            conf_match = re.search(r'CONFIDENCE:\s*(\d+)', response)
            if conf_match:
                confidence = float(conf_match.group(1)) / 100.0
            
            # Extract other conditions
            cond_match = re.search(r'OTHER CONDITIONS:\s*(.+?)(?:\n\n|$)', response, re.IGNORECASE | re.DOTALL)
            if cond_match:
                cond_text = cond_match.group(1)
                conditions = [c.strip() for c in cond_text.split(',') if c.strip()]
        
        except Exception as e:
            print(f"Response parsing error: {e}")
        
        return diagnosis, confidence, reasoning, conditions
    
    def _fallback_analysis(self, symptoms_text: str) -> tuple:
        """Simple rule-based fallback when API unavailable"""
        symptoms_lower = symptoms_text.lower()
        
        # Simple keyword matching
        rules = [
            {
                "keywords": ["fever", "cough", "cold", "sore throat"],
                "diagnosis": "Upper Respiratory Infection",
                "confidence": 0.75
            },
            {
                "keywords": ["headache", "nausea", "dizziness", "vision"],
                "diagnosis": "Migraine or Neurological Issue",
                "confidence": 0.70
            },
            {
                "keywords": ["chest pain", "shortness of breath", "heart"],
                "diagnosis": "Cardiovascular Condition",
                "confidence": 0.80
            },
            {
                "keywords": ["stomach", "abdominal pain", "vomiting", "diarrhea"],
                "diagnosis": "Gastrointestinal Issue",
                "confidence": 0.72
            },
            {
                "keywords": ["joint pain", "muscle pain", "stiffness"],
                "diagnosis": "Musculoskeletal Condition",
                "confidence": 0.68
            }
        ]
        
        matched_conditions = []
        best_match = None
        best_score = 0
        
        for rule in rules:
            matches = sum(1 for kw in rule["keywords"] if kw in symptoms_lower)
            if matches > 0:
                score = matches / len(rule["keywords"])
                matched_conditions.append(rule["diagnosis"])
                if score > best_score:
                    best_score = score
                    best_match = rule
        
        if best_match:
            return (
                best_match["diagnosis"],
                best_match["confidence"] * best_score,
                f"Based on symptom keywords: {', '.join(best_match['keywords'])}",
                matched_conditions
            )
        
        return (
            "Insufficient Data for Diagnosis",
            0.3,
            "Unable to match symptoms to known patterns",
            []
        )


# Global instance
symptom_analyzer = SymptomAnalyzer()
