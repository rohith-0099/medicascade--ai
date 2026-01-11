
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image as RLImage, Table, TableStyle
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
        # Thicker padding for clear circle visibility
        self.width = max(len(text) * 9 + 40, 80)
        self.height = 40

    def draw(self):
        # Draw bold red ellipse
        self.canv.setStrokeColor(red)
        self.canv.setLineWidth(3)  # Increased from 2 to 3 for better visibility
        # Draw ellipse with slight padding from boundaries
        self.canv.ellipse(2, 2, self.width - 2, self.height - 2)
        
        # Draw text bold and centered
        self.canv.setFillColor(black)
        self.canv.setFont("Helvetica-Bold", 14) # Larger font
        self.canv.drawCentredString(self.width/2, self.height/2 - 5, self.text)

class PDFAnnotator:
   
    def __init__(self):
        self.styles = getSampleStyleSheet()
        
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
        
        # Explicitly set margins to avoid layout squashing
        doc = SimpleDocTemplate(
            output_path, 
            pagesize=letter,
            rightMargin=50,
            leftMargin=50,
            topMargin=50,
            bottomMargin=50
        )
        story = []
        
        title = Paragraph("<b>Medical Diagnosis Report</b>", self.styles['Title'])
        story.append(title)
        story.append(Spacer(1, 0.3 * inch))
        
        patient_info = data.get("patient_info", {})
        if patient_info:
            info_text = f"<b>Patient:</b> {patient_info.get('name', 'Unknown')}<br/>"
            info_text += f"<b>Age:</b> {patient_info.get('age', 'Unknown')}<br/>"
            info_text += f"<b>Gender:</b> {patient_info.get('gender', 'Unknown')}"
            story.append(Paragraph(info_text, self.styles['Normal']))
            story.append(Spacer(1, 0.2 * inch))
        
        diagnosis = data.get("diagnosis", "Unknown")
        confidence = data.get("confidence", 0.0)
        
        diag_text = f"<b>PRIMARY DIAGNOSIS:</b><br/>{diagnosis}"
        story.append(Paragraph(diag_text, self.styles['DiagnosisTitle']))
        
        conf_text = f"<b>Confidence:</b> {confidence:.0%}"
        story.append(Paragraph(conf_text, self.styles['Heading3']))
        story.append(Spacer(1, 0.3 * inch))
        
        specific_values = data.get("specific_values", [])
        if specific_values:
            story.append(Paragraph("<b>🔴 KEY FINDINGS (Significant Data):</b>", self.styles['Heading2']))
            story.append(Spacer(1, 0.15 * inch))
            
            table_data = []
            
            for val in specific_values:
                clean_val = val.replace('**', '').replace('•', '').strip()
                if ':' in clean_val:
                    label, value = clean_val.split(':', 1)
                    label = label.strip()
                    value = value.strip()  # Crucial: remove leading space
                    
                    # Create the circled value flowable
                    value_circle = CircledTextFlowable(value)
                    
                    label_para = Paragraph(f"<b>{label}:</b>", self.styles['Normal'])
                    table_data.append([label_para, value_circle])
            
            if table_data:
                col_widths = [180, 200]
                t = Table(table_data, colWidths=col_widths)
                
                t.setStyle(TableStyle([
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                    ('ALIGN', (0,0), (0,-1), 'RIGHT'),  # Label right aligned
                    ('ALIGN', (1,0), (1,-1), 'LEFT'),   # Value left aligned
                    ('LEFTPADDING', (1,0), (1,-1), 15), # Space between label and value
                    ('BOTTOMPADDING', (0,0), (-1,-1), 20), # Increased vertical spacing for larger circles
                ]))
                
                story.append(t)
                story.append(Spacer(1, 0.2 * inch))

        evidence_items = data.get("evidence", [])
        
        lab_evidence = [e for e in evidence_items if "ABNORMAL" in e.get('location', '')]
        other_evidence = [e for e in evidence_items if "ABNORMAL" not in e.get('location', '')]
        
        if lab_evidence:
            story.append(Paragraph("<b>⚠️ ABNORMAL LAB VALUES (Triggered Diagnosis):</b>", self.styles['Heading2']))
            story.append(Spacer(1, 0.1 * inch))
            
            for evidence in lab_evidence:
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
        
        if other_evidence:
            story.append(Paragraph("<b>OTHER SUPPORTING EVIDENCE:</b>", self.styles['Heading2']))
            story.append(Spacer(1, 0.1 * inch))
            for i, evidence in enumerate(other_evidence, 1):
                ev_text = f"<b>{i}. {evidence.get('location', 'Evidence')}:</b><br/>"
                ev_text += evidence.get('text', '')
                story.append(Paragraph(ev_text, self.styles['Evidence']))
                story.append(Spacer(1, 0.15 * inch))
        
        story.append(PageBreak())
        story.append(Paragraph("<b>🧠 EXPLAINABLE AI (XAI) CLINICAL REASONING:</b>", self.styles['Heading1']))
        story.append(Spacer(1, 0.2 * inch))
        
        reasoning = data.get("reasoning", "No reasoning provided")
        
        # Define XAI styles with explicit alignment and NO side constraints
        xai_style = ParagraphStyle(
            name='XAI',
            parent=self.styles['Normal'],
            fontSize=11,
            leading=16,
            leftIndent=0,  # Reset indentation
            rightIndent=0, # Reset indentation
            alignment=TA_LEFT, # Explicit left alignment
            spaceAfter=8
        )
        
        xai_header_style = ParagraphStyle(
            name='XAIHeader',
            parent=self.styles['Heading2'], # Use Heading2 for better visibility
            textColor=HexColor('#1976D2'),
            fontSize=14,
            leftIndent=0,
            rightIndent=0,
            alignment=TA_LEFT,
            spaceAfter=10,
            spaceBefore=15
        )
        
        # Safety: Convert literal "\\n" used in older code to real newlines
        reasoning = reasoning.replace('\\n', '\n')
        
        lines = reasoning.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                story.append(Spacer(1, 0.1 * inch)) # Maintain spacing for empty lines
                continue
            
            # Additional safety: ensure text within a line doesn't have internal newlines
            # that might cause vertical stacking if misinterpreted elsewhere
            line = line.replace('\n', ' ').strip()
            
            if line.startswith('##') or line.startswith('**Step'):
                clean_line = line.replace('##', '').replace('**', '').strip()
                story.append(Paragraph(f"<b>{clean_line}</b>", xai_header_style))
            elif line.startswith('**'):
                clean_line = line.replace('**', '')
                story.append(Paragraph(f"<b>{clean_line}</b>", xai_style))
            elif line.startswith('-') or line.startswith('•'):
                clean_line = line[1:].strip()
                story.append(Paragraph(f"  • {clean_line}", xai_style))
            else:
                story.append(Paragraph(line, xai_style))
        
        story.append(Spacer(1, 0.3 * inch))
        
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
        
        story.append(Spacer(1, 0.3 * inch))
        disclaimer = "<i><b>DISCLAIMER:</b> This report is generated by an AI system and should be reviewed by qualified medical professionals. It is not a substitute for professional medical diagnosis or treatment.</i>"
        story.append(Paragraph(disclaimer, self.styles['Normal']))
        
        doc.build(story)
        
        return output_path

pdf_annotator = PDFAnnotator()
