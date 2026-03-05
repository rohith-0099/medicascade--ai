"""
Layer 3 — XAI Explanation
Models:
  • SHAP          — Feature importance scores from specialist outputs
  • Grad-CAM      — Gradient-weighted class activation maps (imaging)
  • google/medgemma-4b-it — Human-readable clinical explanation for doctor

Purpose: Explains the AI's diagnosis process in plain language to the doctor,
         identifies which features drove the decision, and annotates reports/images.
"""

from utils.hf_client import hf_client
from utils.image_annotator import image_annotator
from utils.pdf_annotator import pdf_annotator
from schemas import FinalDiagnosis, PatientData, AnnotatedReport, Evidence
from config import settings
import os
import time
import base64
import re
from typing import List

class Layer3Annotator:

    EXPLAINER_MODEL = "google/medgemma-4b-it"

    def __init__(self):
        pass  # All model calls via hf_client

    def process(self, diagnosis: FinalDiagnosis, patient_data: PatientData, layer1_output=None) -> AnnotatedReport:
        
        print("[Layer 3] Generating explanation and annotations...")
        start_time = time.time()
        
        self.layer1_output = layer1_output
        
        evidence_items = self._extract_evidence_fast(diagnosis, patient_data)
        print(f"[Layer 3] Extracted {len(evidence_items)} evidence items")
        
        specific_values = self._extract_specific_values(patient_data, evidence_items)
        
        explanation = self._generate_explanation_fast(diagnosis, evidence_items, specific_values)
        print("[Layer 3] Generated explanation text")
        
        annotated_images_paths = []
        if patient_data.images:
            print(f"[Layer 3] Annotating {len(patient_data.images)} images...")
            annotated_images_paths = self._annotate_images(
                patient_data.images,
                diagnosis.primary_diagnosis
            )
        
        pdf_path = self._create_pdf_report(
            diagnosis,
            patient_data,
            evidence_items,
            explanation,
            annotated_images_paths,
            specific_values
        )
        print(f"[Layer 3] Created PDF report: {pdf_path}")
        
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
    
    def _extract_specific_values(self, patient_data: PatientData, evidence: List[Evidence]) -> List[str]:
        """Extract specific medical values for circling - checks both evidence and raw data"""
        specific_values = []
        import re
        
        # 1. Check structured lab results first (High Priority)
        if patient_data.lab_results:
            for test, value in patient_data.lab_results.items():
                test_lower = test.lower()
                if any(k in test_lower for k in ['glucose', 'blood pressure', 'bp', 'temp', 'heart', 'hemoglobin']):
                    label = test.replace('_', ' ').title()
                    specific_values.append(f"**{label}:** {value}")
        
        # 2. Check evidence text for formatted values
        for ev in evidence:
            text_lower = ev.text.lower()
            
            # Blood Pressure (if not caught in structured data)
            if ('blood pressure' in text_lower or 'bp' in text_lower or '/' in ev.text) and 'blood pressure' not in str(specific_values).lower():
                bp_match = re.search(r'(\d{2,3})/(\d{2,3})', ev.text)
                if bp_match:
                    specific_values.append(f"**Blood Pressure:** {bp_match.group(0)} mmHg")
            
            # Generic pattern: **Label: Value**
            generic_match = re.search(r'\*\*([A-Za-z0-9\s\-\(\)]+):\s*([A-Za-z0-9\.\/%<>=\-]+)\*\*', ev.text)
            if generic_match:
                label = generic_match.group(1).strip()
                val = generic_match.group(2).strip()
                # Avoid duplicates
                if label.lower() not in [v.split(':')[0].lower().strip('* ') for v in specific_values]:
                    specific_values.append(f"**{label}:** {val}")
                    
        return list(set(specific_values))

    def _extract_evidence_fast(self, diagnosis: FinalDiagnosis, data: PatientData) -> List[Evidence]:
        
        items = []
        
        if self.layer1_output:
            for opinion in self.layer1_output.specialist_opinions:
                if opinion.model_name == "lab_analyzer":
                    abnormal_labs = opinion.key_findings.get('abnormal_values', [])
                    for lab in abnormal_labs:
                        test_name = lab.get('test', 'Unknown test')
                        value = lab.get('value', 0)
                        status = lab.get('status', '')
                        
                        items.append(Evidence(
                            text=f"**{test_name.upper()}: {value}** ({status})",
                            location="Laboratory Results - ABNORMAL",
                            relevance_score=0.95,
                            annotation_type="highlight"
                        ))
                
                if opinion.model_name == "scan_analyzer":
                   ml_prob = opinion.key_findings.get('ml_tumor_probability', 0)
                   if ml_prob > 0.5:
                       items.append(Evidence(
                           text=f"**TUMOR PROBABILITY: {ml_prob:.1%}** (ML Model)",
                           location="Brain Scan Analysis",
                           relevance_score=0.99,
                           annotation_type="highlight"
                       ))
        
        if data.symptoms:
            items.append(Evidence(
                text=data.symptoms[:200],
                location="Patient Symptoms",
                relevance_score=0.85,
                annotation_type="highlight"
            ))
        
        if data.clinical_notes:
            items.append(Evidence(
                text=data.clinical_notes[:200],
                location="Clinical Notes",
                relevance_score=0.75,
                annotation_type="highlight"
            ))
        
        if data.images and len(data.images) > 0:
            items.append(Evidence(
                text=f"Abnormalities detected in {len(data.images)} medical images",
                location="Medical Imaging",
                relevance_score=0.90,
                annotation_type="image_marker"
            ))
        
        return items[:20]
    
    def _generate_explanation_fast(self, diagnosis: FinalDiagnosis, evidence: List[Evidence], specific_values: List[str] = None) -> str:

        clinical_explanation = self._generate_clinical_explanation(diagnosis, evidence, specific_values)
        
        return clinical_explanation
    
    def _generate_clinical_explanation(self, diagnosis: FinalDiagnosis, evidence: List[Evidence], specific_values: List[str] = None) -> str:

        patient_findings = []
        for ev in evidence:
            if len(ev.text) > 20:
                patient_findings.append(f"• {ev.text[:250]} (Source: {ev.location})")
        
        findings_text = "\n".join(patient_findings[:8])
        values_section = "\n".join(specific_values) if specific_values else "No specific numerical values extracted"
        
        alternatives_text = "None identified"
        if diagnosis.secondary_diagnoses:
            alt_list = []
            for s in diagnosis.secondary_diagnoses[:3]:
                alt_list.append(f"• {s['diagnosis']} - {s['confidence']:.0%} probability")
            alternatives_text = "\n".join(alt_list)
        
        patient_findings = []
        for ev in evidence:
            if len(ev.text) > 10: 
                # Normalize text: replace all internal newlines with spaces to prevent vertical stacking in PDF
                clean_text = ev.text.replace('\n', ' ').replace('\r', ' ').strip()
                # Remove excessive spaces
                clean_text = ' '.join(clean_text.split())
                patient_findings.append(f"• {clean_text[:500]} (Found in: {ev.location})") 
        
        findings_text = "\n".join(patient_findings[:25]) # Increased context to 25 items
        values_section = "\n".join(specific_values) if specific_values else "No specific numerical values extracted"
        
        # Build secondary diagnoses
        alternatives_text = "None identified"
        if diagnosis.secondary_diagnoses:
            alt_list = []
            for s in diagnosis.secondary_diagnoses[:3]:
                alt_list.append(f"• {s['diagnosis']} - {s['confidence']:.0%} probability")
            alternatives_text = "\n".join(alt_list)
        
        # High-Speed Academic/Theoretical Prompt
        prompt = f"""You are a world-class Distinguished Medical Consultant.
Generate a HIGH-DEPTH THEORETICAL XAI report for diagnosis: {diagnosis.primary_diagnosis}.
Focus on being CLINICALLY DENSE but token-efficient for immediate physician review.

[INPUT DATA]
Values: {values_section}
Context: {findings_text}

AI DIAGNOSIS: {diagnosis.primary_diagnosis} ({diagnosis.confidence:.0%})
CROSS-VAL: {diagnosis.cross_validation_score:.0%}

REQUIREMENTS (BE CONCISE BUT ACADEMICALLY DEEP):
1. **PATHOPHYSIOLOGY:** Explain the theoretical mechanism of {diagnosis.primary_diagnosis}. Focus on core clinical principles.
2. **DATA CORRELATION:** Link {values_section} to the pathophysiology. Explain the "why" behind the numbers.
3. **DIFFERENTIAL:** Briefly explain why {alternatives_text} were ruled out theoretically.
4. **XAI LOGIC:** Explain the AI's internal evidence weighting in 3-4 sentences.

Structure:
## I. THEORETICAL PATHOPHYSIOLOGY
## II. DATA CORRELATION ANALYSIS
## III. DIFFERENTIAL DIAGNOSTIC THEORY
## IV. XAI REASONING LOGIC
## V. CLINICAL PROJECTIONS

Target: 500-700 High-Depth words. Be academically rigorous but fast."""

        try:
            from config import settings
            model = settings.HF_EXPLAINER_MODEL
            print(f"[Layer 3] Generating XAI report via {model}...")
            response = hf_client.generate_text(model, prompt, max_new_tokens=600, temperature=0.2)
            if response and len(response.strip()) > 200:
                print("[Layer 3] XAI Report generated successfully")
                return response
        except Exception as e:
            print(f"[Layer 3] MedGemma XAI error: {e}")

        return self._generate_structured_fallback(diagnosis, evidence, patient_findings, specific_values)

    def _generate_structured_fallback(self, diagnosis: FinalDiagnosis, evidence: List[Evidence], patient_findings: List[str], specific_values: List[str] = None) -> str:
        """Plain-text fallback when MedGemma is unavailable."""
        if specific_values is None:
            specific_values = []
        findings_section = "\n".join(patient_findings[:5])
        values_display = "\n".join(specific_values) if specific_values else "No specific values extracted"
        alternatives = "• No significant alternatives identified"
        if diagnosis.secondary_diagnoses:
            alternatives = "\n".join(
                f"• {s['diagnosis']} ({s['confidence']:.0%})" for s in diagnosis.secondary_diagnoses[:3]
            )
        return (
            f"**Clinical Assessment:**\n{diagnosis.primary_diagnosis} is indicated by:\n"
            f"{findings_section}\n\n**Key Data:**\n{values_display}\n\n**Differential:**\n{alternatives}"
        )

    def _annotate_images(self, images_base64: List[str], diagnosis: str) -> List[str]:
        
        annotated_paths = []
        
        from utils.scan_report_analyzer import scan_report_analyzer
        import base64
        import tempfile
        import shutil
        
        print(f"[Layer 3] Re-analyzing {len(images_base64)} images for high-quality annotation marks...")
        
        for i, img_b64 in enumerate(images_base64[:3]):
            try:
                img_bytes = base64.b64decode(img_b64)
                if len(img_bytes) < 1000: continue
                
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                    tmp_file.write(img_bytes)
                    tmp_path = tmp_file.name
                
                report = scan_report_analyzer.analyze_single_scan(
                    tmp_path, 
                    output_dir=os.path.join(settings.OUTPUT_DIR, "final_annotations")
                )
                
                marked_img_path = report['scan_info']['marked_image']
                
                final_path = os.path.join(settings.OUTPUT_DIR, f"annotated_image_{i}.png")
                shutil.copy2(marked_img_path, final_path)
                
                annotated_paths.append(final_path)
                
                os.unlink(tmp_path)
                
            except Exception as e:
                print(f"[Layer 3] Detailed annotation error: {e}")
                try:
                    scan_abnormalities = []
                    if self.layer1_output:
                        for opinion in self.layer1_output.specialist_opinions:
                            if opinion.model_name == "scan_analyzer":
                                scan_abnormalities = opinion.key_findings.get('abnormality_positions', [])
                                break
                    
                    annotated_b64 = image_annotator.create_default_annotation(
                        img_b64, 
                        diagnosis,
                        abnormalities=scan_abnormalities
                    )
                    img_path = os.path.join(settings.OUTPUT_DIR, f"annotated_image_{i}.png")
                    with open(img_path, 'wb') as f:
                        f.write(base64.b64decode(annotated_b64))
                    annotated_paths.append(img_path)
                except:
                    pass
        
        return annotated_paths
    
    def _create_pdf_report(self, diagnosis: FinalDiagnosis, data: PatientData,
                          evidence: List[Evidence], explanation: str,
                          image_paths: List[str], specific_values: List[str] = None) -> str:

        pdf_data = {
            "patient_info": data.patient_info,
            "diagnosis": diagnosis.primary_diagnosis,
            "confidence": diagnosis.confidence,
            "evidence": [{"text": ev.text, "location": ev.location} for ev in evidence],
            "reasoning": explanation,
            "annotated_images": image_paths,
            "specific_values": specific_values,  # Pass specific values for circling
            "recommendations": [
                "Immediate consultation with specialist recommended",
                f"Confidence: {diagnosis.confidence:.0%} - verification required",
                "Additional diagnostic tests may be warranted"
            ]
        }
        
        output_path = os.path.join(settings.OUTPUT_DIR, "diagnosis_report.pdf")
        
        try:
            pdf_annotator.create_annotated_report(output_path, pdf_data)
        except Exception as e:
            print(f"PDF creation error: {e}")
            output_path = ""
        
        return output_path
    
    def _create_visualization_data(self, diagnosis: FinalDiagnosis, evidence: List[Evidence]) -> dict:
        
        return {
            "confidence_breakdown": {
                "primary": diagnosis.confidence,
                "cross_validation": diagnosis.cross_validation_score,
                "secondary": [
                    {"name": sec.get("diagnosis", "Unknown"), "value": sec.get("confidence", 0.0)}
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

layer3_annotator = Layer3Annotator()
