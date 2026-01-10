"""
Medical Image Analyzer - Simple CV-based detection
"""
import cv2
import numpy as np
import base64
from typing import Dict, Any, List


class MedicalImageAnalyzer:
    """Fast medical image analysis using OpenCV"""
    
    def __init__(self):
        print("✅ Medical Image Analyzer initialized (OpenCV Enhanced Mode)")
    
    def analyze_medical_image(self, img_base64: str) -> Dict[str, Any]:
        """
        Analyze medical image for abnormalities
        Returns dict with findings and positions
        """
        try:
            # Decode base64 image
            img_bytes = base64.b64decode(img_base64)
            nparr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
            
            if img is None:
                return {"total_findings": 0, "abnormality_positions": []}
            
            # Simple threshold-based detection
            # Find bright regions (potential abnormalities)
            _, thresh = cv2.threshold(img, 200, 255, cv2.THRESH_BINARY)
            
            # Find contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filter significant contours
            abnormal_positions = []
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area > 50:  # Minimum size threshold
                    M = cv2.moments(cnt)
                    if M["m00"] != 0:
                        cx = int(M["m10"] / M["m00"])
                        cy = int(M["m01"] / M["m00"])
                        abnormal_positions.append({"x": cx, "y": cy, "area": int(area)})
            
            return {
                "total_findings": len(abnormal_positions),
                "abnormality_positions": abnormal_positions
            }
            
        except Exception as e:
            print(f"Image analysis error: {e}")
            return {"total_findings": 0, "abnormality_positions": []}


# Global instance
medical_image_analyzer = MedicalImageAnalyzer()
