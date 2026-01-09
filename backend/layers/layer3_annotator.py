"""
Layer 3: Explanation Generator
Creates annotated reports with marked evidence
"""
from utils.ollama_client import ollama_client
from utils.image_annotator import image_annotator
from utils.pdf_annotator import pdf_annotator
from schemas import FinalDiagnosis, PatientData, AnnotatedReport, Evidence
from config import settings
import os
import time
import base64
from typing import List


class Layer3Annotator:
    """Layer 3: Generates explanations and annotations"""
    
    def __init__(self):
        self.ollama = ollama_client
    
    def process(self, diagnosis: FinalDiagnosis, patient_data: PatientData) -> AnnotatedReport:
        """
        Generate annotated report with evidence
        
        Args:
            diagnosis: Final diagnosis from Layer 2
            patient_data: Original patient data from Layer 0
            
        Returns:
            AnnotatedReport with annotations and explanations
        """
        print("[Layer 3] Generating explanation and annotations...")
        start_time = time.time()
        
        # Step 1: Extract evidence from patient data
        evidence_items = self._extract_evidence(diagnosis, patient_data)
        print(f"[Layer 3] Extracted {len(evidence_items)} evidence items")
        
        # Step 2: Generate explanation text
        explanation = self._generate_explanation(diagnosis, evidence_items)
        print("[Layer 3] Generated explanation text")
        
        # Step 3: Annotate images
        annotated_images_paths = []
        if patient_data.images:
            print(f"[Layer 3] Annotating {len(patient_data.images)} images...")
            annotated_images_paths = self._annotate_images(
                patient_data.images,
                diagnosis.primary_diagnosis
            )
        
        # Step 4: Create annotated PDF report
        pdf_path = self._create_pdf_report(
            diagnosis,
            patient_data,
            evidence_items,
            explanation,
            annotated_images_paths
        )
        print(f"[Layer 3] Created PDF report: {pdf_path}")
        
        # Step 5: Generate visualization data
        viz_data = self._create_visualization_data(diagnosis, evidence_items)
        
        elapsed = time.time() - start_time
        print(f"[Layer 3] Annotation complete in {elapsed:.2f}s")
        
        return AnnotatedReport(
            diagnosis=diagnosis,
            evidence_items=evidence_items,
            explanation_text=explanation,
            annotated_pdf_path=pdf_path,
            annotated_images_paths=annotated_images_paths,
            visualization_data=viz_data
        )
    
    def _extract_evidence(self, diagnosis: FinalDiagnosis, data: PatientData) -> List[Evidence]:
        """Extract evidence items that support the diagnosis"""
        evidence_items = []
        
        # Use Ollama to identify relevant evidence
        prompt = f"""Given this diagnosis: {diagnosis.primary_diagnosis}

Review the following patient data and identify the TOP 5 pieces of evidence that support this diagnosis.

PATIENT DATA:
Symptoms: {data.symptoms}
Lab Results: {data.lab_results}
Clinical Notes: {data.clinical_notes}

For each piece of evidence, specify:
1. The exact text/finding
2. Where it was found (e.g., "Symptoms section", "Lab results", etc.)
3. Relevance score (0.0 to 1.0)

Format each as:
EVIDENCE: [text]
LOCATION: [where]
SCORE: [0.0-1.0]
---"""
        
        response = self.ollama.generate(prompt, temperature=0.5)
        
        # Parse response
        evidence_items = self._parse_evidence(response)
        
        # If parsing failed, create default evidence
        if not evidence_items:
            evidence_items = self._create_default_evidence(diagnosis, data)
        
        return evidence_items[:5]  # Top 5 items
    
    def _parse_evidence(self, response: str) -> List[Evidence]:
        """Parse evidence from Ollama response"""
        evidence_items = []
        
        try:
            sections = response.split('---')
            
            for section in sections:
                if 'EVIDENCE:' in section:
                    import re
                    
                    ev_match = re.search(r'EVIDENCE:\s*(.+?)(?:\n|$)', section, re.IGNORECASE)
                    loc_match = re.search(r'LOCATION:\s*(.+?)(?:\n|$)', section, re.IGNORECASE)
                    score_match = re.search(r'SCORE:\s*([\d.]+)', section, re.IGNORECASE)
                    
                    if ev_match:
                        evidence_items.append(Evidence(
                            text=ev_match.group(1).strip(),
                            location=loc_match.group(1).strip() if loc_match else "Patient data",
                            relevance_score=float(score_match.group(1)) if score_match else 0.8,
                            annotation_type="highlight"
                        ))
        
        except Exception as e:
            print(f"Evidence parsing error: {e}")
        
        return evidence_items
    
    def _create_default_evidence(self, diagnosis: FinalDiagnosis, data: PatientData) -> List[Evidence]:
        """Create default evidence items"""
        items = []
        
        if data.symptoms:
            items.append(Evidence(
                text=data.symptoms[:200],
                location="Patient Symptoms",
                relevance_score=0.85,
                annotation_type="highlight"
            ))
        
        if data.lab_results:
            lab_text = ", ".join([f"{k}: {v}" for k, v in list(data.lab_results.items())[:3]])
            items.append(Evidence(
                text=lab_text,
                location="Laboratory Results",
                relevance_score=0.80,
                annotation_type="highlight"
            ))
        
        if data.clinical_notes:
            items.append(Evidence(
                text=data.clinical_notes[:200],
                location="Clinical Notes",
                relevance_score=0.75,
                annotation_type="highlight"
            ))
        
        return items
    
    def _generate_explanation(self, diagnosis: FinalDiagnosis, evidence: List[Evidence]) -> str:
        """Generate human-readable explanation"""
        evidence_text = "\n".join([f"- {ev.text} (from {ev.location})" for ev in evidence])
        
        prompt = f"""Create a clear, doctor-friendly explanation of this diagnosis:

DIAGNOSIS: {diagnosis.primary_diagnosis}
CONFIDENCE: {diagnosis.confidence:.0%}

SUPPORTING EVIDENCE:
{evidence_text}

REASONING: {diagnosis.reasoning}

Write a 3-paragraph explanation that:
1. States the diagnosis and confidence level
2. Explains which evidence supports this conclusion
3. Mentions any uncertainties or alternative diagnoses

Write in professional medical language but keep it clear and concise."""
        
        explanation = self.ollama.generate(prompt, temperature=0.6)
        
        return explanation.strip()
    
    def _annotate_images(self, images_base64: List[str], diagnosis: str) -> List[str]:
        """Annotate medical images"""
        annotated_paths = []
        
        for i, img_b64 in enumerate(images_base64[:3]):  # Annotate up to 3 images
            try:
                # Annotate image
                annotated_b64 = image_annotator.create_default_annotation(img_b64, diagnosis)
                
                # Save to file
                img_path = os.path.join(settings.OUTPUT_DIR, f"annotated_image_{i}.png")
                with open(img_path, 'wb') as f:
                    f.write(base64.b64decode(annotated_b64))
                
                annotated_paths.append(img_path)
            
            except Exception as e:
                print(f"Image annotation error: {e}")
        
        return annotated_paths
    
    def _create_pdf_report(self, diagnosis: FinalDiagnosis, data: PatientData,
                          evidence: List[Evidence], explanation: str,
                          image_paths: List[str]) -> str:
        """Create annotated PDF report"""
        
        pdf_data = {
            "patient_info": data.patient_info,
            "diagnosis": diagnosis.primary_diagnosis,
            "confidence": diagnosis.confidence,
            "evidence": [
                {"text": ev.text, "location": ev.location}
                for ev in evidence
            ],
            "reasoning": explanation,
            "annotated_images": image_paths,
            "recommendations": [
                "Consult with a medical specialist for confirmation",
                "Additional diagnostic tests may be warranted",
                f"Confidence level: {diagnosis.confidence:.0%} - professional review recommended"
            ]
        }
        
        output_path = os.path.join(settings.OUTPUT_DIR, "diagnosis_report.pdf")
        
        try:
            pdf_annotator.create_annotated_report(output_path, pdf_data)
        except Exception as e:
            print(f"PDF creation error: {e}")
            output_path = ""
        
        return output_path
    
    def _create_visualization_data(self, diagnosis: FinalDiagnosis,
                                   evidence: List[Evidence]) -> dict:
        """Create data for frontend visualizations"""
        return {
            "confidence_breakdown": {
                "primary": diagnosis.confidence,
                "cross_validation": diagnosis.cross_validation_score,
                "secondary": [
                    {
                        "name": sec.get("diagnosis", "Unknown"),
                        "value": sec.get("confidence", 0.0)
                    }
                    for sec in diagnosis.secondary_diagnoses
                ]
            },
            "evidence_scores": [
                {
                    "text": ev.text[:50] + "...",
                    "score": ev.relevance_score,
                    "location": ev.location
                }
                for ev in evidence
            ],
            "anomaly_status": {
                "detected": diagnosis.anomaly_detected,
                "description": diagnosis.anomaly_description
            }
        }


# Global instance
layer3_annotator = Layer3Annotator()
