import json
import os
import time
import uuid
from typing import Dict, Any, List

from schemas import (
    CaseDocument,
    CaseFacts,
    Fact,
    Layer0Result,
    PatientData,
    Provenance,
)
from utils.pdf_extractor import PDFExtractor
from utils.data_classifier import DataClassifier
from config import settings


class Layer0Processor:
    """
    Layer 0 — deterministic intake.
    Converts any hospital PDF into structured facts with provenance and stores
    a case bundle on disk:
      - case.json  (FHIR-ish facts + provenance)
      - images/    (extracted or provided scans)
    No AI reasoning occurs here.
    """

    def __init__(self):
        self.classifier = DataClassifier()

    def process(self, pdf_path: str, scan_path: str | None = None) -> Layer0Result:
        start = time.time()
        case_id = f"case_{int(start)}_{uuid.uuid4().hex[:6]}"
        pdf_id = os.path.splitext(os.path.basename(pdf_path))[0]

        print(f"[Layer 0] Ingesting PDF '{pdf_path}' as {case_id}")
        extractor = PDFExtractor(pdf_path)

        text, pdf_images = extractor.smart_extract()
        tables = extractor.extract_tables()

        # If a dedicated scan was supplied, prefer it over embedded images
        images = self._load_scan_or_pdf_images(scan_path, pdf_images)

        # Classify sections with lightweight heuristics
        sections = self.classifier.classify_sections(text)
        patient_info = self.classifier.extract_patient_info(sections.get("patient_demographics", "")) if sections.get("patient_demographics") else {}
        lab_results = self.classifier.extract_lab_values(sections.get("lab_results", "")) if sections.get("lab_results") else {}
        for table in tables:
            lab_results.update(self._extract_lab_from_table(table))
        flat_lab_results = {
            test: (value.get("value", "") if isinstance(value, dict) else value)
            for test, value in lab_results.items()
        }

        facts = self._build_case_facts(patient_info, lab_results, sections, images, pdf_id, tables)

        case_dir = os.path.join(settings.CASE_DIR, case_id)
        os.makedirs(case_dir, exist_ok=True)

        images_dir = self._persist_images(images, case_dir)

        from datetime import datetime

        provenance_map = [
            f.provenance for f in (
                facts.demographics + facts.labs + facts.vitals + facts.meds + facts.history + facts.notes
            ) if f.provenance
        ]

        case_doc = CaseDocument(
            case_id=case_id,
            pdf_id=pdf_id,
            source_pdf=os.path.basename(pdf_path),
            ingested_at=datetime.utcnow(),
            facts=facts,
            raw_text=text,
            tables=tables,
            provenance_map=provenance_map,
            images_dir=images_dir,
        )

        case_json_path = os.path.join(case_dir, "case.json")
        with open(case_json_path, "w", encoding="utf-8") as f:
            json.dump(case_doc.model_dump(mode="json"), f, indent=2)

        elapsed = time.time() - start
        print(f"[Layer 0] Structured case saved to {case_json_path} ({elapsed:.2f}s)")

        # Compatibility bridge for existing specialist modules
        patient_view = PatientData(
            patient_info=patient_info,
            symptoms=sections.get("symptoms", ""),
            lab_results=flat_lab_results,
            clinical_notes=sections.get("clinical_notes", ""),
            images=images,
            raw_text=text,
        )

        return Layer0Result(
            case=case_doc,
            patient_view=patient_view,
            case_json_path=case_json_path,
            images_dir=images_dir,
        )

    # ── helpers ────────────────────────────────────────────────────────────

    def _load_scan_or_pdf_images(self, scan_path: str | None, pdf_images: List[str]) -> List[str]:
        if scan_path:
            import base64
            try:
                with open(scan_path, "rb") as img_file:
                    encoded = base64.b64encode(img_file.read()).decode("utf-8")
                    print("[Layer 0] Using dedicated scan image for analysis")
                    return [encoded]
            except Exception as e:
                print(f"[Layer 0] Scan load error ({e}), falling back to embedded images")
        return pdf_images

    def _build_case_facts(
        self,
        patient_info: Dict[str, Any],
        lab_results: Dict[str, Any],
        sections: Dict[str, str],
        images: List[str],
        pdf_id: str,
        tables: List[Dict[str, Any]],
    ) -> CaseFacts:
        facts = CaseFacts()

        def prov(span: str, page: int = 1) -> Provenance:
            return Provenance(pdf_id=pdf_id, page=page, bbox=None, text_span=span[:140])

        # Demographics
        for key, val in patient_info.items():
            facts.demographics.append(Fact(label=key, value=val, provenance=prov(str(val))))

        # Labs
        for test, val in lab_results.items():
            page = 1
            value = val
            if isinstance(val, dict):
                value = val.get("value", "")
                page = int(val.get("page", 1) or 1)
            facts.labs.append(Fact(label=test, value=value, provenance=prov(f"{test}: {value}", page=page)))

        # Symptoms / clinical notes
        if sections.get("symptoms"):
            facts.notes.append(Fact(label="symptoms", value=sections["symptoms"], provenance=prov(sections["symptoms"])))
        if sections.get("clinical_notes"):
            facts.notes.append(Fact(label="clinical_notes", value=sections["clinical_notes"], provenance=prov(sections["clinical_notes"])))
        if not facts.notes and sections.get("other"):
            excerpt = sections["other"][:6000]
            facts.notes.append(Fact(label="other_notes", value=excerpt, provenance=prov(excerpt)))

        # Vitals — quick regex pass for BP/HR/Temp inside any text block
        vitals_text = sections.get("vital_signs", "") or sections.get("clinical_notes", "") or sections.get("other", "")
        facts.vitals.extend(self._extract_vitals(vitals_text, pdf_id))

        # Meds / history (best-effort from notes)
        if sections.get("medications"):
            facts.meds.append(Fact(label="medications", value=sections["medications"], provenance=prov(sections["medications"])))
        history_text = sections.get("history") or sections.get("medical_history", "")
        if history_text:
            facts.history.append(Fact(label="history", value=history_text, provenance=prov(history_text)))

        # Bring timeline and medication tables into structured facts.
        self._append_table_context_facts(facts, tables, pdf_id)

        facts.images = images
        return facts

    def _extract_lab_from_table(self, table: Dict[str, Any]) -> Dict[str, Any]:
        lab_data: Dict[str, Any] = {}
        headers = table.get("headers", [])
        rows = table.get("data", [])

        test_col = None
        value_col = None

        for i, header in enumerate(headers):
            header_lower = str(header).lower()
            if any(k in header_lower for k in ["test", "parameter", "name"]):
                test_col = header
            if any(k in header_lower for k in ["value", "result", "level"]):
                value_col = header

        if test_col and value_col:
            for row in rows:
                if test_col in row and value_col in row:
                    test_name = str(row[test_col]).strip()
                    test_value = str(row[value_col]).strip()
                    if test_name and test_value:
                        lab_data[test_name] = {"value": test_value, "page": int(table.get("page", 1) or 1)}
        return lab_data

    def _append_table_context_facts(self, facts: CaseFacts, tables: List[Dict[str, Any]], pdf_id: str) -> None:
        def clean(value: Any) -> str:
            text = str(value or "").replace("(cid:127)", " ").strip()
            return " ".join(text.split())

        for table in tables:
            headers = [str(h).lower() for h in table.get("headers", [])]
            rows = table.get("data", [])
            page = int(table.get("page", 1) or 1)

            has_symptoms = any("symptom" in h for h in headers)
            has_meds = any("medication" in h or "dosage" in h for h in headers)
            has_history = any("medical condition" in h or "family history" in h or "relation" in h for h in headers)
            if not any([has_symptoms, has_meds, has_history]):
                continue

            for row in rows:
                if not isinstance(row, dict):
                    continue
                if has_symptoms:
                    time_val = self._pick_row_value(row, ["time period", "period", "time"])
                    symptom_val = self._pick_row_value(row, ["symptoms reported", "symptoms", "chief complaints"])
                    severity_val = self._pick_row_value(row, ["severity"])
                    if symptom_val:
                        value = clean(f"{time_val}: {symptom_val}" if time_val else symptom_val)
                        if severity_val:
                            value = clean(f"{value}; severity: {severity_val}")
                        facts.notes.append(
                            Fact(
                                label="symptom_timeline",
                                value=value,
                                provenance=Provenance(pdf_id=pdf_id, page=page, bbox=None, text_span=value[:140]),
                            )
                        )
                if has_meds:
                    med_val = self._pick_row_value(row, ["medications prescribed", "medication", "dosage"])
                    if med_val:
                        value = clean(med_val)
                        facts.meds.append(
                            Fact(
                                label="medications",
                                value=value,
                                provenance=Provenance(pdf_id=pdf_id, page=page, bbox=None, text_span=value[:140]),
                            )
                        )
                if has_history:
                    history_val = self._pick_row_value(row, ["medical conditions", "notes", "relation"])
                    if history_val:
                        value = clean(history_val)
                        facts.history.append(
                            Fact(
                                label="history",
                                value=value,
                                provenance=Provenance(pdf_id=pdf_id, page=page, bbox=None, text_span=value[:140]),
                            )
                        )

    def _pick_row_value(self, row: Dict[str, Any], key_hints: List[str]) -> str:
        for key, value in row.items():
            key_low = str(key).lower()
            if any(hint in key_low for hint in key_hints):
                return str(value or "").strip()
        return ""

    def _persist_images(self, images: List[str], case_dir: str) -> str | None:
        if not images:
            return None
        import base64
        images_dir = os.path.join(case_dir, "images")
        os.makedirs(images_dir, exist_ok=True)
        for idx, img_b64 in enumerate(images):
            try:
                with open(os.path.join(images_dir, f"scan_{idx}.png"), "wb") as f:
                    f.write(base64.b64decode(img_b64))
            except Exception as e:
                print(f"[Layer 0] Failed to persist image {idx}: {e}")
        return images_dir

    def _extract_vitals(self, text: str, pdf_id: str) -> List[Fact]:
        """Lightweight regex vitals extractor: BP, HR, Temp, SpO2."""
        import re
        vitals: List[Fact] = []
        if not text:
            return vitals

        def pv(span: str) -> Provenance:
            return Provenance(pdf_id=pdf_id, page=1, bbox=None, text_span=span[:120])

        bp = re.search(r'(\d{2,3})/(\d{2,3})', text)
        if bp:
            val = f"{bp.group(1)}/{bp.group(2)}"
            vitals.append(Fact(label="blood_pressure", value=val, unit="mmHg", provenance=pv(val)))

        hr = re.search(r'(?:hr|heart rate|pulse)[:\s]+(\d{2,3})', text, re.IGNORECASE)
        if hr:
            val = hr.group(1)
            vitals.append(Fact(label="heart_rate", value=val, unit="bpm", provenance=pv(val)))

        temp = re.search(r'(?:temp|temperature)[:\s]+(\d{2}\.?\d*)', text, re.IGNORECASE)
        if temp:
            val = temp.group(1)
            vitals.append(Fact(label="temperature", value=val, unit="°C", provenance=pv(val)))

        spo2 = re.search(r'(?:spo2|oxygen saturation|sat)[:\s]+(\d{2})', text, re.IGNORECASE)
        if spo2:
            val = spo2.group(1)
            vitals.append(Fact(label="spo2", value=val, unit="%", provenance=pv(val)))

        return vitals


layer0_processor = Layer0Processor()
