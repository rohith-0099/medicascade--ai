
from schemas import SpecialistOpinion
from utils.medical_image_analyzer import medical_image_analyzer
from typing import List
import base64

class ScanAnalyzer:

    def __init__(self):
        self.model_name = "scan_analyzer"
        self.ai_model = "microsoft/BiomedCLIP-PubMedBERT_256"
    
    def analyze(self, images_base64: List[str]) -> SpecialistOpinion:
        
        if not images_base64 or len(images_base64) == 0:
            return SpecialistOpinion(
                model_name=self.model_name,
                diagnosis="No medical images provided",
                confidence=0.0,
                reasoning="No scan data available for analysis"
            )
        
        print(f"[Scan Analyzer] Analyzing {len(images_base64)} medical images using Advanced Engine...")
        
        all_findings = []
        total_abnormalities = 0
        abnormality_positions = []
        images_with_findings = 0
        
        from utils.scan_report_analyzer import scan_report_analyzer
        import base64
        import tempfile
        import os
        from config import settings
        
        for i, img_b64 in enumerate(images_base64):
            try:
                img_bytes = base64.b64decode(img_b64)
                if len(img_bytes) < 1000: continue
                
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                    tmp_file.write(img_bytes)
                    tmp_path = tmp_file.name
                
                report = scan_report_analyzer.analyze_single_scan(tmp_path, output_dir=os.path.join(settings.OUTPUT_DIR, "scan_reports"))
                
                findings_count = report['summary']['total_findings']
                
                if findings_count > 0:
                    total_abnormalities += findings_count
                    images_with_findings += 1
                    
                    descriptions = [f.get('type', 'Abnormality') for f in report['findings']]
                    finding_text = f"Image {i+1}: Found {findings_count} abnormalities ({', '.join(descriptions[:3])})"
                    all_findings.append(finding_text)
                    print(f"  {finding_text}")
                    
                    for f in report['findings']:
                        loc = f.get('location', (0,0))
                        abnormality_positions.append({
                            "x": loc[0],
                            "y": loc[1],
                            "area": f.get('size_mm', 0) * 10
                        })
                
                os.unlink(tmp_path)
                
            except Exception as e:
                print(f"[Scan Analyzer] Error analyzing image {i}: {e}")
                continue
        
        if total_abnormalities > 0:
            diagnosis = f"Suspicious mass detected - {total_abnormalities} region(s) identified"
            confidence = min(0.75 + (images_with_findings / 10), 0.95)
            reasoning = f"Advanced CV Analysis detected {total_abnormalities} significant regions of interest."
            
            return SpecialistOpinion(
                model_name=self.model_name,
                diagnosis=diagnosis,
                confidence=confidence,
                reasoning=reasoning,
                detected_conditions=all_findings[:10],
                key_findings={
                    "total_abnormalities": total_abnormalities,
                    "abnormality_positions": abnormality_positions[:100],
                    "detailed_report_available": True
                }
            )
        
        return SpecialistOpinion(
            model_name=self.model_name,
            diagnosis="No significant abnormalities detected in scans",
            confidence=0.85,
            reasoning="Advanced CV Analysis found no significant pathology.",
            key_findings={"abnormality_positions": []}
        )

scan_analyzer = ScanAnalyzer()
