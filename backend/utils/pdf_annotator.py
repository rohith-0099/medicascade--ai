"""
PDF annotation utilities for Layer 3
Highlights evidence in original PDF
"""
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import red, green, yellow, HexColor
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from typing import List, Dict, Any
import os


class PDFAnnotator:
    """Creates annotated PDF reports"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        
        # Create custom styles
        self.styles.add(ParagraphStyle(
            name='Highlight',
            parent=self.styles['Normal'],
            backColor=yellow,
            borderColor=red,
            borderWidth=1,
            borderPadding=5
        ))
        
        self.styles.add(ParagraphStyle(
            name='Evidence',
            parent=self.styles['Normal'],
            backColor=HexColor('#FFF3CD'),
            borderColor=HexColor('#FFC107'),
            borderWidth=2,
            borderPadding=8,
            leftIndent=10
        ))
        
        self.styles.add(ParagraphStyle(
            name='DiagnosisTitle',
            parent=self.styles['Heading1'],
            textColor=HexColor('#D32F2F'),
            fontSize=18,
            spaceAfter=12
        ))
    
    def create_annotated_report(self, output_path: str, data: Dict[str, Any]) -> str:
        """
        Create annotated PDF report
        
        Args:
            output_path: Where to save the PDF
            data: Dictionary with diagnosis, evidence, explanation, images
            
        Returns:
            Path to created PDF
        """
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        story = []
        
        # Title
        title = Paragraph("<b>Medical Diagnosis Report</b>", self.styles['Title'])
        story.append(title)
        story.append(Spacer(1, 0.3 * inch))
        
        # Patient Info
        patient_info = data.get("patient_info", {})
        if patient_info:
            info_text = f"<b>Patient:</b> {patient_info.get('name', 'Unknown')}<br/>"
            info_text += f"<b>Age:</b> {patient_info.get('age', 'Unknown')}<br/>"
            info_text += f"<b>Gender:</b> {patient_info.get('gender', 'Unknown')}"
            story.append(Paragraph(info_text, self.styles['Normal']))
            story.append(Spacer(1, 0.2 * inch))
        
        # Primary Diagnosis
        diagnosis = data.get("diagnosis", "Unknown")
        confidence = data.get("confidence", 0.0)
        
        diag_text = f"<b>PRIMARY DIAGNOSIS:</b><br/>{diagnosis}"
        story.append(Paragraph(diag_text, self.styles['DiagnosisTitle']))
        
        conf_text = f"<b>Confidence:</b> {confidence:.0%}"
        story.append(Paragraph(conf_text, self.styles['Heading3']))
        story.append(Spacer(1, 0.3 * inch))
        
        # Evidence Section
        story.append(Paragraph("<b>EVIDENCE FROM YOUR DATA:</b>", self.styles['Heading2']))
        story.append(Spacer(1, 0.1 * inch))
        
        evidence_items = data.get("evidence", [])
        for i, evidence in enumerate(evidence_items, 1):
            ev_text = f"<b>{i}. {evidence.get('location', 'Evidence')}:</b><br/>"
            ev_text += evidence.get('text', '')
            story.append(Paragraph(ev_text, self.styles['Evidence']))
            story.append(Spacer(1, 0.15 * inch))
        
        # Reasoning
        story.append(Paragraph("<b>CLINICAL REASONING:</b>", self.styles['Heading2']))
        reasoning = data.get("reasoning", "No reasoning provided")
        story.append(Paragraph(reasoning, self.styles['Normal']))
        story.append(Spacer(1, 0.3 * inch))
        
        # Annotated Images
        annotated_images = data.get("annotated_images", [])
        if annotated_images:
            story.append(PageBreak())
            story.append(Paragraph("<b>ANNOTATED MEDICAL IMAGES:</b>", self.styles['Heading2']))
            story.append(Spacer(1, 0.2 * inch))
            
            for img_path in annotated_images:
                if os.path.exists(img_path):
                    try:
                        img = RLImage(img_path, width=5*inch, height=4*inch)
                        story.append(img)
                        story.append(Spacer(1, 0.3 * inch))
                    except Exception as e:
                        print(f"Error adding image: {e}")
        
        # Recommendations
        story.append(PageBreak())
        story.append(Paragraph("<b>RECOMMENDATIONS:</b>", self.styles['Heading2']))
        
        recommendations = data.get("recommendations", [
            "Consult with a physician for professional medical advice",
            "This AI-generated report should not replace clinical judgment",
            "Further diagnostic tests may be required for confirmation"
        ])
        
        for rec in recommendations:
            story.append(Paragraph(f"• {rec}", self.styles['Normal']))
            story.append(Spacer(1, 0.1 * inch))
        
        # Disclaimer
        story.append(Spacer(1, 0.3 * inch))
        disclaimer = "<i><b>DISCLAIMER:</b> This report is generated by an AI system and should be reviewed by qualified medical professionals. It is not a substitute for professional medical diagnosis or treatment.</i>"
        story.append(Paragraph(disclaimer, self.styles['Normal']))
        
        # Build PDF
        doc.build(story)
        
        return output_path


# Global instance
pdf_annotator = PDFAnnotator()
