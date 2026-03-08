"""
ICD-10-CM code mapper for common diagnoses.
Uses a local lookup table — no external API or API key required.
Performs exact → partial → keyword fuzzy matching.
"""
import re
from typing import Tuple

# (ICD-10-CM code, official description)
_ICD10: dict = {
    # ── Metabolic / Endocrine ─────────────────────────────────────────────
    "type 2 diabetes mellitus": ("E11.9",  "Type 2 diabetes mellitus without complications"),
    "type 1 diabetes mellitus": ("E10.9",  "Type 1 diabetes mellitus without complications"),
    "uncontrolled type 2 diabetes": ("E11.65", "Type 2 diabetes mellitus with hyperglycemia"),
    "uncontrolled type 2 diabetes mellitus": ("E11.65", "Type 2 diabetes mellitus with hyperglycemia"),
    "type 2 diabetes with hyperglycemia": ("E11.65", "Type 2 diabetes mellitus with hyperglycemia"),
    "diabetic ketoacidosis": ("E11.10", "Type 2 diabetes mellitus with ketoacidosis"),
    "hypoglycemia": ("E16.0",  "Drug-induced hypoglycemia without coma"),
    "metabolic syndrome": ("E88.81", "Metabolic syndrome"),
    "hypothyroidism": ("E03.9",  "Hypothyroidism, unspecified"),
    "hyperthyroidism": ("E05.90", "Thyrotoxicosis, unspecified, without crisis"),
    "cushing syndrome": ("E24.9",  "Cushing syndrome, unspecified"),
    "cushing's syndrome": ("E24.9", "Cushing syndrome, unspecified"),
    "obesity": ("E66.9",   "Obesity, unspecified"),
    "dyslipidemia": ("E78.5",  "Hyperlipidemia, unspecified"),
    "hyperlipidemia": ("E78.5",  "Hyperlipidemia, unspecified"),
    "hypertriglyceridemia": ("E78.1",  "Pure hyperglyceridemia"),
    "wilson disease": ("E83.01", "Wilson's disease"),
    "wilson's disease": ("E83.01", "Wilson's disease"),
    # ── Cardiovascular ────────────────────────────────────────────────────
    "acute myocardial infarction": ("I21.9",  "Acute myocardial infarction, unspecified"),
    "myocardial infarction": ("I21.9",  "Acute myocardial infarction, unspecified"),
    "stemi": ("I21.3",  "ST elevation myocardial infarction of unspecified site"),
    "nstemi": ("I21.4",  "Non-ST elevation myocardial infarction"),
    "heart failure": ("I50.9",  "Heart failure, unspecified"),
    "congestive heart failure": ("I50.9", "Heart failure, unspecified"),
    "hypertension": ("I10",    "Essential (primary) hypertension"),
    "essential hypertension": ("I10", "Essential (primary) hypertension"),
    "atrial fibrillation": ("I48.91", "Unspecified atrial fibrillation"),
    "unstable angina": ("I20.0",  "Unstable angina"),
    "stable angina": ("I20.9",  "Angina pectoris, unspecified"),
    "stroke": ("I63.9",  "Cerebral infarction, unspecified"),
    "ischemic stroke": ("I63.9",  "Cerebral infarction, unspecified"),
    "transient ischemic attack": ("G45.9", "Transient cerebral ischemic attack, unspecified"),
    "tia": ("G45.9",  "Transient cerebral ischemic attack, unspecified"),
    "pulmonary embolism": ("I26.99", "Other pulmonary embolism without acute cor pulmonale"),
    "deep vein thrombosis": ("I82.409", "Acute deep vein thrombosis of unspecified deep vessels"),
    "dvt": ("I82.409", "Acute deep vein thrombosis of unspecified deep vessels"),
    "aortic stenosis": ("I35.0",  "Nonrheumatic aortic (valve) stenosis"),
    "peripheral artery disease": ("I73.9", "Peripheral vascular disease, unspecified"),
    # ── Renal ─────────────────────────────────────────────────────────────
    "chronic kidney disease": ("N18.9",  "Chronic kidney disease, unspecified"),
    "ckd": ("N18.9",  "Chronic kidney disease, unspecified"),
    "ckd stage 1": ("N18.1",  "Chronic kidney disease, stage 1"),
    "ckd stage 2": ("N18.2",  "Chronic kidney disease, stage 2 (mild)"),
    "ckd stage 3": ("N18.3",  "Chronic kidney disease, stage 3 (moderate)"),
    "ckd stage 4": ("N18.4",  "Chronic kidney disease, stage 4 (severe)"),
    "ckd stage 5": ("N18.5",  "Chronic kidney disease, stage 5"),
    "end stage renal disease": ("N18.6", "End-stage renal disease"),
    "esrd": ("N18.6",  "End-stage renal disease"),
    "acute kidney injury": ("N17.9",  "Acute kidney failure, unspecified"),
    "acute renal failure": ("N17.9",  "Acute kidney failure, unspecified"),
    "renal failure": ("N17.9",  "Acute kidney failure, unspecified"),
    "diabetic nephropathy": ("E11.65", "Type 2 diabetes mellitus with hyperglycemia"),
    "nephrotic syndrome": ("N04.9",  "Nephrotic syndrome with unspecified morphologic changes"),
    "nephrolithiasis": ("N20.0",  "Calculus of kidney"),
    # ── Respiratory ───────────────────────────────────────────────────────
    "pneumonia": ("J18.9",  "Pneumonia, unspecified organism"),
    "community-acquired pneumonia": ("J18.9", "Pneumonia, unspecified organism"),
    "hospital-acquired pneumonia": ("J15.9", "Unspecified bacterial pneumonia"),
    "copd": ("J44.1",  "COPD with acute exacerbation"),
    "chronic obstructive pulmonary disease": ("J44.1", "COPD with acute exacerbation"),
    "asthma": ("J45.50", "Severe persistent asthma, uncomplicated"),
    "pulmonary edema": ("J81.1",  "Chronic pulmonary edema"),
    "pleural effusion": ("J90",   "Pleural effusion, not elsewhere classified"),
    "pulmonary fibrosis": ("J84.10", "Pulmonary fibrosis, unspecified"),
    "lung cancer": ("C34.90", "Malignant neoplasm of unspecified part of bronchus and lung"),
    "covid-19": ("U07.1",  "COVID-19"),
    "covid": ("U07.1",  "COVID-19"),
    # ── Neurological ──────────────────────────────────────────────────────
    "glioblastoma": ("C71.9",  "Malignant neoplasm of brain, unspecified"),
    "glioblastoma multiforme": ("C71.9", "Malignant neoplasm of brain, unspecified"),
    "brain tumor": ("C71.9",  "Malignant neoplasm of brain, unspecified"),
    "intracranial neoplasm": ("C71.9", "Malignant neoplasm of brain, unspecified"),
    "brain mass": ("C71.9",  "Malignant neoplasm of brain, unspecified"),
    "meningioma": ("D32.9",  "Benign neoplasm of meninges, unspecified"),
    "epilepsy": ("G40.909", "Unspecified epilepsy, not intractable"),
    "seizure disorder": ("G40.909", "Unspecified epilepsy, not intractable"),
    "alzheimer's disease": ("G30.9",  "Alzheimer's disease, unspecified"),
    "alzheimer disease": ("G30.9",  "Alzheimer's disease, unspecified"),
    "parkinson's disease": ("G20",   "Parkinson's disease"),
    "parkinson disease": ("G20",   "Parkinson's disease"),
    "multiple sclerosis": ("G35",   "Multiple sclerosis"),
    "migraine": ("G43.909", "Migraine, unspecified, not intractable"),
    "peripheral neuropathy": ("G60.9", "Hereditary and idiopathic neuropathy, unspecified"),
    "diabetic neuropathy": ("E11.40", "Type 2 diabetes mellitus with diabetic neuropathy, unspecified"),
    # ── Gastrointestinal / Hepatic ────────────────────────────────────────
    "liver cirrhosis": ("K74.60", "Unspecified cirrhosis of liver"),
    "cirrhosis": ("K74.60", "Unspecified cirrhosis of liver"),
    "hepatitis b": ("B18.1",  "Chronic viral hepatitis B without delta-agent"),
    "hepatitis c": ("B18.2",  "Chronic viral hepatitis C"),
    "fatty liver disease": ("K76.0",  "Fatty change of liver"),
    "nafld": ("K76.0",  "Fatty change of liver"),
    "nash": ("K75.81", "Nonalcoholic steatohepatitis"),
    "pancreatitis": ("K85.9",  "Acute pancreatitis without necrosis or infection, unspecified"),
    "peptic ulcer": ("K27.9",  "Peptic ulcer, unspecified"),
    "inflammatory bowel disease": ("K52.9", "Noninfective gastroenteritis and colitis, unspecified"),
    "crohn's disease": ("K50.90", "Crohn's disease of small intestine without complications"),
    "ulcerative colitis": ("K51.90", "Ulcerative colitis, unspecified, without complications"),
    "colon cancer": ("C18.9",  "Malignant neoplasm of colon, unspecified"),
    # ── Infectious ────────────────────────────────────────────────────────
    "sepsis": ("A41.9",  "Sepsis, unspecified organism"),
    "septic shock": ("A41.9",  "Sepsis, unspecified organism"),
    "tuberculosis": ("A15.9",  "Respiratory tuberculosis, unspecified"),
    "hiv": ("B20",    "Human immunodeficiency virus disease"),
    "malaria": ("B54",    "Unspecified malaria"),
    "urinary tract infection": ("N39.0", "Urinary tract infection, site not specified"),
    "uti": ("N39.0",  "Urinary tract infection, site not specified"),
    # ── Oncology ──────────────────────────────────────────────────────────
    "breast cancer": ("C50.919", "Malignant neoplasm of unspecified site of unspecified female breast"),
    "prostate cancer": ("C61",   "Malignant neoplasm of prostate"),
    "lymphoma": ("C85.90", "Non-Hodgkin lymphoma, unspecified, unspecified site"),
    "leukemia": ("C95.90", "Leukemia, unspecified, not having achieved remission"),
    # ── Musculoskeletal ───────────────────────────────────────────────────
    "rheumatoid arthritis": ("M05.79", "Rheumatoid arthritis with rheumatoid factor of multiple sites"),
    "osteoarthritis": ("M19.90", "Primary osteoarthritis, unspecified site"),
    "osteoporosis": ("M81.0",  "Age-related osteoporosis without current pathological fracture"),
    "gout": ("M10.9",  "Gout, unspecified"),
    "lupus": ("M32.9",  "Systemic lupus erythematosus, unspecified"),
    # ── Mental Health ─────────────────────────────────────────────────────
    "depression": ("F32.9",  "Major depressive disorder, single episode, unspecified"),
    "anxiety": ("F41.9",  "Anxiety disorder, unspecified"),
    "schizophrenia": ("F20.9",  "Schizophrenia, unspecified"),
    "bipolar disorder": ("F31.9",  "Bipolar disorder, unspecified"),
    # ── Default ───────────────────────────────────────────────────────────
    "undetermined": ("R69",   "Illness, unspecified"),
}


