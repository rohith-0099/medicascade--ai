
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

    def __init__(self):
        self.ollama = ollama_client
    
    def process(self, diagnosis: FinalDiagnosis, patient_data: PatientData, layer1_output=None) -> AnnotatedReport:
        
        print("[Layer 3] Generating explanation and annotations...")
        start_time = time.time()
        
        self.layer1_output = layer1_output
        
        evidence_items = self._extract_evidence_fast(diagnosis, patient_data)
        print(f"[Layer 3] Extracted {len(evidence_items)} evidence items")
        
        specific_values = self._extract_specific_values(evidence_items)
        
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
    
    def _extract_specific_values(self, evidence: List[Evidence]) -> List[str]:
        
        specific_values = []
        import re
        
        for ev in evidence:
            text_lower = ev.text.lower()
            
            if 'blood pressure' in text_lower or 'bp' in text_lower or '/' in ev.text:
                bp_match = re.search(r'(\d{2,3})/(\d{2,3})', ev.text)
                if bp_match:
                    specific_values.append(f"**Blood Pressure:** {bp_match.group(0)} mmHg")
            
            if 'glucose' in text_lower:
                glucose_match = re.search(r'glucose[:\s]+(\d+)', text_lower)
                if glucose_match:
                    specific_values.append(f"**Glucose:** {glucose_match.group(1)} mg/dL")
            
            if 'temperature' in text_lower or 'temp' in text_lower:
                temp_match = re.search(r'(\d{2,3}\.?\d*)[°]?[fF]', ev.text)
                if temp_match:
                    specific_values.append(f"**Temperature:** {temp_match.group(1)}°F")
            
            if 'heart rate' in text_lower or 'hr' in text_lower:
                hr_match = re.search(r'(\d{2,3})\s*bpm', text_lower)
                if hr_match:
                    specific_values.append(f"**Heart Rate:** {hr_match.group(1)} bpm")
            
            generic_match = re.search(r'\*\*([A-Za-z0-9\s\-\(\)]+):\s*([0-9\.]+%?)\*\*', ev.text)
            if generic_match:
                label = generic_match.group(1).strip()
                val = generic_match.group(2).strip()
                if label.lower() not in ['blood pressure', 'glucose', 'temperature', 'heart rate']:
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
        
        return items[:8]
    
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
        
        # Enhanced prompt for Gemini
        prompt = f"""You are a medical AI writing a comprehensive diagnostic report for physicians. Analyze this diagnosis and explain it in detail.

SPECIFIC MEDICAL VALUES FOUND:
{values_section}

ALL PATIENT DATA ANALYZED:
{findings_text}

AI DIAGNOSIS: {diagnosis.primary_diagnosis}
AI CONFIDENCE: {diagnosis.confidence:.0%}
CROSS-VALIDATION: {diagnosis.cross_validation_score:.0%} agreement across 5 AI models

ALTERNATIVE DIAGNOSES CONSIDERED:
{alternatives_text}

Write a COMPREHENSIVE medical report with these sections:

## CLINICAL FINDINGS & KEY VALUES
[List the SPECIFIC medical values found (BP, glucose, temp, etc.) and summarize other findings. Be precise - cite exact numbers from the Patient Data.]

## DISEASE EXPLANATION
[Explain what {diagnosis.primary_diagnosis} is - definition, pathophysiology, typical presentation, clinical significance]

## CORRELATION WITH PATIENT DATA
[For EACH specific value found, explain how it supports or relates to {diagnosis.primary_diagnosis}. Example: "Blood Pressure of 190/110 mmHg indicates severe hypertension, a known risk factor for stroke." Be very specific - mention each value by name and number.]

## DIAGNOSTIC REASONING
[Explain the clinical logic: Given these specific findings, why is {diagnosis.primary_diagnosis} the most likely diagnosis? How do the findings fit the diagnostic criteria?]

## DIFFERENTIAL DIAGNOSIS
[Why were alternatives ruled out? What specific findings exclude other conditions?]

## CLINICAL RECOMMENDATIONS
[Based on this diagnosis and the specific values found, what immediate actions are needed? What tests? What treatments? Be specific and actionable.]

## CONFIDENCE & LIMITATIONS
[Why {diagnosis.confidence:.0%} confidence? What specific findings support this? What data is missing? What uncertainties remain?]

Use professional medical terminology. Be thorough and specific. ALWAYS cite exact values when discussing findings. Target audience is a doctor. Maximum 1000 words."""

        try:
            from utils.gemini_client import gemini_client
            print("[Layer 3] Attempting to generate explanation with Gemini 1.5 Flash...")
            
            response = gemini_client.generate_medical_explanation(prompt, max_tokens=1500)
            
            if response and len(response.strip()) > 200:
                formatted = response
                
                print(f"[Layer 3] Generated Gemini-powered clinical explanation with specific values")
                return formatted
                
        except Exception as e:
            print(f"[Layer 3] Gemini explanation error: {e}")
            
        try:
            response = self.ollama.generate(prompt, temperature=0.3, max_tokens=800)
            
            if response and len(response.strip()) > 200:
                formatted = response
                
                print(f"[Layer 3] Generated Ollama explanation with values")
                return formatted
        except:
            pass
        
        return self._generate_structured_fallback(diagnosis, evidence, patient_findings, specific_values)
    
    def _generate_structured_fallback(self, diagnosis: FinalDiagnosis, evidence: List[Evidence], patient_findings: List[str], specific_values: List[str] = None) -> str:

        if specific_values is None:
            specific_values = []
        
        findings_section = "\n".join(patient_findings[:5])
        values_display = "\n".join(specific_values) if specific_values else "No specific numerical values extracted from patient data"
        
        alternatives = ""
        if diagnosis.secondary_diagnoses:
            alt_items = []
            for s in diagnosis.secondary_diagnoses[:3]:
                alt_items.append(f"• {s['diagnosis']} ({s['confidence']:.0%})")
            alternatives = "\n".join(alt_items)
        else:
            alternatives = "• No significant alternative diagnoses identified"
        
        return f"**Clinical Assessment:**\\n{diagnosis.primary_diagnosis} is indicated by:\\n{findings_section}\\n\\n**Key Data:**\\n{values_display}\\n\\n**Differential:**\\n{alternatives}"

        prompt = f"Explain the medical diagnosis of {diagnosis.primary_diagnosis} given these symptoms:\\n{findings_section}"

        try:
            response = self.ollama.generate(prompt, temperature=0.3, max_tokens=300)
            
            if response and len(response.strip()) > 50:
                formatted = response
                print(f"[Layer 3] Generated disease explanation for: {diagnosis}")
                return formatted
        except Exception as e:
            print(f"[Layer 3] Disease explanation error: {e}")
        
        return f"Diagnosis: {diagnosis.primary_diagnosis}. Evidence: {findings_section}"
    
    def _generate_xai_explanation(self, diagnosis: FinalDiagnosis, evidence: List[Evidence]) -> str:

        evidence_list = []
        for ev in evidence[:5]:
            evidence_list.append(f"• {ev.text[:120]}")
        evidence_text = "\n".join(evidence_list)
        
        secondary_list = []
        for s in diagnosis.secondary_diagnoses[:3]:
            secondary_list.append(f"• {s['diagnosis']} ({s['confidence']:.0%} probability)")
        secondaries_text = "\n".join(secondary_list) if secondary_list else "None"
        
        prompt = f

        try:
            response = self.ollama.generate(prompt, temperature=0.4, max_tokens=600)
            
            if response and len(response.strip()) > 100:
                xai_output = f
                
                print("[Layer 3] Generated clear XAI explanation")
                return xai_output
        
        except Exception as e:
            print(f"[Layer 3] Ollama XAI error: {e}")
        
        return ""
    
    def _generate_fallback_explanation(self, diagnosis: FinalDiagnosis, evidence: List[Evidence]) -> str:

        evidence_bullets = []
        for ev in evidence[:4]:
            evidence_bullets.append(f"• {ev.text[:100]}...")
        
        secondary_text = ""
        if diagnosis.secondary_diagnoses and len(diagnosis.secondary_diagnoses) > 0:
            secondary_bullets = []
            for s in diagnosis.secondary_diagnoses[:3]:
                secondary_bullets.append(f"• {s['diagnosis']} - {s['confidence']:.0%} probability")
            secondary_text = f
        
        explanation = f

        return explanation
    
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
