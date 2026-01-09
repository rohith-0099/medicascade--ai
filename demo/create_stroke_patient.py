"""
Create test patient PDF with brain CT scan (stroke case)
"""
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors
import os


def create_stroke_patient_pdf():
    """Create a realistic stroke patient PDF with CT scan"""
    
    output_path = "/home/rohith/medicascade-ai/demo/stroke_patient.pdf"
    os.makedirs("/home/rohith/medicascade-ai/demo", exist_ok=True)
    
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title = Paragraph("<b>EMERGENCY PATIENT MEDICAL REPORT</b>", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 0.2 * inch))
    
    # Emergency Banner
    emergency = Paragraph("<b><font color='red'>⚠️ EMERGENCY CASE - IMMEDIATE ATTENTION REQUIRED</font></b>", 
                         styles['Heading2'])
    story.append(emergency)
    story.append(Spacer(1, 0.2 * inch))
    
    # Patient Demographics
    story.append(Paragraph("<b>Patient Information</b>", styles['Heading2']))
    demo_data = [
        ["Name:", "Robert Johnson"],
        ["Age:", "67 years"],
        ["Gender:", "Male"],
        ["Patient ID:", "EMRG-789012"],
        ["Date/Time:", "January 9, 2026 - 19:45"],
        ["Arrival Mode:", "Ambulance - Code Stroke"]
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
    symptoms = """<b>SUDDEN ONSET severe headache, confusion, and left-sided weakness.</b><br/><br/>
Patient was found collapsed at home by family members at 18:30. Wife reports patient complained of 
"worst headache of my life" before losing consciousness for approximately 2 minutes. Upon regaining 
consciousness, patient was confused, disoriented, and unable to move left arm. Speech was slurred.<br/><br/>
<b>Time of symptom onset:</b> Approximately 18:25 (80 minutes ago)<br/>
<b>Last known well:</b> 18:15<br/>
<b>NIHSS Score:</b> 14 (moderate to severe stroke)"""
    story.append(Paragraph(symptoms, styles['Normal']))
    story.append(Spacer(1, 0.3 * inch))
    
    # Vital Signs
    story.append(Paragraph("<b>Vital Signs (on arrival)</b>", styles['Heading2']))
    vitals_data = [
        ["Parameter", "Value", "Status"],
        ["Blood Pressure", "190/110 mmHg", "⚠️ CRITICAL HIGH"],
        ["Heart Rate", "88 bpm", "Normal"],
        ["Temperature", "98.4°F", "Normal"],
        ["Respiratory Rate", "18/min", "Normal"],
        ["Oxygen Saturation", "96%", "Normal"],
        ["Glasgow Coma Scale", "13/15", "⚠️ Decreased"],
    ]
    vitals_table = Table(vitals_data, colWidths=[2*inch, 1.8*inch, 1.5*inch])
    vitals_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 1), (-1, 1), colors.Color(1, 0.8, 0.8)),
        ('BACKGROUND', (0, 6), (-1, 6), colors.Color(1, 0.9, 0.7)),
    ]))
    story.append(vitals_table)
    story.append(Spacer(1, 0.3 * inch))
    
    # Physical Examination
    story.append(Paragraph("<b>Neurological Examination</b>", styles['Heading2']))
    neuro_exam = """<b>Mental Status:</b> Confused, disoriented to time and place<br/>
<b>Speech:</b> Slurred, difficulty finding words (expressive aphasia)<br/>
<b>Cranial Nerves:</b> Left facial droop (CN VII), pupils equal and reactive<br/>
<b>Motor:</b> Left arm 1/5 strength, left leg 2/5 strength, right side 5/5<br/>
<b>Sensory:</b> Decreased sensation on left side<br/>
<b>Reflexes:</b> Hyperreflexia on left, positive Babinski on left<br/>
<b>Coordination:</b> Unable to assess due to left-sided weakness"""
    story.append(Paragraph(neuro_exam, styles['Normal']))
    story.append(Spacer(1, 0.3 * inch))
    
    # Laboratory Results
    story.append(Paragraph("<b>STAT Laboratory Results</b>", styles['Heading2']))
    lab_data = [
        ["Test Name", "Result", "Normal Range", "Unit"],
        ["Hemoglobin", "15.8", "13.5-17.5", "g/dL"],
        ["WBC Count", "13.2", "4.0-11.0", "10^3/μL"],
        ["Platelets", "185", "150-400", "10^3/μL"],
        ["Glucose", "156", "70-100", "mg/dL"],
        ["Sodium", "138", "136-145", "mEq/L"],
        ["Potassium", "4.2", "3.5-5.0", "mEq/L"],
        ["Creatinine", "1.1", "0.6-1.2", "mg/dL"],
        ["PT/INR", "1.1", "0.9-1.1", "ratio"],
        ["PTT", "28", "25-35", "seconds"],
    ]
    lab_table = Table(lab_data, colWidths=[2*inch, 1*inch, 1.2*inch, 0.8*inch])
    lab_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 2), (-1, 2), colors.Color(1, 0.95, 0.9)),  # Elevated WBC
        ('BACKGROUND', (0, 4), (-1, 4), colors.Color(1, 0.95, 0.9)),  # Elevated glucose
    ]))
    story.append(lab_table)
    story.append(Spacer(1, 0.3 * inch))
    
    # CT Scan - ADD THE IMAGE HERE
    story.append(Paragraph("<b>⚠️ BRAIN CT SCAN (NON-CONTRAST)</b>", styles['Heading2']))
    ct_findings_header = Paragraph("<b><font color='red'>CRITICAL FINDINGS - STAT NEUROSURGERY CONSULT</font></b>", 
                                   styles['Heading3'])
    story.append(ct_findings_header)
    story.append(Spacer(1, 0.1 * inch))
    
    # Add CT scan image
    ct_image_path = "/home/rohith/.gemini/antigravity/brain/db167039-f21c-4ded-a567-4d56441c64ac/uploaded_image_1767970386937.png"
    if os.path.exists(ct_image_path):
        ct_img = RLImage(ct_image_path, width=4*inch, height=3*inch)
        story.append(ct_img)
        story.append(Spacer(1, 0.2 * inch))
    
    ct_findings = """<b>RADIOLOGIST INTERPRETATION:</b><br/><br/>
<b>FINDINGS:</b><br/>
- Large hyperdense area in the RIGHT BASAL GANGLIA region measuring approximately 3.5 x 3.0 cm<br/>
- Consistent with ACUTE INTRACEREBRAL HEMORRHAGE (ICH)<br/>
- Mild mass effect with compression of the right lateral ventricle<br/>
- No midline shift currently visible<br/>
- No evidence of herniation at this time<br/>
- No subarachnoid hemorrhage identified<br/><br/>

<b><font color='red'>IMPRESSION: ACUTE RIGHT BASAL GANGLIA HEMORRHAGE (HEMORRHAGIC STROKE)</font></b><br/>
<b>Estimated volume:</b> ~35 mL<br/>
<b>Location:</b> Deep right hemisphere (putamen/internal capsule region)<br/>
<b>Risk:</b> HIGH risk for expansion and neurological deterioration"""
    story.append(Paragraph(ct_findings, styles['Normal']))
    story.append(Spacer(1, 0.3 * inch))
    
    # Medical History
    story.append(Paragraph("<b>Past Medical History</b>", styles['Heading2']))
    history = """<b>Chronic Conditions:</b><br/>
- Hypertension (poorly controlled, on medication irregularly)<br/>
- Type 2 Diabetes Mellitus<br/>
- Hyperlipidemia<br/>
- Chronic kidney disease Stage 2<br/><br/>

<b>Medications (Home):</b><br/>
- Lisinopril 20mg daily (admits poor compliance)<br/>
- Amlodipine 10mg daily<br/>
- Metformin 1000mg twice daily<br/>
- Atorvastatin 40mg nightly<br/><br/>

<b>Social History:</b><br/>
- Former smoker (quit 5 years ago, 40 pack-year history)<br/>
- Occasional alcohol use<br/>
- Sedentary lifestyle<br/><br/>

<b>Family History:</b><br/>
- Father died of stroke at age 69<br/>
- Mother with hypertension and diabetes"""
    story.append(Paragraph(history, styles['Normal']))
    story.append(Spacer(1, 0.3 * inch))
    
    # Clinical Assessment
    story.append(Paragraph("<b>EMERGENCY DEPARTMENT DIAGNOSIS</b>", styles['Heading2']))
    assessment = """<b><font color='red' size='14'>ACUTE HEMORRHAGIC STROKE - RIGHT BASAL GANGLIA</font></b><br/><br/>

<b>Assessment:</b> 67-year-old male with sudden onset severe headache, confusion, and left hemiparesis. 
Brain CT confirms acute intracerebral hemorrhage in right basal ganglia. Presentation consistent with 
hypertensive hemorrhagic stroke given history of poorly controlled hypertension.<br/><br/>

<b>Severity:</b> Moderate-severe (NIHSS 14, hemorrhage volume ~35mL)<br/>
<b>Etiology:</b> Most likely hypertensive hemorrhage (chronic uncontrolled BP)<br/>
<b>Complications Risk:</b> HIGH - risk of hematoma expansion, increased ICP, herniation<br/><br/>

<b>⚠️ IMMEDIATE MANAGEMENT INITIATED:</b><br/>
- Neurosurgery STAT consult (on way)<br/>
- ICU admission arranged<br/>
- Blood pressure control initiated (target SBP 140-160)<br/>
- Repeat CT scheduled in 6 hours<br/>
- Intracranial pressure monitoring consideration<br/>
- Reversal agents if needed (none needed - normal INR)<br/><br/>

<b>PROGNOSIS:</b> Guarded. Significant neurological deficits present. Recovery will depend on 
hemorrhage stability, response to treatment, and rehabilitation."""
    story.append(Paragraph(assessment, styles['Normal']))
    story.append(Spacer(1, 0.2 * inch))
    
    # Build PDF
    doc.build(story)
    
    print(f"✅ Stroke patient PDF created: {output_path}")
    print(f"📄 This case includes:")
    print(f"   - Brain CT scan showing hemorrhagic stroke")
    print(f"   - Severe neurological symptoms")
    print(f"   - Abnormal vital signs (high BP)")
    print(f"   - Complete medical history")
    print(f"\n🧪 Expected AI diagnosis: Hemorrhagic Stroke / Intracerebral Hemorrhage")
    return output_path


if __name__ == "__main__":
    create_stroke_patient_pdf()
