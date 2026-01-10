
import re
from typing import Dict, Any, List
from utils.ollama_client import ollama_client

class DataClassifier:

    CATEGORIES = [
        "patient_demographics",
        "symptoms",
        "vital_signs",
        "lab_results",
        "medical_history",
        "clinical_notes",
        "medications",
        "allergies",
        "diagnosis",
        "other"
    ]
    
    def __init__(self):
        self.ollama = ollama_client
    
    def classify_sections(self, text: str) -> Dict[str, str]:
        
        sections = self._split_into_sections(text)
        
        classified_data = {
            "patient_demographics": "",
            "symptoms": "",
            "vital_signs": "",
            "lab_results": "",
            "medical_history": "",
            "clinical_notes": "",
            "medications": "",
            "allergies": "",
            "diagnosis": "",
            "other": ""
        }
        
        for section in sections:
            if len(section.strip()) < 10:
                continue
                
            category = self._classify_section(section)
            
            if category in classified_data:
                classified_data[category] += "\n" + section
        
        return classified_data
    
    def _split_into_sections(self, text: str) -> List[str]:
        
        patterns = [
            r'\n(?:Patient Information|PATIENT DETAILS?|Demographics?)[\s:]*\n',
            r'\n(?:Chief Complaint|SYMPTOMS?|Presenting Complaint)[\s:]*\n',
            r'\n(?:Vital Signs?|VITALS?)[\s:]*\n',
            r'\n(?:Lab(?:oratory)? Results?|TEST RESULTS?)[\s:]*\n',
            r'\n(?:Medical History|HISTORY|Past Medical History)[\s:]*\n',
            r'\n(?:Clinical Notes?|NOTES|Assessment)[\s:]*\n',
            r'\n(?:Medications?|MEDS|Prescriptions?)[\s:]*\n',
            r'\n(?:Allergies|ALLERGIES)[\s:]*\n',
            r'\n(?:Diagnosis|DIAGNOSIS|Impression)[\s:]*\n',
        ]
        
        combined_pattern = '|'.join(patterns)
        
        sections = re.split(combined_pattern, text, flags=re.IGNORECASE)
        
        if len(sections) <= 1:
            sections = text.split('\n\n')
        
        return [s.strip() for s in sections if s.strip()]
    
    def _classify_section(self, section: str) -> str:
        
        section_lower = section.lower()
        
        if any(keyword in section_lower for keyword in ['name:', 'age:', 'gender:', 'dob:', 'patient id']):
            return "patient_demographics"
        
        if any(keyword in section_lower for keyword in ['symptom', 'complaint', 'pain', 'fever', 'nausea', 'headache']):
            return "symptoms"
        
        if any(keyword in section_lower for keyword in ['blood pressure', 'heart rate', 'temperature', 'pulse', 'bp:', 'hr:']):
            return "vital_signs"
        
        if any(keyword in section_lower for keyword in ['hemoglobin', 'glucose', 'cholesterol', 'wbc', 'rbc', 'platelet']):
            return "lab_results"
        
        if any(keyword in section_lower for keyword in ['history', 'previous', 'past medical', 'family history']):
            return "medical_history"
        
        if any(keyword in section_lower for keyword in ['medication', 'prescription', 'drug', 'tablet', 'capsule', 'mg', 'ml']):
            return "medications"
        
        if 'allerg' in section_lower:
            return "allergies"
        
        try:
            category = self.ollama.classify_text(section, self.CATEGORIES)
            if category in self.CATEGORIES:
                return category
        except Exception as e:
            print(f"Ollama classification error: {e}")
        
        return "other"
    
    def extract_patient_info(self, demographics_text: str) -> Dict[str, Any]:
        
        fields = ["name", "age", "gender", "date_of_birth", "patient_id", "address", "phone"]
        
        try:
            extracted = self.ollama.extract_structured_data(demographics_text, fields)
            return extracted
        except Exception as e:
            print(f"Patient info extraction error: {e}")
            return {}
    
    def extract_lab_values(self, lab_text: str) -> Dict[str, Any]:
        
        fields = [
            "hemoglobin", "wbc", "rbc", "platelets",
            "glucose", "cholesterol", "triglycerides",
            "sodium", "potassium", "creatinine",
            "alt", "ast", "bilirubin"
        ]
        
        try:
            extracted = self.ollama.extract_structured_data(lab_text, fields)
            return extracted
        except Exception as e:
            print(f"Lab values extraction error: {e}")
            return {}

data_classifier = DataClassifier()
