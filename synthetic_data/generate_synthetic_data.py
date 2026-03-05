"""
MediCascade AI — Synthetic Medical Data Generator
Generates realistic patient PDF records for testing the full cascade pipeline.

Cases:
  1. Type 2 Diabetes (lab-heavy)
  2. Acute Myocardial Infarction (symptoms + ECG notes)
  3. Brain Tumor / Glioma (imaging + clinical notes)
  4. Chronic Kidney Disease Stage 3 (lab results)
  5. Community-Acquired Pneumonia (symptoms + imaging + labs)

Run: python generate_synthetic_data.py
Output: synthetic_data/*.pdf
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import date

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "synthetic_data")
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ─── Style helpers ────────────────────────────────────────────────────────────

def build_doc(filename: str):
    path = os.path.join(OUTPUT_DIR, filename)
    doc = SimpleDocTemplate(
        path, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm
    )
    return doc, path


def styles():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle("HospitalHeader", fontSize=16, fontName="Helvetica-Bold",
                         alignment=TA_CENTER, textColor=colors.HexColor("#1a3a5c"), spaceAfter=4))
    s.add(ParagraphStyle("SubHeader", fontSize=10, fontName="Helvetica",
                         alignment=TA_CENTER, textColor=colors.grey, spaceAfter=10))
    s.add(ParagraphStyle("SectionTitle", fontSize=12, fontName="Helvetica-Bold",
                         textColor=colors.HexColor("#1a3a5c"), spaceBefore=10, spaceAfter=4))
    s.add(ParagraphStyle("Body", fontSize=9.5, fontName="Helvetica",
                         leading=14, spaceAfter=4))
    s.add(ParagraphStyle("Abnormal", fontSize=9.5, fontName="Helvetica-Bold",
                         textColor=colors.red, leading=14))
    s.add(ParagraphStyle("Label", fontSize=9, fontName="Helvetica-Bold",
                         textColor=colors.HexColor("#333333")))
    return s


def header_block(st, hospital="City General Hospital", dept="Department of Medicine"):
    return [
        Paragraph(hospital, st["HospitalHeader"]),
        Paragraph(dept, st["SubHeader"]),
        HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1a3a5c")),
        Spacer(1, 6),
    ]


def patient_info_table(st, name, age, sex, dob, mrn, date_str, physician):
    data = [
        ["Patient Name:", name, "MRN:", mrn],
        ["Age / Sex:", f"{age} years / {sex}", "Date:", date_str],
        ["DOB:", dob, "Physician:", physician],
    ]
    t = Table(data, colWidths=[38*mm, 62*mm, 28*mm, 62*mm])
    t.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica", 9),
        ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 9),
        ("FONT", (2, 0), (2, -1), "Helvetica-Bold", 9),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#222222")),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eef3f9")),
        ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#eef3f9")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return [t, Spacer(1, 8)]


def lab_table(st, headers, rows, abnormal_rows=None):
    abnormal_rows = abnormal_rows or []
    full = [headers] + rows
    t = Table(full, colWidths=[55*mm, 35*mm, 35*mm, 45*mm, 20*mm])
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a5c")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9),
        ("FONT", (0, 1), (-1, -1), "Helvetica", 9),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f9fc")]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for r in abnormal_rows:
        style_cmds += [
            ("TEXTCOLOR", (1, r+1), (1, r+1), colors.red),
            ("FONT", (1, r+1), (1, r+1), "Helvetica-Bold", 9),
            ("TEXTCOLOR", (4, r+1), (4, r+1), colors.red),
            ("FONT", (4, r+1), (4, r+1), "Helvetica-Bold", 9),
        ]
    t.setStyle(TableStyle(style_cmds))
    return t


# ═════════════════════════════════════════════════════════════════════════════
# CASE 1 — Type 2 Diabetes Mellitus
# ═════════════════════════════════════════════════════════════════════════════

def generate_case_diabetes():
    doc, path = build_doc("case_01_type2_diabetes.pdf")
    st = styles()
    story = []

    story += header_block(st, "City General Hospital", "Department of Internal Medicine — Endocrinology")
    story += patient_info_table(st,
        name="Rajesh Kumar", age=54, sex="Male", dob="12-Mar-1970",
        mrn="MGH-2024-04471", date_str="05-Mar-2026", physician="Dr. Ananya Sharma, MD")

    story += [
        Paragraph("CLINICAL REPORT — OUTPATIENT VISIT", st["SectionTitle"]),
        Paragraph(
            "<b>Chief Complaint:</b> Increased thirst, frequent urination, fatigue, and blurred vision for the past 3 months.",
            st["Body"]),
        Paragraph(
            "<b>History of Present Illness:</b> Mr. Rajesh Kumar is a 54-year-old male with a 5-year history of "
            "hypertension who presents with polyuria, polydipsia, and unexplained weight loss of approximately 6 kg "
            "over 3 months. He reports waking up 3–4 times per night to urinate. He has a strong family history of "
            "diabetes mellitus (mother and maternal uncle). BMI is 31.2 kg/m².",
            st["Body"]),
        Spacer(1, 6),
        Paragraph("VITAL SIGNS", st["SectionTitle"]),
    ]

    vitals = [
        ["Blood Pressure:", "148/92 mmHg", "Heart Rate:", "82 bpm"],
        ["Temperature:", "37.1 °C", "SpO2:", "98%"],
        ["BMI:", "31.2 kg/m²", "Weight:", "88 kg"],
    ]
    t_vitals = Table(vitals, colWidths=[38*mm, 62*mm, 28*mm, 62*mm])
    t_vitals.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica", 9),
        ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 9),
        ("FONT", (2, 0), (2, -1), "Helvetica-Bold", 9),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story += [t_vitals, Spacer(1, 8)]

    story.append(Paragraph("LABORATORY RESULTS", st["SectionTitle"]))
    lab_headers = ["Test", "Result", "Normal Range", "Unit", "Flag"]
    lab_rows = [
        ["Fasting Blood Glucose",   "214",  "70 – 100",   "mg/dL", "HIGH ↑"],
        ["HbA1c",                   "8.7",  "< 5.7",      "%",     "HIGH ↑"],
        ["Post-Prandial Glucose",   "318",  "< 140",      "mg/dL", "HIGH ↑"],
        ["Serum Insulin",           "22.4", "2.6 – 24.9", "µU/mL", "Normal"],
        ["Total Cholesterol",       "224",  "< 200",      "mg/dL", "HIGH ↑"],
        ["LDL Cholesterol",         "148",  "< 100",      "mg/dL", "HIGH ↑"],
        ["HDL Cholesterol",         "38",   "> 40",       "mg/dL", "LOW ↓"],
        ["Triglycerides",           "298",  "< 150",      "mg/dL", "HIGH ↑"],
        ["Serum Creatinine",        "1.1",  "0.7 – 1.2",  "mg/dL", "Normal"],
        ["eGFR",                    "72",   "> 60",       "mL/min","Normal"],
        ["Urine Microalbumin",      "82",   "< 30",       "mg/g",  "HIGH ↑"],
        ["HbA1c (3 months prior)",  "7.2",  "< 5.7",      "%",     "HIGH ↑"],
    ]
    story.append(lab_table(st, lab_headers, lab_rows, abnormal_rows=[0,1,2,4,5,6,7,10,11]))
    story.append(Spacer(1, 8))

    story += [
        Paragraph("CLINICAL NOTES", st["SectionTitle"]),
        Paragraph(
            "The patient's fasting glucose of 214 mg/dL and HbA1c of 8.7% are consistent with poorly controlled "
            "Type 2 Diabetes Mellitus. The progressive rise from 7.2% to 8.7% over 3 months indicates worsening "
            "glycaemic control. Elevated LDL and triglycerides indicate dyslipidaemia, a common comorbidity. "
            "Microalbuminuria (82 mg/g) suggests early diabetic nephropathy. "
            "Hypertension (148/92 mmHg) adds significant cardiovascular risk. "
            "Recommend initiation of Metformin 500 mg BD, dietary counselling, and ophthalmology referral for "
            "diabetic retinopathy screening.",
            st["Body"]),
        Spacer(1, 8),
        Paragraph("PRELIMINARY DIAGNOSIS", st["SectionTitle"]),
        Paragraph("Type 2 Diabetes Mellitus — Uncontrolled (HbA1c 8.7%). "
                  "Associated: Dyslipidaemia, Early Diabetic Nephropathy, Hypertension.", st["Abnormal"]),
    ]

    doc.build(story)
    print(f"  ✅ Generated: {path}")
    return path


# ═════════════════════════════════════════════════════════════════════════════
# CASE 2 — Acute Myocardial Infarction (STEMI)
# ═════════════════════════════════════════════════════════════════════════════

def generate_case_ami():
    doc, path = build_doc("case_02_myocardial_infarction.pdf")
    st = styles()
    story = []

    story += header_block(st, "City General Hospital", "Department of Cardiology — Emergency Cardiac Unit")
    story += patient_info_table(st,
        name="Suresh Mehta", age=61, sex="Male", dob="14-Jun-1964",
        mrn="MGH-2024-07832", date_str="05-Mar-2026", physician="Dr. Priya Nair, DM (Cardiology)")

    story += [
        Paragraph("EMERGENCY ADMISSION REPORT — ACUTE CHEST PAIN", st["SectionTitle"]),
        Paragraph(
            "<b>Chief Complaint:</b> Severe crushing chest pain radiating to the left arm and jaw, onset 2 hours ago.",
            st["Body"]),
        Paragraph(
            "<b>History of Present Illness:</b> Mr. Suresh Mehta is a 61-year-old male smoker (40 pack-years) "
            "with known hypertension and hypercholesterolaemia who presented to the emergency department with sudden "
            "onset severe retrosternal chest pain (9/10) radiating to the left arm and jaw, associated with "
            "diaphoresis, nausea, and dyspnoea. Pain began at rest approximately 2 hours prior to arrival. "
            "He denies prior similar episodes. On examination he is pale, diaphoretic, and in obvious distress. "
            "No previous cardiac history. Currently on Amlodipine 5 mg and Atorvastatin 40 mg.",
            st["Body"]),
        Spacer(1, 6),
        Paragraph("VITAL SIGNS ON ADMISSION", st["SectionTitle"]),
    ]

    vitals = [
        ["Blood Pressure:", "88/60 mmHg (Hypotensive)", "Heart Rate:", "112 bpm (Tachycardia)"],
        ["Temperature:", "37.0 °C", "SpO2:", "92% on room air"],
        ["Respiratory Rate:", "24 breaths/min", "GCS:", "15/15"],
    ]
    t_vitals = Table(vitals, colWidths=[38*mm, 62*mm, 28*mm, 62*mm])
    t_vitals.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica", 9),
        ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 9),
        ("FONT", (2, 0), (2, -1), "Helvetica-Bold", 9),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ("TEXTCOLOR", (1, 0), (1, 0), colors.red),
        ("FONT", (1, 0), (1, 0), "Helvetica-Bold", 9),
        ("TEXTCOLOR", (3, 0), (3, 0), colors.red),
        ("FONT", (3, 0), (3, 0), "Helvetica-Bold", 9),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story += [t_vitals, Spacer(1, 8)]

    story.append(Paragraph("ECG FINDINGS", st["SectionTitle"]))
    story.append(Paragraph(
        "12-lead ECG performed at 08:14 AM: <b>ST-segment elevation of 4–5 mm in leads II, III, and aVF</b> "
        "consistent with inferior wall ST-elevation myocardial infarction (STEMI). "
        "Reciprocal ST depression in leads I and aVL. Sinus tachycardia at 112 bpm. "
        "No left bundle branch block. QTc interval: 450 ms.",
        st["Body"]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("CARDIAC BIOMARKERS", st["SectionTitle"]))
    lab_headers = ["Biomarker", "Result", "Normal Range", "Unit", "Flag"]
    lab_rows = [
        ["Troponin-I (hs-cTnI)", "8.42",  "< 0.04",     "ng/mL", "CRITICAL ↑↑"],
        ["CK-MB",                "112",   "0 – 25",      "U/L",   "HIGH ↑"],
        ["BNP",                  "480",   "< 100",       "pg/mL", "HIGH ↑"],
        ["Myoglobin",            "420",   "< 90",        "ng/mL", "HIGH ↑"],
        ["D-Dimer",              "0.48",  "< 0.50",      "µg/mL", "Normal"],
        ["Serum Potassium",      "3.4",   "3.5 – 5.0",   "mEq/L", "LOW ↓"],
        ["Serum Sodium",         "138",   "135 – 145",   "mEq/L", "Normal"],
        ["Creatinine",           "1.3",   "0.7 – 1.2",   "mg/dL", "HIGH ↑"],
        ["PT/INR",               "1.1",   "0.9 – 1.1",   "",      "Normal"],
    ]
    story.append(lab_table(st, lab_headers, lab_rows, abnormal_rows=[0,1,2,3,5,7]))
    story.append(Spacer(1, 8))

    story += [
        Paragraph("CLINICAL NOTES", st["SectionTitle"]),
        Paragraph(
            "Highly elevated hs-cTnI (8.42 ng/mL) and CK-MB (112 U/L) with ST-elevation on ECG confirm an "
            "acute inferior STEMI. Haemodynamic instability (BP 88/60) suggests cardiogenic shock. "
            "Patient transferred immediately to catheterisation laboratory for emergency primary PCI "
            "(percutaneous coronary intervention). Dual antiplatelet therapy (Aspirin 300 mg + Ticagrelor 180 mg) "
            "and unfractionated heparin initiated. Cardiothoracic surgery on standby.",
            st["Body"]),
        Spacer(1, 8),
        Paragraph("PRELIMINARY DIAGNOSIS", st["SectionTitle"]),
        Paragraph("Acute Inferior STEMI with Cardiogenic Shock. Risk: CRITICAL — Immediate PCI required.", st["Abnormal"]),
    ]

    doc.build(story)
    print(f"  ✅ Generated: {path}")
    return path


# ═════════════════════════════════════════════════════════════════════════════
# CASE 3 — Brain Tumor / Glioblastoma
# ═════════════════════════════════════════════════════════════════════════════

def generate_case_brain_tumor():
    doc, path = build_doc("case_03_brain_tumor_glioblastoma.pdf")
    st = styles()
    story = []

    story += header_block(st, "City General Hospital", "Department of Neurosurgery & Neuro-Oncology")
    story += patient_info_table(st,
        name="Kavitha Reddy", age=47, sex="Female", dob="22-Sep-1978",
        mrn="MGH-2024-09215", date_str="05-Mar-2026", physician="Dr. Vikram Rao, MCh (Neurosurgery)")

    story += [
        Paragraph("NEUROSURGICAL CONSULTATION REPORT", st["SectionTitle"]),
        Paragraph(
            "<b>Chief Complaint:</b> Progressive headaches, new-onset seizures, and right-sided weakness for 6 weeks.",
            st["Body"]),
        Paragraph(
            "<b>History of Present Illness:</b> Mrs. Kavitha Reddy is a 47-year-old female who presents with a "
            "6-week history of severe, progressive headaches worse in the morning, two witnessed tonic-clonic seizures "
            "in the past 2 weeks, and progressive right-sided arm and leg weakness. She reports word-finding difficulty "
            "and personality changes noted by her family. No prior neurological history. No significant family history "
            "of brain tumors. Non-smoker, no alcohol consumption.",
            st["Body"]),
        Spacer(1, 6),
        Paragraph("MRI BRAIN — RADIOLOGY REPORT", st["SectionTitle"]),
        Paragraph(
            "<b>Modality:</b> MRI Brain with and without contrast (3T scanner) — 05-Mar-2026",
            st["Body"]),
        Paragraph(
            "<b>Findings:</b> A large, irregular, heterogeneously enhancing mass lesion is identified in the "
            "LEFT TEMPORAL-PARIETAL region measuring approximately <b>4.8 cm × 4.2 cm × 3.9 cm</b>. "
            "The lesion demonstrates central areas of necrosis, surrounding vasogenic oedema extending into the "
            "adjacent white matter, and significant midline shift of <b>7 mm to the right</b>. "
            "Post-gadolinium images show ring-enhancement with an irregular inner border — highly characteristic "
            "of high-grade glioma. No evidence of leptomeningeal spread. Herniation not yet present. "
            "DWI shows restricted diffusion within the necrotic core.",
            st["Body"]),
        Paragraph(
            "<b>Radiological Impression:</b> Large ring-enhancing left temporal-parietal mass with mass effect, "
            "midline shift, and surrounding oedema. Features highly suggestive of "
            "<b>Glioblastoma Multiforme (GBM), WHO Grade IV</b>.",
            st["Abnormal"]),
        Spacer(1, 6),
        Paragraph("NEUROLOGICAL EXAMINATION", st["SectionTitle"]),
        Paragraph(
            "GCS: 14/15. Oriented to person and place. Right-sided hemiparesis (power 3/5 upper and lower limb). "
            "Expressive dysphasia noted. Fundoscopy: bilateral papilloedema consistent with raised intracranial pressure. "
            "Plantar reflex: extensor on right. Brisk deep tendon reflexes right side.",
            st["Body"]),
        Spacer(1, 6),
        Paragraph("LABORATORY RESULTS", st["SectionTitle"]),
    ]

    lab_headers = ["Test", "Result", "Normal Range", "Unit", "Flag"]
    lab_rows = [
        ["Haemoglobin",      "11.2", "12.0 – 16.0", "g/dL",  "LOW ↓"],
        ["WBC Count",        "9800", "4000 – 11000", "cells/µL","Normal"],
        ["Platelets",        "218",  "150 – 400",    "×10³/µL","Normal"],
        ["LDH",              "488",  "140 – 280",    "U/L",   "HIGH ↑"],
        ["CRP",              "18.2", "< 5.0",        "mg/L",  "HIGH ↑"],
        ["Sodium",           "131",  "135 – 145",    "mEq/L", "LOW ↓"],
        ["Serum Creatinine", "0.9",  "0.5 – 1.1",    "mg/dL", "Normal"],
        ["CEA (tumour marker)","3.2","< 5.0",        "ng/mL", "Normal"],
        ["AFP",              "1.8",  "< 10",         "ng/mL", "Normal"],
    ]
    story.append(lab_table(st, lab_headers, lab_rows, abnormal_rows=[0,3,4,5]))
    story.append(Spacer(1, 8))

    story += [
        Paragraph("CLINICAL NOTES & PLAN", st["SectionTitle"]),
        Paragraph(
            "MRI findings are highly consistent with Glioblastoma Multiforme (GBM), the most aggressive primary "
            "brain tumour (WHO Grade IV). The size (4.8 cm), ring-enhancement, necrotic core, and 7 mm midline shift "
            "indicate an advanced lesion. The hyponatraemia (131 mEq/L) is likely secondary to SIADH related to the "
            "intracranial mass. Elevated LDH indicates high tumour burden and poor prognosis. "
            "Immediate plan: Start IV Dexamethasone 8 mg BD for cerebral oedema. "
            "Levetiracetam 1000 mg BD for seizure prophylaxis. "
            "Refer to tumour board for surgical planning — maximal safe resection followed by concurrent "
            "Temozolomide chemotherapy and radiotherapy (Stupp protocol).",
            st["Body"]),
        Spacer(1, 8),
        Paragraph("PRELIMINARY DIAGNOSIS", st["SectionTitle"]),
        Paragraph("Glioblastoma Multiforme (GBM) — Left Temporal-Parietal Region, WHO Grade IV, 4.8 cm with 7 mm midline shift.", st["Abnormal"]),
    ]

    doc.build(story)
    print(f"  ✅ Generated: {path}")
    return path


# ═════════════════════════════════════════════════════════════════════════════
# CASE 4 — Chronic Kidney Disease Stage 3
# ═════════════════════════════════════════════════════════════════════════════

def generate_case_ckd():
    doc, path = build_doc("case_04_chronic_kidney_disease.pdf")
    st = styles()
    story = []

    story += header_block(st, "City General Hospital", "Department of Nephrology")
    story += patient_info_table(st,
        name="Mohammed Farouk", age=68, sex="Male", dob="03-Jan-1958",
        mrn="MGH-2024-11042", date_str="05-Mar-2026", physician="Dr. Sunita Rao, DM (Nephrology)")

    story += [
        Paragraph("NEPHROLOGY OUTPATIENT CONSULTATION", st["SectionTitle"]),
        Paragraph(
            "<b>Chief Complaint:</b> Leg swelling, fatigue, decreased urine output, and foamy urine for 4 months.",
            st["Body"]),
        Paragraph(
            "<b>History of Present Illness:</b> Mr. Mohammed Farouk is a 68-year-old male with a 15-year history "
            "of Type 2 Diabetes and 10 years of hypertension, presenting with progressive bilateral leg swelling, "
            "marked fatigue, reduced urine output, and frothy urine. He notes increasing breathlessness on exertion "
            "over 2 months. No dysuria or haematuria. Currently on Metformin 500 mg BD, Glipizide 5 mg daily, "
            "Amlodipine 10 mg, and Losartan 50 mg.",
            st["Body"]),
        Spacer(1, 6),
        Paragraph("RENAL FUNCTION TESTS", st["SectionTitle"]),
    ]

    lab_headers = ["Test", "Result", "Normal Range", "Unit", "Flag"]
    lab_rows = [
        ["Serum Creatinine",        "2.8",  "0.7 – 1.2",   "mg/dL",   "HIGH ↑↑"],
        ["Blood Urea Nitrogen (BUN)","42",  "7 – 20",       "mg/dL",   "HIGH ↑"],
        ["eGFR (CKD-EPI)",          "31",  "> 60",          "mL/min",  "LOW ↓↓"],
        ["Uric Acid",               "8.4", "3.5 – 7.2",    "mg/dL",   "HIGH ↑"],
        ["Serum Potassium",         "5.6", "3.5 – 5.0",    "mEq/L",   "HIGH ↑"],
        ["Serum Sodium",            "133", "135 – 145",     "mEq/L",   "LOW ↓"],
        ["Serum Phosphate",         "5.2", "2.5 – 4.5",    "mg/dL",   "HIGH ↑"],
        ["Serum Calcium",           "7.8", "8.5 – 10.5",   "mg/dL",   "LOW ↓"],
        ["Haemoglobin",             "9.4", "13.5 – 17.5",  "g/dL",    "LOW ↓"],
        ["Urine Protein/Creatinine","2.8", "< 0.2",         "ratio",   "HIGH ↑↑"],
        ["Urine Microalbumin",      "480", "< 30",           "mg/g",   "HIGH ↑↑"],
        ["HbA1c",                   "9.1", "< 5.7",          "%",      "HIGH ↑"],
        ["Intact PTH",              "118", "15 – 65",       "pg/mL",   "HIGH ↑"],
    ]
    story.append(lab_table(st, lab_headers, lab_rows, abnormal_rows=list(range(12))))
    story.append(Spacer(1, 8))

    story += [
        Paragraph("CLINICAL NOTES", st["SectionTitle"]),
        Paragraph(
            "eGFR of 31 mL/min classifies this patient as CKD Stage 3b (G3b). The combination of long-standing "
            "diabetes and hypertension with severe proteinuria (UPCR 2.8) strongly suggests diabetic nephropathy "
            "as the primary aetiology. Hyperkalaemia (K+ 5.6 mEq/L) is a significant concern — Metformin and "
            "Glipizide must be discontinued immediately given the impaired renal function. "
            "Normochromic anaemia (Hb 9.4 g/dL) consistent with CKD-related anaemia of chronic disease. "
            "Elevated PTH and low calcium suggest early renal osteodystrophy. "
            "Recommend: nephrology-supervised dietary protein restriction, phosphate binders, "
            "erythropoiesis-stimulating agent, and CKD-appropriate antihypertensives. "
            "Prepare patient for haemodialysis counselling.",
            st["Body"]),
        Spacer(1, 8),
        Paragraph("PRELIMINARY DIAGNOSIS", st["SectionTitle"]),
        Paragraph("Chronic Kidney Disease Stage 3b (eGFR 31). Aetiology: Diabetic Nephropathy. "
                  "Associated: Anaemia of CKD, Renal Osteodystrophy, Hyperkalaemia.", st["Abnormal"]),
    ]

    doc.build(story)
    print(f"  ✅ Generated: {path}")
    return path


# ═════════════════════════════════════════════════════════════════════════════
# CASE 5 — Community-Acquired Pneumonia
# ═════════════════════════════════════════════════════════════════════════════

def generate_case_pneumonia():
    doc, path = build_doc("case_05_pneumonia.pdf")
    st = styles()
    story = []

    story += header_block(st, "City General Hospital", "Department of Pulmonology & Respiratory Medicine")
    story += patient_info_table(st,
        name="Priya Sharma", age=34, sex="Female", dob="17-Jul-1991",
        mrn="MGH-2024-13377", date_str="05-Mar-2026", physician="Dr. Arjun Menon, MD (Pulmonology)")

    story += [
        Paragraph("INPATIENT ADMISSION REPORT", st["SectionTitle"]),
        Paragraph(
            "<b>Chief Complaint:</b> High-grade fever, productive cough with yellow-green sputum, and right-sided chest pain for 5 days.",
            st["Body"]),
        Paragraph(
            "<b>History of Present Illness:</b> Ms. Priya Sharma is a 34-year-old non-smoker who presents with a "
            "5-day history of high-grade fever (up to 40.1°C), productive cough with purulent yellow-green sputum, "
            "right-sided pleuritic chest pain worsening on deep inspiration, and significant fatigue. "
            "She reports an upper respiratory tract infection 2 weeks ago that appeared to resolve. "
            "No known immunocompromise. No recent travel or sick contacts. Up to date with vaccination. "
            "Currently on no regular medications.",
            st["Body"]),
        Spacer(1, 6),
        Paragraph("VITAL SIGNS", st["SectionTitle"]),
    ]

    vitals = [
        ["Temperature:",      "39.8 °C (Febrile)", "Heart Rate:",  "108 bpm (Tachycardia)"],
        ["Blood Pressure:",   "118/74 mmHg",        "SpO2:",        "92% on room air"],
        ["Respiratory Rate:", "26 breaths/min",      "CRB-65 Score:", "2 (Moderate Severity)"],
    ]
    t_vitals = Table(vitals, colWidths=[38*mm, 62*mm, 28*mm, 62*mm])
    t_vitals.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica", 9),
        ("FONT", (0, 0), (0, -1), "Helvetica-Bold", 9),
        ("FONT", (2, 0), (2, -1), "Helvetica-Bold", 9),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ("TEXTCOLOR", (1, 0), (1, 0), colors.red),
        ("FONT", (1, 0), (1, 0), "Helvetica-Bold", 9),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story += [t_vitals, Spacer(1, 8)]

    story.append(Paragraph("CHEST X-RAY FINDINGS", st["SectionTitle"]))
    story.append(Paragraph(
        "<b>PA Chest X-Ray — 05-Mar-2026:</b> Right lower lobe consolidation with air bronchograms clearly visible. "
        "Blunting of the right costophrenic angle suggestive of a small right pleural effusion. "
        "Left lung clear. No pneumothorax. Cardiac silhouette normal. "
        "<b>Impression: Right lower lobe consolidation — Community-Acquired Pneumonia.</b>",
        st["Body"]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("LABORATORY RESULTS", st["SectionTitle"]))
    lab_headers = ["Test", "Result", "Normal Range", "Unit", "Flag"]
    lab_rows = [
        ["WBC Count",         "18,400", "4000 – 11000",  "cells/µL", "HIGH ↑↑"],
        ["Neutrophils",       "82",     "40 – 70",        "%",        "HIGH ↑"],
        ["CRP",               "142",    "< 5.0",          "mg/L",     "HIGH ↑↑"],
        ["Procalcitonin (PCT)","2.8",   "< 0.1",          "ng/mL",    "HIGH ↑↑"],
        ["ESR",               "88",     "< 20",           "mm/hr",    "HIGH ↑"],
        ["Haemoglobin",       "12.1",   "12.0 – 16.0",    "g/dL",     "Normal"],
        ["Lactate",           "2.1",    "0.5 – 1.6",      "mmol/L",   "HIGH ↑"],
        ["Sodium",            "134",    "135 – 145",      "mEq/L",    "LOW ↓"],
        ["Creatinine",        "0.9",    "0.5 – 1.1",      "mg/dL",    "Normal"],
        ["Blood Culture",     "Pending","Negative",       "",          "Pending"],
        ["Sputum Culture",    "Gram-positive cocci in clusters", "Negative", "", "Abnormal"],
    ]
    story.append(lab_table(st, lab_headers, lab_rows, abnormal_rows=[0,1,2,3,4,6,7,10]))
    story.append(Spacer(1, 8))

    story += [
        Paragraph("CLINICAL NOTES", st["SectionTitle"]),
        Paragraph(
            "Clinical, radiological, and laboratory findings are consistent with moderate-severity Community-Acquired "
            "Pneumonia (CAP) affecting the right lower lobe. The markedly elevated WBC (18,400), CRP (142 mg/L), "
            "and PCT (2.8 ng/mL) indicate significant bacterial infection. Sputum showing gram-positive cocci in "
            "clusters raises suspicion for Streptococcus pneumoniae or Staphylococcus aureus. "
            "Mildly elevated lactate (2.1 mmol/L) warrants monitoring for early sepsis. "
            "CRB-65 score of 2 indicates moderate severity — hospital admission and parenteral antibiotics indicated. "
            "Initiated: IV Amoxicillin-Clavulanate 1.2g TDS + Azithromycin 500 mg OD. "
            "Awaiting blood and sputum culture sensitivity. Physiotherapy for chest clearance initiated.",
            st["Body"]),
        Spacer(1, 8),
        Paragraph("PRELIMINARY DIAGNOSIS", st["SectionTitle"]),
        Paragraph("Community-Acquired Pneumonia (CAP) — Right Lower Lobe, Moderate Severity (CRB-65: 2). "
                  "Suspected bacterial aetiology. Small right pleural effusion. Monitor for sepsis.", st["Abnormal"]),
    ]

    doc.build(story)
    print(f"  ✅ Generated: {path}")
    return path


# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print(f"\nMediCascade AI — Synthetic Data Generator")
    print(f"Output directory: {OUTPUT_DIR}")
    print("=" * 55)
    generate_case_diabetes()
    generate_case_ami()
    generate_case_brain_tumor()
    generate_case_ckd()
    generate_case_pneumonia()
    print("=" * 55)
    print(f"\n✅ All 5 synthetic patient PDFs generated in: {OUTPUT_DIR}")
    print("\nCases:")
    print("  1. case_01_type2_diabetes.pdf         — Type 2 DM (HbA1c 8.7%)")
    print("  2. case_02_myocardial_infarction.pdf  — STEMI (Troponin 8.42)")
    print("  3. case_03_brain_tumor_glioblastoma.pdf — GBM WHO Grade IV (4.8 cm)")
    print("  4. case_04_chronic_kidney_disease.pdf — CKD Stage 3b (eGFR 31)")
    print("  5. case_05_pneumonia.pdf              — CAP Right Lower Lobe")
