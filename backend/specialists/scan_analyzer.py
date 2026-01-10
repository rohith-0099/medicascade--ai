"""
Scan Analyzer - Medical Image Analysis
"""
from schemas import SpecialistOpinion
from utils.medical_image_analyzer import medical_image_analyzer
from typing import List
import base64


class ScanAnalyzer:
    """Analyzes medical scan images"""
    
    def __init__(self):
        self.model_name = "scan_analyzer"
        self.ai_model = "microsoft/BiomedCLIP-PubMedBERT_256"
    
    def analyze(self, images_base64: List[str]) -> SpecialistOpinion:
        """Analyze medical images"""
        if not images_base64 or len(images_base64) == 0:
            return SpecialistOpinion(
                model_name=self.model_name,
                diagnosis="No medical images provided",
                confidence=0.0,
                reasoning="No scan data available for analysis"
            )
        
        print(f"[Scan Analyzer] Analyzing {len(images_base64)} medical images...")
        
        # Use medical image analyzer
        all_findings = []
        total_abnormalities = 0
        abnormality_positions = []
        images_with_findings = 0
        
        for i, img_b64 in enumerate(images_base64):
            # Skip if image is too small (likely not a medical image)
            try:
                img_bytes = len(img_b64)
                if img_bytes < 1000:  # Skip tiny images
                    continue
            except:
                continue
            
            result = medical_image_analyzer.analyze_medical_image(img_b64)
            
            findings_count = result.get('total_findings', 0)
            
            # Only count if there are significant findings (not just noise)
            if findings_count > 100:  # Threshold for actual abnormalities vs noise
                total_abnormalities += findings_count
                all_findings.append(f"Image {i+1}: {findings_count} abnormalities")
                images_with_findings += 1
                
                # Store positions for annotation
                positions = result.get('abnormality_positions', [])
                abnormality_positions.extend(positions)
                print(f"  Image {i+1}: Found {findings_count} abnormalities")
            else:
                print(f"  Image {i+1}: Found {findings_count} abnormalities")
        
        # If we found significant abnormalities
        if total_abnormalities > 500 and images_with_findings > 0:  # Meaningful threshold
            diagnosis = f"Suspicious mass detected - {total_abnormalities} bright region(s) identified"
            confidence = min(0.70 + (images_with_findings / 20), 0.90)
            reasoning = f"Detected abnormalities across {images_with_findings} images"
            
            return SpecialistOpinion(
                model_name=self.model_name,
                diagnosis=diagnosis,
                confidence=confidence,
                reasoning=reasoning,
                detected_conditions=all_findings[:5],
                key_findings={
                    "total_abnormalities": total_abnormalities,
                    "abnormality_positions": abnormality_positions[:100]  # Limit for JSON
                }
            )
        
        # No significant findings
        return SpecialistOpinion(
            model_name=self.model_name,
            diagnosis="No significant abnormalities detected in scans",
            confidence=0.70,
            reasoning="Medical images reviewed, no critical pathology identified",
            key_findings={"abnormality_positions": []}
        )


scan_analyzer = ScanAnalyzer()
