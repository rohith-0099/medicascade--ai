
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

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
        pass  # Pure regex classifier — no external model needed

    def classify_sections(self, text: str) -> dict[str, str]:
        
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
    
    def _split_into_sections(self, text: str) -> list[str]:
        
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
        
        if any(keyword in section_lower for keyword in [
            'hemoglobin', 'haemoglobin', 'glucose', 'cholesterol', 'wbc', 'rbc', 'platelet',
            'ceruloplasmin', 'copper', 'bilirubin', 'troponin', 'creatinine', 'alt', 'ast',
            'ldh', 'inr', 'albumin', 'ammonia', 'urine copper', '24-hr', '24hr',
        ]):
            return "lab_results"
        
        if any(keyword in section_lower for keyword in ['history', 'previous', 'past medical', 'family history']):
            return "medical_history"
        
        if any(keyword in section_lower for keyword in ['medication', 'prescription', 'drug', 'tablet', 'capsule', 'mg', 'ml']):
            return "medications"
        
        if 'allerg' in section_lower:
            return "allergies"
        
        return "other"
    
    def extract_patient_info(self, demographics_text: str) -> dict[str, Any]:
        """Fast Regex-based extraction for patient info"""
        info = {}
        text = demographics_text.lower()
        
        # Name
        name_match = re.search(r'(?:name|patient|patient name)[:\s]+([a-z\s]+)', text)
        if name_match:
            info['name'] = name_match.group(1).strip().title()
            
        # Age
        age_match = re.search(r'(?:age|years|yrs)[:\s]+(\d{1,3})', text)
        if age_match:
            info['age'] = age_match.group(1)
            
        # Gender
        gender_match = re.search(r'(?:gender|sex)[:\s]+([a-z]+)', text)
        if gender_match:
            info['gender'] = gender_match.group(1).strip().title()
            
        # ID
        id_match = re.search(r'(?:id|mrn|ref)[:\s]+([a-z0-9\-\.]+)', text)
        if id_match:
            info['patient_id'] = id_match.group(1).upper()
            
        return info
    
    def extract_lab_values(self, lab_text: str) -> dict[str, Any]:
        """Fast Regex-based extraction for common lab values"""
        labs = {}
        text = lab_text.lower()
        
        patterns = {
            'hemoglobin': r'hemoglobin[:\s]+(\d+\.?\d*)',
            'wbc': r'wbc[:\s]+(\d+\.?\d*)',
            'glucose': r'glucose[:\s]+(\d+)',
            'creatinine': r'creatinine[:\s]+(\d+\.?\d*)',
            'cholesterol': r'cholesterol[:\s]+(\d+)',
            'platelets': r'platelets[:\s]+(\d+)',
            'potassium': r'potassium[:\s]+(\d+\.?\d*)',
            'sodium': r'sodium[:\s]+(\d+)'
        }
        
        for name, pattern in patterns.items():
            match = re.search(pattern, text)
            if match:
                labs[name] = match.group(1)
                
        return labs

data_classifier = DataClassifier()
