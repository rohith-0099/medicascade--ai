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


from reportlab.platypus import Flowable
from reportlab.graphics.shapes import Drawing, Ellipse, String
from reportlab.lib.colors import red, black

class CircledTextFlowable(Flowable):
    def __init__(self, text):
        Flowable.__init__(self)
        self.text = text
        self.width = len(text) * 8 + 30
        self.height = 35

    def draw(self):
        # Draw red ellipse
        self.canv.setStrokeColor(red)
        self.canv.setLineWidth(2)
        self.canv.ellipse(0, 0, self.width, self.height)
        
        # Draw text
        self.canv.setFillColor(HexColor('#000000'))
        self.canv.setFont("Helvetica-Bold", 12)
        self.canv.drawCentredString(self.width/2, self.height/2 - 4, self.text)


class PDFAnnotator:
   
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
        Create annotated PDF report with CIRCLED KEY VALUES
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
        
        # --- NEW SECTION: CIRCLED KEY VALUES ---
        specific_values = data.get("specific_values", [])
        if specific_values:
            story.append(Paragraph("<b>🔴 KEY FINDINGS (Significant Data):</b>", self.styles['Heading2']))
            story.append(Spacer(1, 0.15 * inch))
            
            # Create a table-like layout for circled values or just verify flowables
            from reportlab.platypus import Table, TableStyle
            
            # Extract just the value part if possible, or circle the whole line
            circled_items = []
            for val in specific_values:
                # Clean up markdown bold
                clean_val = val.replace('**', '').replace('•', '').strip()
                if ':' in clean_val:
                    # Circle the value part
                    label, value = clean_val.split(':', 1)
                    full_text = f"{label}: {value.strip()}"
                    circled_items.append(CircledTextFlowable(full_text))
            
            if circled_items:
                # Add flowed circled items
                for item in circled_items:
                    story.append(item)
                    story.append(Spacer(1, 0.2 * inch))
            
            story.append(Spacer(1, 0.2 * inch))
        
        
        # Evidence Section - ABNORMAL LAB VALUES FIRST
        evidence_items = data.get("evidence", [])
        
        # Separate lab values from other evidence
        lab_evidence = [e for e in evidence_items if "ABNORMAL" in e.get('location', '')]
        other_evidence = [e for e in evidence_items if "ABNORMAL" not in e.get('location', '')]
        
        # Show abnormal labs FIRST with RED highlighting
        if lab_evidence:
            story.append(Paragraph("<b>⚠️ ABNORMAL LAB VALUES (Triggered Diagnosis):</b>", self.styles['Heading2']))
            story.append(Spacer(1, 0.1 * inch))
            
            for evidence in lab_evidence:
                # Red highlighted box for each abnormal lab
                lab_style = ParagraphStyle(
                    name='LabAlert',
                    parent=self.styles['Normal'],
                    backColor=HexColor('#FFCCCC'),  # Light red
                    borderColor=red,
                    borderWidth=3,
                    borderPadding=10,
                    fontSize=13,
                    textColor=HexColor('#CC0000'),  # Dark red text
                    fontName='Helvetica-Bold'
                )
                ev_text = evidence.get('text', '')
                story.append(Paragraph(ev_text, lab_style))
                story.append(Spacer(1, 0.15 * inch))
        
        # Other evidence
        if other_evidence:
            story.append(Paragraph("<b>OTHER SUPPORTING EVIDENCE:</b>", self.styles['Heading2']))
            story.append(Spacer(1, 0.1 * inch))
            for i, evidence in enumerate(other_evidence, 1):
                ev_text = f"<b>{i}. {evidence.get('location', 'Evidence')}:</b><br/>"
                ev_text += evidence.get('text', '')
                story.append(Paragraph(ev_text, self.styles['Evidence']))
                story.append(Spacer(1, 0.15 * inch))
        
        # XAI Clinical Reasoning - FULL DISPLAY
        story.append(PageBreak())  # New page for XAI reasoning
        story.append(Paragraph("<b>🧠 EXPLAINABLE AI (XAI) CLINICAL REASONING:</b>", self.styles['Heading1']))
        story.append(Spacer(1, 0.2 * inch))
        
        reasoning = data.get("reasoning", "No reasoning provided")
        
        # Parse and format XAI sections
        xai_style = ParagraphStyle(
            name='XAI',
            parent=self.styles['Normal'],
            fontSize=11,
            leading=16,
            leftIndent=15,
            spaceAfter=8
        )
        
        xai_header_style = ParagraphStyle(
            name='XAIHeader',
            parent=self.styles['Heading3'],
            textColor=HexColor('#1976D2'),
            fontSize=13,
            spaceAfter=6,
            spaceBefore=10
        )
        
        # Split reasoning by sections and format each
        lines = reasoning.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Headers (## or **Step)
            if line.startswith('##') or line.startswith('**Step'):
                clean_line = line.replace('##', '').replace('**', '').strip()
                story.append(Paragraph(f"<b>{clean_line}</b>", xai_header_style))
            # Bold sections
            elif line.startswith('**'):
                clean_line = line.replace('**', '')
                story.append(Paragraph(f"<b>{clean_line}</b>", xai_style))
            # List items
            elif line.startswith('-') or line.startswith('•'):
                clean_line = line[1:].strip()
                story.append(Paragraph(f"  • {clean_line}", xai_style))
            # Normal text
            else:
                story.append(Paragraph(line, xai_style))
        
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