def get_icd10_code(diagnosis: str) -> Tuple[str, str]:
    """
    Map a free-text diagnosis to an ICD-10-CM code.

    Returns (code, description).
    Falls back to R69 (Illness, unspecified) when no match found.
    """
    if not diagnosis:
        return ("R69", "Illness, unspecified")

    lower = re.sub(r"\s+", " ", diagnosis.lower().strip(" ."))

    # 1. Exact match
    if lower in _ICD10:
        return _ICD10[lower]

    # 2. Partial match: diagnosis key is a substring of input (or vice-versa)
    #    Pick the longest matching key for specificity.
    candidates = [
        (k, v) for k, v in _ICD10.items()
        if k in lower or lower in k
    ]
    if candidates:
        return max(candidates, key=lambda x: len(x[0]))[1]

    # 3. Keyword match: any word > 4 chars in the lookup key appears in input
    kw_candidates = []
    for k, v in _ICD10.items():
        words = [w for w in k.split() if len(w) > 4]
        if words and all(w in lower for w in words):
            kw_candidates.append((k, v))
    if kw_candidates:
        return max(kw_candidates, key=lambda x: len(x[0]))[1]

    # 4. Single keyword: at least one meaningful word matches
    for k, v in _ICD10.items():
        words = [w for w in k.split() if len(w) > 5]
        if words and any(w in lower for w in words):
            return v

    return ("R69", "Illness, unspecified")


def get_icd10_for_differential(differentials: list) -> list:
    """Enrich a list of differential dicts with ICD-10 codes."""
    enriched = []
    for d in differentials:
        if isinstance(d, dict):
            diag = d.get("diagnosis", "")
            code, desc = get_icd10_code(diag)
            enriched.append({**d, "icd10_code": code, "icd10_description": desc})
        else:
            enriched.append(d)
    return enriched
