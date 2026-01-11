
import cv2
import numpy as np
from pathlib import Path
import json
from datetime import datetime
import os

class ScanReportAnalyzer:

    def __init__(self):
        self.scan_types = {
            'brain': ['mri', 'ct_head', 'brain'],
            'chest': ['x-ray', 'chest', 'lung'],
            'abdomen': ['ct_abdomen', 'ultrasound']
        }
    
    def analyze_single_scan(self, scan_path: str, scan_type=None, output_dir="backend/outputs/scan_reports"):

        img = cv2.imread(str(scan_path))
        if img is None:
            return {"error": f"Could not load scan: {scan_path}"}
        
        original = img.copy()
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        if scan_type is None:
            scan_type = self._detect_scan_type(img)
        
        print(f"\n{'='*60}")
        print(f"[SCAN ANALYSIS] {Path(scan_path).name}")
        print(f"[TYPE] {scan_type.upper()}")
        print(f"{'='*60}\n")
        
        enhanced = self._enhance_medical_image(gray)
        
        abnormalities = self._detect_abnormalities(enhanced, gray, scan_type)
        
        ml_probability = 0.0
        
        marked_image = self._draw_red_circles(original, abnormalities, ml_probability)
        
        report = self._generate_scan_report(
            scan_path, 
            scan_type, 
            abnormalities,
            marked_image,
            output_dir,
            ml_probability
        )
        
        return report
    
    def _enhance_medical_image(self, gray_image):

        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray_image)
        
        denoised = cv2.fastNlMeansDenoising(enhanced, h=10)
        
        return denoised
    
    def _detect_abnormalities(self, enhanced, original_gray, scan_type):

        abnormalities = []
        
        h, w = enhanced.shape
        circles = cv2.HoughCircles(
            enhanced,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=100,
            param1=50,
            param2=45,
            minRadius=20,
            maxRadius=140
        )
        
        if circles is not None:
            circles = np.uint16(np.around(circles))
            
            for idx, (x, y, r) in enumerate(circles[0]):
                x, y, r = int(x), int(y), int(r)
                
                if x < r or y < r or x > w-r or y > h-r:
                    continue
                
                mask = np.zeros(original_gray.shape, dtype=np.uint8)
                cv2.circle(mask, (x, y), r, 255, -1)
                
                roi = enhanced[mask > 0]
                if roi.size == 0: continue
                
                mean_intensity = np.mean(roi)
                std_intensity = np.std(roi)
                
                roi_region = enhanced[max(0, y-r):min(h, y+r),
                                     max(0, x-r):min(w, x+r)]
                
                edge_density = 0
                if roi_region.size > 0:
                    edges = cv2.Canny(roi_region, 50, 150)
                    edge_density = np.sum(edges > 0) / edges.size
                
                finding = self._classify_finding(
                    mean_intensity, 
                    std_intensity, 
                    edge_density,
                    scan_type
                )
                
                if finding['is_abnormal']:
                    abnormalities.append({
                        'id': len(abnormalities) + 1,
                        'type': finding['type'],
                        'location': (int(x), int(y)),
                        'radius': int(r),
                        'size_mm': int(r * 0.5),  # Approximate
                        'intensity': float(mean_intensity),
                        'texture_score': float(std_intensity),
                        'edge_density': float(edge_density),
                        'confidence': finding['confidence'],
                        'severity': finding['severity'],
                        'description': finding['description']
                    })
        
        bright_spots = self._detect_intensity_anomalies(enhanced, 'bright')
        dark_spots = self._detect_intensity_anomalies(enhanced, 'dark')
        
        for spot in bright_spots + dark_spots:
            is_duplicate = any(
                np.sqrt((spot['x'] - a['location'][0])**2 + 
                       (spot['y'] - a['location'][1])**2) < 50
                for a in abnormalities
            )
            
            if not is_duplicate:
                abnormalities.append({
                    'id': len(abnormalities) + 1,
                    'type': spot['type'],
                    'location': (spot['x'], spot['y']),
                    'radius': spot['radius'],
                    'size_mm': spot['radius'] * 0.5,
                    'intensity': spot['intensity'],
                    'confidence': spot['confidence'],
                    'severity': spot['severity'],
                    'description': spot['description']
                })
        
        severity_map = {'High': 3, 'Medium': 2, 'Low': 1, 'None': 0}
        abnormalities.sort(key=lambda x: (severity_map.get(x['severity'], 0), x['confidence']), reverse=True)
        
        final_list = []
        for abn in abnormalities:
            if len(final_list) >= 3:
                break
            if abn['severity'] == 'Low' and len(abnormalities) > 3:
                continue
                
            final_list.append(abn)
            
        for i, abn in enumerate(final_list):
            abn['id'] = i + 1
            
        return final_list
    
    def _classify_finding(self, intensity, std, edge_density, scan_type):

        finding = {
            'is_abnormal': False,
            'type': 'Normal',
            'confidence': 0.0,
            'severity': 'None',
            'description': ''
        }
        
        if intensity > 175:
            finding = {
                'is_abnormal': True,
                'type': 'Bright Mass',
                'confidence': min((intensity - 175) / 80 + 0.6, 0.95),
                'severity': 'High' if intensity > 200 else 'Medium',
                'description': 'Hyperintense region suggestive of mass lesion'
            }
        
        elif intensity < 55:
            finding = {
                'is_abnormal': True,
                'type': 'Hypodense Region',
                'confidence': min((55 - intensity) / 55 + 0.5, 0.90),
                'severity': 'High' if intensity < 35 else 'Medium',
                'description': 'Hypodense area - possible hemorrhage or cystic lesion'
            }
        
        elif std > 45:
            finding = {
                'is_abnormal': True,
                'type': 'Irregular Texture',
                'confidence': min(std / 80 + 0.5, 0.85),
                'severity': 'Medium',
                'description': 'Heterogeneous texture pattern - further evaluation needed'
            }
        
        elif edge_density > 0.15:
            finding = {
                'is_abnormal': True,
                'type': 'Well-Defined Mass',
                'confidence': min(edge_density * 4 + 0.4, 0.88),
                'severity': 'Medium',
                'description': 'Circumscribed mass with defined borders'
            }
        
        return finding
    
    def _detect_intensity_anomalies(self, enhanced, anomaly_type='bright'):

        if anomaly_type == 'bright':
            _, thresh = cv2.threshold(enhanced, 180, 255, cv2.THRESH_BINARY)
        else:
            _, thresh = cv2.threshold(enhanced, 50, 255, cv2.THRESH_BINARY_INV)
        
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        spots = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if 100 < area < 5000:
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    
                    radius = int(np.sqrt(area / np.pi))
                    
                    mask = np.zeros(enhanced.shape, dtype=np.uint8)
                    cv2.drawContours(mask, [contour], -1, 255, -1)
                    intensity = cv2.mean(enhanced, mask=mask)[0]
                    
                    spots.append({
                        'x': cx,
                        'y': cy,
                        'radius': radius,
                        'intensity': intensity,
                        'type': f'{anomaly_type.capitalize()} Spot',
                        'confidence': 0.65,
                        'severity': 'Low',
                        'description': f'{anomaly_type.capitalize()} intensity anomaly'
                    })
        
        return spots
    
    def _draw_red_circles(self, image, abnormalities, ml_probability=0.0):

        marked = image.copy()
        
        cv2.rectangle(marked, (0, 0), (image.shape[1], 60), (0, 0, 0), -1)
        header_text = f"SCAN ANALYSIS - {len(abnormalities)} Finding(s)"
        cv2.putText(marked, header_text, (10, 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        for abn in abnormalities:
            x, y = abn['location']
            r = abn['radius']
            
            if abn['severity'] == 'High':
                color = (0, 0, 255)
                thickness = 4
            elif abn['severity'] == 'Medium':
                color = (0, 165, 255)
                thickness = 3
            else:
                color = (0, 255, 255)
                thickness = 2
            
            circle_radius = int(r * 1.3)
            cv2.circle(marked, (x, y), circle_radius, color, thickness)
            
            cv2.line(marked, (x-10, y), (x+10, y), color, 2)
            cv2.line(marked, (x, y-10), (x, y+10), color, 2)
            
            arrow_start = (x, y - circle_radius - 25)
            arrow_end = (x, y - circle_radius - 5)
            cv2.arrowedLine(marked, arrow_start, arrow_end, color, 2, tipLength=0.3)
            
            label = f"#{abn['id']}: {abn['type']}"
            (label_w, label_h), baseline = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2
            )
            
            cv2.rectangle(
                marked,
                (x - label_w//2 - 5, y - circle_radius - 50),
                (x + label_w//2 + 5, y - circle_radius - 28),
                color,
                -1
            )
            
            cv2.putText(
                marked,
                label,
                (x - label_w//2, y - circle_radius - 33),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                2
            )
            
            conf_text = f"{abn['confidence']:.0%}"
            cv2.putText(
                marked,
                conf_text,
                (x - 15, y + 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                color,
                1
            )
        
        return marked
    
    def _detect_scan_type(self, image):

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        
        circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, 100, param1=50, param2=30)
        if circles is not None and len(circles[0]) > 0:
            return 'brain'
        
        aspect_ratio = h / w
        if 0.9 < aspect_ratio < 1.4:
            return 'chest'
        
        return 'general'
    
    def _generate_scan_report(self, scan_path, scan_type, abnormalities, marked_image, output_dir, ml_probability=0.0):

        scan_name = Path(scan_path).stem
        save_dir = Path(output_dir)
        save_dir.mkdir(parents=True, exist_ok=True)
        
        marked_path = save_dir / f"{scan_name}_marked.jpg"
        cv2.imwrite(str(marked_path), marked_image)
        
        report = {
            'scan_info': {
                'original_file': str(scan_path),
                'scan_type': scan_type,
                'analyzed_at': datetime.now().isoformat(),
                'marked_image': str(marked_path)
            },
            'summary': {
                'total_findings': len(abnormalities),
                'high_severity': sum(1 for a in abnormalities if a['severity'] == 'High'),
                'medium_severity': sum(1 for a in abnormalities if a['severity'] == 'Medium'),
                'low_severity': sum(1 for a in abnormalities if a['severity'] == 'Low')
            },
            'findings': abnormalities
        }
        
        report_path = save_dir / f"{scan_name}_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        print(f"✅ Report saved to: {report_path}")
        print(f"✅ Marked image saved to: {marked_path}")
        
        return report

scan_report_analyzer = ScanReportAnalyzer()
