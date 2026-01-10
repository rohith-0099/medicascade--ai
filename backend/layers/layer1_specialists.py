"""
Layer 1: Multiple AI Specialists
Orchestrates parallel analysis from all specialist models
"""
from specialists.symptom_analyzer import symptom_analyzer
from specialists.lab_analyzer import lab_analyzer
from specialists.scan_analyzer import scan_analyzer
from specialists.notes_analyzer import notes_analyzer
from specialists.risk_analyzer import risk_analyzer
from schemas import PatientData, Layer1Output, SpecialistOpinion
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


class Layer1Specialists:
    """Layer 1: Coordinates multiple specialist AI models"""
    
    def __init__(self):
        self.specialists = {
            "symptom": symptom_analyzer,
            "lab": lab_analyzer,
            "scan": scan_analyzer,
            "notes": notes_analyzer,
            "risk": risk_analyzer
        }
    
    def process(self, patient_data: PatientData) -> Layer1Output:
        """
        Process patient data through all specialists in parallel
        
        Args:
            patient_data: Structured patient data from Layer 0
            
        Returns:
            Layer1Output with all specialist opinions
        """
        print(f"[Layer 1] Running {len(self.specialists)} specialist models...")
        start_time = time.time()
        
        opinions = []
        
        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_specialist = {
                executor.submit(self._run_symptom_analyzer, patient_data): "symptom",
                executor.submit(self._run_lab_analyzer, patient_data): "lab",
                executor.submit(self._run_scan_analyzer, patient_data): "scan",
                executor.submit(self._run_notes_analyzer, patient_data): "notes",
                executor.submit(self._run_risk_analyzer, patient_data): "risk"
            }
            
            for future in as_completed(future_to_specialist):
                specialist_name = future_to_specialist[future]
                try:
                    opinion = future.result()
                    opinions.append(opinion)
                    print(f"[Layer 1] {specialist_name} completed: {opinion.diagnosis} ({opinion.confidence:.2f})")
                except Exception as e:
                    print(f"[Layer 1] Error in {specialist_name}: {e}")
                    # Add fallback opinion
                    opinions.append(SpecialistOpinion(
                        model_name=f"{specialist_name}_analyzer",
                        diagnosis=f"{specialist_name} analysis unavailable",
                        confidence=0.0,
                        reasoning=f"Error: {str(e)}"
                    ))
        
        elapsed = time.time() - start_time
        print(f"[Layer 1] All specialists completed in {elapsed:.2f}s")
        
        return Layer1Output(
            specialist_opinions=opinions,
            processing_time=elapsed
        )
    
    def _run_symptom_analyzer(self, data: PatientData) -> SpecialistOpinion:
        """Run symptom analyzer with patient symptoms"""
        # Combine symptoms from structured data and raw text
        symptoms_text = data.symptoms or ""
        if data.raw_text:
            symptoms_text += "\n" + data.raw_text[:1000]
        return symptom_analyzer.analyze(symptoms_text)
    
    def _run_lab_analyzer(self, data: PatientData) -> SpecialistOpinion:
        """Run lab analyzer with lab results"""
        return lab_analyzer.analyze(data.lab_results or [])
    
    def _run_scan_analyzer(self, data: PatientData) -> SpecialistOpinion:
        """Run scan analyzer with medical images"""
        return scan_analyzer.analyze(data.images or [])
    
    def _run_notes_analyzer(self, data: PatientData) -> SpecialistOpinion:
        """Run notes analyzer with clinical notes"""
        notes_text = data.clinical_notes or ""
        if not notes_text and data.raw_text:
            notes_text = data.raw_text[:2000]
        return notes_analyzer.analyze(notes_text)
    
    def _run_risk_analyzer(self, data: PatientData) -> SpecialistOpinion:
        """Run risk analyzer with patient info"""
        patient_info = data.patient_info or {}
        
        # Add medical history from raw text
        if data.raw_text:
            patient_info['medical_history'] = data.raw_text[:1000]
        
        return risk_analyzer.analyze(patient_info)


# Global instance
layer1_specialists = Layer1Specialists()
