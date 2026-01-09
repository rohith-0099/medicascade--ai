"""
Medical Image Analyzer - Layer 1 Specialist
Analyzes X-rays, CT scans, and other medical imaging
"""
from utils.hf_client import hf_client
from config import settings
from schemas import SpecialistOpinion
import base64
from typing import List


class ScanAnalyzer:
    """Analyzes medical images"""
    
    def __init__(self):
        self.model = settings.HF_VISION_MODEL
        self.hf = hf_client
    
    def analyze(self, images_base64: List[str]) -> SpecialistOpinion:
        """
        Analyze medical images
        
        Args:
            images_base64: List of base64 encoded images
            
        Returns:
            SpecialistOpinion with findings
        """
        if not images_base64 or len(images_base64) == 0:
            return SpecialistOpinion(
                model_name="scan_analyzer",
                diagnosis="No medical images available",
                confidence=0.0,
                reasoning="No imaging data provided"
            )
        
        # Analyze first image (or could loop through all)
        findings = []
        confidences = []
        
        for i, img_b64 in enumerate(images_base64[:3]):  # Analyze up to 3 images
            try:
                # Decode base64 to bytes
                img_bytes = base64.b64decode(img_b64)
                
                # Query vision model
                result = self.hf.query_vision(self.model, img_bytes)
                
                if result:
                    findings.append(f"Image {i+1}: {result}")
                    confidences.append(0.7)  # Default confidence
            
            except Exception as e:
                print(f"Image analysis error: {e}")
                continue
        
        # Fallback if API doesn't work
        if not findings:
            return self._fallback_analysis(len(images_base64))
        
        # Combine findings
        diagnosis = self._interpret_findings(findings)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5
        reasoning = "\n".join(findings)
        
        return SpecialistOpinion(
            model_name="scan_analyzer",
            diagnosis=diagnosis,
            confidence=avg_confidence,
            reasoning=reasoning,
            detected_conditions=[diagnosis],
            key_findings={"num_images": len(images_base64), "findings": findings}
        )
    
    def _interpret_findings(self, findings: List[str]) -> str:
        """Interpret image analysis findings"""
        findings_text = " ".join(findings).lower()
        
        # Simple keyword matching
        if any(word in findings_text for word in ["tumor", "mass", "lesion", "abnormal"]):
            return "Abnormal Mass or Lesion Detected"
        elif any(word in findings_text for word in ["pneumonia", "infiltrate", "consolidation"]):
            return "Possible Pneumonia"
        elif any(word in findings_text for word in ["fracture", "break", "broken"]):
            return "Possible Fracture"
        elif any(word in findings_text for word in ["normal", "clear", "healthy"]):
            return "No Significant Abnormalities"
        else:
            return "Medical Image Analyzed (See Details)"
    
    def _fallback_analysis(self, num_images: int) -> SpecialistOpinion:
        """Fallback when vision API unavailable"""
        return SpecialistOpinion(
            model_name="scan_analyzer",
            diagnosis="Medical images require radiologist review",
            confidence=0.5,
            reasoning=f"{num_images} medical image(s) uploaded. Automated vision analysis unavailable - manual review recommended.",
            detected_conditions=["Pending Radiologist Review"],
            key_findings={"num_images": num_images, "status": "fallback"}
        )


# Global instance
scan_analyzer = ScanAnalyzer()
