
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
        self.width = max(len(text) * 8 + 20, 60)
        self.height = 30

    def draw(self):
        self.canv.setStrokeColor(red)
        self.canv.setLineWidth(2)
        self.canv.ellipse(0, 0, self.width, self.height)
        
        self.canv.setFillColor(HexColor('#000000'))
        self.canv.setFont("Helvetica-Bold", 12)
        self.canv.drawCentredString(self.width/2, self.height/2 - 4, self.text)

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
        
        doc = SimpleDocTemplate(output_path, pagesize=letter)
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
                    value = value.strip()
                    
                    value_circle = CircledTextFlowable(value)
                    
                    label_para = Paragraph(f"<b>{label}:</b>", self.styles['Normal'])
                    table_data.append([label_para, value_circle])
            
            if table_data:
                col_widths = [250, 200]
                t = Table(table_data, colWidths=col_widths)
                
                t.setStyle(TableStyle([
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                    ('ALIGN', (0,0), (0,-1), 'RIGHT'),  # Label right aligned
                    ('ALIGN', (1,0), (1,-1), 'LEFT'),   # Value left aligned
                    ('LEFTPADDING', (1,0), (1,-1), 15), # Space between label and value
                    ('BOTTOMPADDING', (0,0), (-1,-1), 10), # Vertical spacing between rows
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
        
        lines = reasoning.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
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
