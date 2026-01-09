"""
Create sample patient PDF for testing
"""
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors
import os


def create_sample_patient_pdf():
    """Create a realistic sample patient PDF"""
    
    output_path = "/home/rohith/medicascade-ai/demo/sample_patient.pdf"
    os.makedirs("/home/rohith/medicascade-ai/demo", exist_ok=True)
    
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title = Paragraph("<b>PATIENT MEDICAL REPORT</b>", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 0.3 * inch))
    
    # Patient Demographics
    story.append(Paragraph("<b>Patient Information</b>", styles['Heading2']))
    demo_data = [
        ["Name:", "John Doe"],
        ["Age:", "58 years"],
        ["Gender:", "Male"],
        ["Patient ID:", "MRN-123456"],
        ["Date:", "January 9, 2026"]
    ]
    demo_table = Table(demo_data, colWidths=[2*inch, 4*inch])
    demo_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
    ]))
    story.append(demo_table)
    story.append(Spacer(1, 0.3 * inch))
    
    # Chief Complaint / Symptoms
    story.append(Paragraph("<b>Chief Complaint</b>", styles['Heading2']))
    symptoms = """Patient presents with severe chest pain radiating to left arm for past 3 hours. 
Reports shortness of breath, nausea, and excessive sweating. Pain described as crushing sensation, 
rated 8/10 in intensity. Patient has history of hypertension and smoking (20 pack-years)."""
    story.append(Paragraph(symptoms, styles['Normal']))
    story.append(Spacer(1, 0.3 * inch))
    
    # Vital Signs
    story.append(Paragraph("<b>Vital Signs</b>", styles['Heading2']))
    vitals_data = [
        ["Parameter", "Value", "Normal Range"],
        ["Blood Pressure", "165/95 mmHg", "120/80 mmHg"],
        ["Heart Rate", "102 bpm", "60-100 bpm"],
        ["Temperature", "98.8°F", "97-99°F"],
        ["Respiratory Rate", "22/min", "12-20/min"],
    ]
    vitals_table = Table(vitals_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
    vitals_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(vitals_table)
    story.append(Spacer(1, 0.3 * inch))
    
    # Laboratory Results
    story.append(Paragraph("<b>Laboratory Results</b>", styles['Heading2']))
    lab_data = [
        ["Test Name", "Result", "Normal Range", "Unit"],
        ["Troponin I", "2.5", "0.0-0.04", "ng/mL"],
        ["CK-MB", "45", "0-25", "U/L"],
        ["Cholesterol (Total)", "245", "< 200", "mg/dL"],
        ["LDL Cholesterol", "165", "< 100", "mg/dL"],
        ["HDL Cholesterol", "35", "> 40", "mg/dL"],
        ["Triglycerides", "220", "< 150", "mg/dL"],
        ["Glucose (Fasting)", "118", "70-100", "mg/dL"],
        ["Hemoglobin", "14.2", "13.5-17.5", "g/dL"],
        ["WBC Count", "11.5", "4.0-11.0", "10^3/μL"],
    ]
    lab_table = Table(lab_data, colWidths=[2*inch, 1*inch, 1.2*inch, 0.8*inch])
    lab_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        # Highlight abnormal values
        ('BACKGROUND', (0, 1), (-1, 1), colors.Color(1, 0.9, 0.9)),  # Troponin
        ('BACKGROUND', (0, 2), (-1, 2), colors.Color(1, 0.9, 0.9)),  # CK-MB
        ('BACKGROUND', (0, 3), (-1, 3), colors.Color(1, 0.9, 0.9)),  # Total Chol
        ('BACKGROUND', (0, 4), (-1, 4), colors.Color(1, 0.9, 0.9)),  # LDL
        ('BACKGROUND', (0, 5), (-1, 5), colors.Color(1, 0.9, 0.9)),  # HDL
        ('BACKGROUND', (0, 6), (-1, 6), colors.Color(1, 0.9, 0.9)),  # Triglyc
    ]))
    story.append(lab_table)
    story.append(Spacer(1, 0.3 * inch))
    
    # Medical History
    story.append(Paragraph("<b>Medical History</b>", styles['Heading2']))
    history = """<b>Past Medical History:</b> Hypertension (diagnosed 5 years ago), Type 2 Diabetes Mellitus 
(controlled with Metformin), Hyperlipidemia.<br/><br/>
<b>Medications:</b> Lisinopril 10mg daily, Metformin 1000mg twice daily, Atorvastatin 20mg daily.<br/><br/>
<b>Social History:</b> 30-year smoking history (1 pack/day), occasional alcohol use, sedentary lifestyle.<br/><br/>
<b>Family History:</b> Father died of myocardial infarction at age 62. Mother has hypertension."""
    story.append(Paragraph(history, styles['Normal']))
    story.append(Spacer(1, 0.3 * inch))
    
    # Clinical Assessment
    story.append(Paragraph("<b>Clinical Assessment</b>", styles['Heading2']))
    assessment = """Patient presentation is highly concerning for acute coronary syndrome. Elevated cardiac 
biomarkers (Troponin I and CK-MB) combined with typical angina symptoms and risk factors (age, male gender, 
hypertension, diabetes, smoking, family history) strongly suggest myocardial infarction. Immediate cardiology 
consultation and cardiac catheterization recommended."""
    story.append(Paragraph(assessment, styles['Normal']))
    
    # Build PDF
    doc.build(story)
    
    print(f"Sample patient PDF created: {output_path}")
    return output_path


if __name__ == "__main__":
    create_sample_patient_pdf()
