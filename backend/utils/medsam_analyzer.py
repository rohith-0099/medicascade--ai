
import numpy as np
import cv2
from pathlib import Path
from typing import List, Dict, Tuple
import os

class MedSAMAnalyzer:

    def __init__(self, model_path: str = None):
        
        self.model = None
        self.predictor = None
        print("✅ Medical Image Analyzer initialized (OpenCV Enhanced Mode)")
    
    def analyze_image(self, image_path: str) -> List[Dict]:
        
        try:
            image = cv2.imread(image_path)
            if image is None:
                return []
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            abnormalities = []
            
            dark_regions = self._detect_dark_regions(gray)
            abnormalities.extend(dark_regions)
            
            bright_regions = self._detect_bright_regions(gray)
            abnormalities.extend(bright_regions)
            
            edge_regions = self._detect_edges(gray)
            abnormalities.extend(edge_regions)
            
            abnormalities = self._filter_detections(abnormalities)
            
            print(f"  Detected {len(abnormalities)} potential abnormalities")
            return abnormalities
            
        except Exception as e:
            print(f"Image analysis error: {e}")
            return []
    
    def _detect_dark_regions(self, gray_image: np.ndarray) -> List[Dict]:
        
        _, dark_mask = cv2.threshold(gray_image, 30, 255, cv2.THRESH_BINARY_INV)
        
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        dark_mask = cv2.morphologyEx(dark_mask, cv2.MORPH_CLOSE, kernel)
        dark_mask = cv2.morphologyEx(dark_mask, cv2.MORPH_OPEN, kernel)
        
        contours, _ = cv2.findContours(dark_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        detections = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 2000:
                x, y, w, h = cv2.boundingRect(contour)
                
                img_height, img_width = gray_image.shape
                if x < img_width * 0.1 or x + w > img_width * 0.9:
                    continue
                if y < img_height * 0.1 or y + h > img_height * 0.9:
                    continue
                
                detections.append({
                    'type': 'mass/tumor',  # Could be tumor
                    'bbox': (x, y, w, h),
                    'confidence': min(0.85, area / 10000),
                    'center': (x + w//2, y + h//2)
                })
        
        return detections
    
    def _detect_bright_regions(self, gray_image: np.ndarray) -> List[Dict]:
        
        _, bright_mask = cv2.threshold(gray_image, 230, 255, cv2.THRESH_BINARY)
        
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        bright_mask = cv2.morphologyEx(bright_mask, cv2.MORPH_CLOSE, kernel)
        
        contours, _ = cv2.findContours(bright_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        detections = []
        img_height, img_width = gray_image.shape
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 1500:
                x, y, w, h = cv2.boundingRect(contour)
                
                if x < img_width * 0.1 or x + w > img_width * 0.9:
                    continue
                if y < img_height * 0.1 or y + h > img_height * 0.9:
                    continue
                
                detections.append({
                    'type': 'calcification',
                    'bbox': (x, y, w, h),
                    'confidence': min(0.75, area / 8000),
                    'center': (x + w//2, y + h//2)
                })
        
        return detections
    
    def _detect_edges(self, gray_image: np.ndarray) -> List[Dict]:
        
        return []
    
    def _filter_detections(self, detections: List[Dict]) -> List[Dict]:
        
        if not detections:
            return []
        
        detections.sort(key=lambda x: x['confidence'], reverse=True)
        
        filtered = []
        for det in detections:
            overlap = False
            for existing in filtered:
                if self._boxes_overlap(det['bbox'], existing['bbox']):
                    overlap = True
                    break
            
            if not overlap:
                filtered.append(det)
        
        return filtered[:2]
    
    def _boxes_overlap(self, box1: Tuple, box2: Tuple, threshold: float = 0.3) -> bool:
        
        x1, y1, w1, h1 = box1
        x2, y2, w2, h2 = box2
        
        x_overlap = max(0, min(x1 + w1, x2 + w2) - max(x1, x2))
        y_overlap = max(0, min(y1 + h1, y2 + h2) - max(y1, y2))
        overlap_area = x_overlap * y_overlap
        
        area1 = w1 * h1
        area2 = w2 * h2
        union_area = area1 + area2 - overlap_area
        
        iou = overlap_area / union_area if union_area > 0 else 0
        
        return iou > threshold

medsam_analyzer = None

def get_medsam_analyzer():
    
    global medsam_analyzer
    if medsam_analyzer is None:
        medsam_analyzer = MedSAMAnalyzer()
    return medsam_analyzer
