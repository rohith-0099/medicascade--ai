
import cv2
import numpy as np
import base64
from typing import Dict, Any, List

class MedicalImageAnalyzer:

    def __init__(self):
        print("✅ Medical Image Analyzer initialized (OpenCV Enhanced Mode)")
    
    def analyze_medical_image(self, img_base64: str) -> Dict[str, Any]:
        
        try:
            img_bytes = base64.b64decode(img_base64)
            nparr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
            
            if img is None:
                return {"total_findings": 0, "abnormality_positions": []}

            blurred = cv2.GaussianBlur(img, (5, 5), 0)
            
            thresh = cv2.adaptiveThreshold(
                blurred, 
                255, 
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY_INV,
                11,
                2
            )
            
            kernel = np.ones((3,3), np.uint8)
            opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)
            closing = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, kernel, iterations=2)
            
            contours, _ = cv2.findContours(closing, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            abnormal_positions = []
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if 100 < area < (img.shape[0] * img.shape[1] * 0.9): 
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

medical_image_analyzer = MedicalImageAnalyzer()
