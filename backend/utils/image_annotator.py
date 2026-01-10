"""
Image annotation utilities for Layer 3
Uses OpenCV to draw annotations on medical images
"""
import cv2
import numpy as np
import base64
from PIL import Image
import io
from typing import List, Tuple


class ImageAnnotator:
    """Annotates medical images with findings"""
    
    def __init__(self):
        self.colors = {
            "red": (0, 0, 255),
            "green": (0, 255, 0),
            "blue": (255, 0, 0),
            "yellow": (0, 255, 255),
            "orange": (0, 165, 255)
        }
    
    def annotate_image(self, image_base64: str, annotations: List[dict]) -> str:
        """
        Annotate image with markers
        
        Args:
            image_base64: Base64 encoded image
            annotations: List of annotation dicts with 'type', 'position', 'text'
            
        Returns:
            Base64 encoded annotated image
        """
        try:
            # Decode base64 to image
            img_bytes = base64.b64decode(image_base64)
            img_pil = Image.open(io.BytesIO(img_bytes))
            img_array = np.array(img_pil)
            
            # Convert RGB to BGR for OpenCV
            if len(img_array.shape) == 3:
                img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            else:
                img_bgr = cv2.cvtColor(img_array, cv2.COLOR_GRAY2BGR)
            
            # Apply annotations
            for annot in annotations:
                img_bgr = self._apply_annotation(img_bgr, annot)
            
            # Convert back to RGB
            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            img_pil_out = Image.fromarray(img_rgb)
            
            # Encode back to base64
            buffered = io.BytesIO()
            img_pil_out.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            return img_str
        
        except Exception as e:
            print(f"Image annotation error: {e}")
            return image_base64  # Return original on error
    
    def _apply_annotation(self, img: np.ndarray, annot: dict) -> np.ndarray:
        """Apply single annotation to image"""
        annot_type = annot.get("type", "text")
        color = self.colors.get(annot.get("color", "red"), self.colors["red"])
        
        if annot_type == "circle":
            center = annot.get("center", (img.shape[1] // 2, img.shape[0] // 2))
            radius = annot.get("radius", 50)
            thickness = annot.get("thickness", 3)
            cv2.circle(img, center, radius, color, thickness)
        
        elif annot_type == "box":
            x, y, w, h = annot.get("rect", (10, 10, 100, 100))
            cv2.rectangle(img, (x, y), (x + w, y + h), color, 3)
        
        elif annot_type == "arrow":
            start = annot.get("start", (50, 50))
            end = annot.get("end", (150, 150))
            cv2.arrowedLine(img, start, end, color, 3, tipLength=0.3)
        
        elif annot_type == "text":
            text = annot.get("text", "Annotation")
            position = annot.get("position", (50, 50))
            font_scale = annot.get("font_scale", 0.7)
            thickness = annot.get("thickness", 2)
            
            # Add background for better readability
            (text_width, text_height), baseline = cv2.getTextSize(
                text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness
            )
            cv2.rectangle(
                img,
                (position[0] - 5, position[1] - text_height - 5),
                (position[0] + text_width + 5, position[1] + baseline + 5),
                (0, 0, 0),
                -1
            )
            cv2.putText(img, text, position, cv2.FONT_HERSHEY_SIMPLEX,
                       font_scale, color, thickness, cv2.LINE_AA)
        
        return img
    
    def create_default_annotation(self, image_base64: str, diagnosis: str, abnormalities: list = None) -> str:
        """Add RED DOT at detected spots + diagnosis label"""
        try:
            # Decode to get image dimensions
            img_bytes = base64.b64decode(image_base64)
            img_pil = Image.open(io.BytesIO(img_bytes))
            width, height = img_pil.size
            
            annotations = []
            
            # If abnormalities detected, add RED DOTS at those spots
            if abnormalities and len(abnormalities) > 0:
                for abnorm in abnormalities[:3]:  # Max 3 dots
                    center = abnorm.get('center')
                    if center:
                        # Draw small RED DOT at detected location
                        annotations.append({
                            "type": "circle",
                            "center": center,
                            "radius": 8,  # Small dot
                            "color": "red",
                            "thickness": -1  # Filled circle (solid dot)
                        })
            
            # Add diagnosis label at top
            annotations.append({
                "type": "text",
                "text": diagnosis[:50],
                "position": (20, 40),
                "color": "green",
                "font_scale": 0.8,
                "thickness": 2
            })
            
            return self.annotate_image(image_base64, annotations)
        
        except Exception as e:
            print(f"Annotation error: {e}")
            return image_base64


# Global instance
image_annotator = ImageAnnotator()
