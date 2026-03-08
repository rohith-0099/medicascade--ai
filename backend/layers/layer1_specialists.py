import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List

from config import settings
from schemas import CaseDocument, Layer1Findings, SpecialistView

try:
    from groq import Groq
except ImportError:
    Groq = None

from specialists.scan_analyzer import scan_analyzer  # vision specialist (MedGemma)


class Layer1Specialists:
    """
    Layer 1 — multi-model specialists.
    Produces independent structured JSON "views" from the same extracted facts.
    Roles:
      - notes            → symptom timeline + impressions
      - labs             → abnormal labs + patterns
      - medication       → meds list + interaction risks
      - history_genetics → comorbidities / inherited risks
      - exposure         → work/environment risks
      - imaging (if images exist) → radiology-style findings
    """

    def __init__(self):
        self.groq_client = None
        if settings.GROQ_API_KEY and Groq:
            try:
                self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
            except Exception as e:
                print(f"[Layer 1] Groq client init failed, fallback mode enabled: {e}")
        self.model = settings.GROQ_MODEL
        print(f"[Layer 1] Text specialist model: {self.model} (Groq)")

    # ── public API ──────────────────────────────────────────────────────────
    def process(self, case: CaseDocument) -> Layer1Findings:
        tasks = {
            "notes": lambda: self._notes_agent(case),
            "labs": lambda: self._labs_agent(case),
            "medication": lambda: self._meds_agent(case),
            "history_genetics": lambda: self._history_agent(case),
            "exposure": lambda: self._exposure_agent(case),
        }
        if case.facts.images:
            tasks["imaging"] = lambda: self._imaging_agent(case)

        views: List[SpecialistView] = []
        with ThreadPoolExecutor(max_workers=len(tasks)) as pool:
            future_map = {pool.submit(fn): name for name, fn in tasks.items()}
            for future in as_completed(future_map):
                name = future_map[future]
                try:
                    view = future.result()
                    views.append(view)
                    print(f"[Layer 1] [OK] {name} view ready ({view.confidence:.0%})")
                except Exception as e:
                    print(f"[Layer 1] [FAIL] {name} failed: {e}")
                    views.append(
                        SpecialistView(
                            agent=name,
                            role=f"{name} agent",
                            model=self.model if name != "imaging" else settings.HF_VISION_MODEL,
                            confidence=0.0,
                            findings={"error": str(e)},
                        )
                    )

        contract = self._build_contract_fields(views)
        findings = Layer1Findings(
            case_id=case.case_id,
            views=views,
            candidate_diagnoses=contract["candidate_diagnoses"],
            red_flags=contract["red_flags"],
            abnormal_labs=contract["abnormal_labs"],
            symptom_timeline=contract["symptom_timeline"],
            risk_factors=contract["risk_factors"],
            aggregated_summary=self._aggregate_summary(views),
        )

        # Persist to case folder
        case_dir = os.path.join(settings.CASE_DIR, case.case_id)
        os.makedirs(case_dir, exist_ok=True)
        findings_path = os.path.join(case_dir, "layer1_findings.json")
        with open(findings_path, "w", encoding="utf-8") as f:
            json.dump(findings.model_dump(mode="json"), f, indent=2)
        findings.findings_json_path = findings_path
        print(f"[Layer 1] layer1_findings.json saved -> {findings_path}")
        return findings

    # ── agents ─────────────────────────────────────────────────────────────
    def _notes_agent(self, case: CaseDocument) -> SpecialistView:
        notes_text = self._compose_notes_context(case)
        prompt = (
            "You are the Notes agent. Read the clinical notes and produce JSON with keys: "
            "symptom_timeline (array of {time, symptom, severity?}), "
            "exam_findings (array of strings), impressions (array), "
            "red_flags (array). Keep it concise."
        )
        findings = self._llm_json(prompt, notes_text)
        findings = self._ensure_notes_fields(findings, notes_text)
        return SpecialistView(
            agent="notes",
            role="Symptom timeline + clinician impressions",
            model=self.model,
            confidence=findings.pop("_confidence", 0.7),
            findings=findings,
        )

    def _labs_agent(self, case: CaseDocument) -> SpecialistView:
        lab_lines = [f"{f.label}: {f.value}" for f in case.facts.labs]
        text = "\n".join(lab_lines) or case.raw_text[:1500]
        prompt = (
            "You are the Labs agent. Return JSON: {abnormal_labs:[{test,value,status}], "
            "patterns:[string], risk_flags:[string], primary_suspect:string}. "
            "Use status 'high'/'low' where possible."
        )
        findings = self._llm_json(prompt, text)
        findings = self._normalize_labs_findings(findings)
        heuristic = self._heuristic_lab_findings(case)
        for key in ("abnormal_labs", "patterns", "risk_flags", "primary_suspect"):
            if not findings.get(key):
                findings[key] = heuristic.get(key, [] if key != "primary_suspect" else "")
        if not findings.get("red_flags"):
            findings["red_flags"] = heuristic.get("red_flags", [])
        if not findings.get("differentials"):
            findings["differentials"] = heuristic.get("differentials", [])
        if not findings.get("_confidence"):
            findings["_confidence"] = heuristic.get("_confidence", 0.65)
        return SpecialistView(
            agent="labs",
            role="Laboratory interpretation",
            model=self.model,
            confidence=findings.pop("_confidence", 0.7),
            findings=findings,
        )

    def _meds_agent(self, case: CaseDocument) -> SpecialistView:
        meds_text = "\n".join(str(f.value) for f in case.facts.meds) or case.raw_text[:1200]
        prompt = (
            "You are the Medication agent. Extract current medications, allergies, "
            "and flag obvious interaction risks. JSON schema: "
            "{medications:[{name,dose?,route?}], allergies:[string], interactions:[string]}."
        )
        findings = self._llm_json(prompt, meds_text)
        return SpecialistView(
            agent="medication",
            role="Medication & allergy cross-check",
            model=self.model,
            confidence=findings.pop("_confidence", 0.65),
            findings=findings,
        )

    def _history_agent(self, case: CaseDocument) -> SpecialistView:
        hx_text = "\n".join(str(f.value) for f in case.facts.history) or case.raw_text[:1500]
        prompt = (
            "You are the History/Genetics agent. Summarize comorbidities, family history, "
            "and inherited risk flags. JSON: {comorbidities:[string], family_history:[string], "
            "inherited_risks:[string]}."
        )
        findings = self._llm_json(prompt, hx_text)
        return SpecialistView(
            agent="history_genetics",
            role="Comorbidities & inherited risk",
            model=self.model,
            confidence=findings.pop("_confidence", 0.65),
            findings=findings,
        )

    def _exposure_agent(self, case: CaseDocument) -> SpecialistView:
        prompt = (
            "You are the Exposure agent. From the text, identify occupational or environmental "
            "exposures worth considering. JSON: {exposures:[{agent, context, likelihood}], "
            "consider:[string]}."
        )
        findings = self._llm_json(prompt, case.raw_text[:1800])
        return SpecialistView(
            agent="exposure",
            role="Exposure-linked risks",
            model=self.model,
            confidence=findings.pop("_confidence", 0.55),
            findings=findings,
        )

    def _imaging_agent(self, case: CaseDocument) -> SpecialistView:
        if not settings.HF_API_TOKEN:
            return SpecialistView(
                agent="imaging",
                role="Imaging interpretation",
                model=settings.HF_VISION_MODEL,
                confidence=0.0,
                findings={"note": "HF_API_TOKEN missing; imaging agent skipped."},
                evidence=[],
            )

        # Reuse existing vision specialist; no Groq key required.
        opinion = scan_analyzer.analyze(case.facts.images)
        return SpecialistView(
            agent="imaging",
            role="Imaging interpretation",
            model=settings.HF_VISION_MODEL,
            confidence=opinion.confidence,
            findings={
                "radiology_findings": opinion.key_findings,
                "diagnosis": opinion.diagnosis,
                "reasoning": opinion.reasoning,
            },
            evidence=[],
        )

    # ── helpers ─────────────────────────────────────────────────────────────
    def _llm_json(self, system_prompt: str, content: str) -> Dict[str, Any]:
        if not content:
            return {}

        if self.groq_client:
            try:
                sampled_content = self._windowed_excerpt(content, max_chars=12000)
                resp = self.groq_client.chat.completions.create(
                    model=self.model,
                    temperature=0.2,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": sampled_content},
                    ],
                )
                raw = resp.choices[0].message.content
                return json.loads(raw)
            except Exception as e:
                print(f"[Layer 1] Groq JSON error: {e}")

        # Fallback heuristic: return minimal structure
        return {"raw_excerpt": content[:400], "_confidence": 0.3}

    def _compose_notes_context(self, case: CaseDocument) -> str:
        notes = "\n".join(str(f.value) for f in case.facts.notes if f.value)
        table_timeline_lines: List[str] = []
        for table in case.tables:
            headers = [str(h).lower() for h in table.get("headers", [])]
            if not any("symptom" in h for h in headers):
                continue
            for row in table.get("data", []):
                if not isinstance(row, dict):
                    continue
                time_part = ""
                symptom_part = ""
                severity_part = ""
                for k, v in row.items():
                    key = str(k).lower()
                    if "time" in key or "period" in key:
                        time_part = str(v)
                    elif "symptom" in key:
                        symptom_part = str(v)
                    elif "severity" in key:
                        severity_part = str(v)
                if symptom_part:
                    line = f"{time_part} | {symptom_part}".strip(" |")
                    if severity_part:
                        line += f" | severity: {severity_part}"
                    table_timeline_lines.append(line)

        parts = [chunk for chunk in [notes, "\n".join(table_timeline_lines), case.raw_text] if chunk]
        return self._windowed_excerpt("\n\n".join(parts), max_chars=14000)

    def _windowed_excerpt(self, text: str, max_chars: int = 12000) -> str:
        if len(text) <= max_chars:
            return text
        section = max_chars // 3
        head = text[:section]
        mid_start = max(0, len(text) // 2 - section // 2)
        mid = text[mid_start:mid_start + section]
        tail = text[-section:]
        return "\n...\n".join([head, mid, tail])

    def _coerce_to_string_list(self, value: Any) -> List[str]:
        if isinstance(value, list):
            out: List[str] = []
            for item in value:
                if isinstance(item, str):
                    if item.strip():
                        out.append(item.strip())
                elif isinstance(item, dict) and item:
                    out.append(", ".join([f"{k}: {v}" for k, v in item.items()][:3]))
                elif item:
                    out.append(str(item))
            return out
        if isinstance(value, str):
            parts = [part.strip() for part in value.replace("\n", ",").split(",")]
            return [part for part in parts if part]
        return []

    def _normalize_labs_findings(self, findings: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(findings, dict):
            normalized: Dict[str, Any] = {}
        else:
            normalized = dict(findings or {})
        for key in ("patterns", "risk_flags", "red_flags"):
            normalized[key] = self._coerce_to_string_list(normalized.get(key))

        differentials = normalized.get("differentials")
        if isinstance(differentials, str):
            normalized["differentials"] = self._coerce_to_string_list(differentials)
        elif not isinstance(differentials, list):
            normalized["differentials"] = []
        return normalized

    def _aggregate_summary(self, views: List[SpecialistView]) -> Dict[str, Any]:
        summary = {
            "agents_run": [v.agent for v in views],
            "weak_spots": [v.agent for v in views if v.confidence < 0.4],
        }
        primary = next((v for v in views if v.agent == "labs" and v.findings.get("primary_suspect")), None)
        if primary:
            summary["candidate_primary"] = primary.findings.get("primary_suspect")
        return summary

    def _build_contract_fields(self, views: List[SpecialistView]) -> Dict[str, Any]:
        """
        Builds the required Layer-1 output contract:
          - candidate_diagnoses
          - red_flags
          - abnormal_labs
          - symptom_timeline
          - risk_factors
        """
        candidates: List[Dict[str, Any]] = []
        red_flags: List[str] = []
        abnormal_labs: List[Dict[str, Any]] = []
        symptom_timeline: List[Dict[str, Any]] = []
        risk_factors: List[str] = []

        for view in views:
            findings = view.findings or {}

            # Candidate diagnoses from each specialist
            diag = (
                findings.get("primary_suspect")
                or findings.get("diagnosis")
                or findings.get("top_diagnosis")
            )
            if diag:
                candidates.append(
                    {
                        "agent": view.agent,
                        "diagnosis": diag,
                        "confidence": view.confidence,
                    }
                )
            for diff in findings.get("differentials", []) if isinstance(findings.get("differentials"), list) else []:
                if isinstance(diff, dict) and diff.get("diagnosis"):
                    candidates.append(
                        {
                            "agent": view.agent,
                            "diagnosis": str(diff.get("diagnosis")),
                            "confidence": max(0.2, min(0.6, float(diff.get("confidence", 0.3) or 0.3))),
                        }
                    )
                elif isinstance(diff, str) and diff.strip():
                    candidates.append(
                        {
                            "agent": view.agent,
                            "diagnosis": diff.strip(),
                            "confidence": max(0.2, min(0.55, view.confidence * 0.6)),
                        }
                    )

            # Red flags
            red_flags.extend(self._coerce_to_string_list(findings.get("red_flags")))
            red_flags.extend(self._coerce_to_string_list(findings.get("risk_flags")))

            # Abnormal labs
            labs = findings.get("abnormal_labs")
            if isinstance(labs, list):
                for lab in labs:
                    if isinstance(lab, dict):
                        abnormal_labs.append(lab)
                    else:
                        abnormal_labs.append({"raw": str(lab)})

            # Symptom timeline (from notes agent)
            timeline = findings.get("symptom_timeline")
            if isinstance(timeline, list):
                for point in timeline:
                    if isinstance(point, dict):
                        symptom_timeline.append(point)

            # Risk factors (history, exposure, meds interactions)
            for key in ("inherited_risks", "consider", "interactions", "comorbidities"):
                vals = findings.get(key)
                risk_factors.extend(self._coerce_to_string_list(vals))

        # De-duplicate while preserving order
        dedup_red = list(dict.fromkeys(red_flags))
        dedup_risk = list(dict.fromkeys(risk_factors))
        ranked_candidates = sorted(candidates, key=lambda x: x.get("confidence", 0), reverse=True)
        dedup_candidates: List[Dict[str, Any]] = []
        seen_diags = set()
        for candidate in ranked_candidates:
            diag = str(candidate.get("diagnosis", "")).strip()
            if not diag:
                continue
            key = diag.lower()
            if key in seen_diags:
                continue
            seen_diags.add(key)
            dedup_candidates.append(candidate)

        if dedup_candidates:
            primary = dedup_candidates[0].get("diagnosis", "")
            for fallback in self._fallback_differentials(primary):
                if not any(c.get("diagnosis", "").lower() == fallback.lower() for c in dedup_candidates):
                    dedup_candidates.append(
                        {
                            "agent": "rule_fallback",
                            "diagnosis": fallback,
                            "confidence": 0.28,
                        }
                    )
                if len(dedup_candidates) >= 4:
                    break

        return {
            "candidate_diagnoses": dedup_candidates[:8],
            "red_flags": dedup_red[:20],
            "abnormal_labs": abnormal_labs[:40],
            "symptom_timeline": symptom_timeline[:40],
            "risk_factors": dedup_risk[:30],
        }

    def _ensure_notes_fields(self, findings: Dict[str, Any], notes_text: str) -> Dict[str, Any]:
        extracted_timeline = self._extract_symptom_timeline(notes_text)
        if not isinstance(findings.get("symptom_timeline"), list):
            findings["symptom_timeline"] = extracted_timeline
        else:
            findings["symptom_timeline"] = self._merge_timeline(findings["symptom_timeline"], extracted_timeline)

        if not isinstance(findings.get("red_flags"), list):
            findings["red_flags"] = self._extract_red_flags_from_text(notes_text)
        elif not findings["red_flags"]:
            findings["red_flags"] = self._extract_red_flags_from_text(notes_text)
        return findings

    def _extract_symptom_timeline(self, text: str) -> List[Dict[str, Any]]:
        import re

        timeline: List[Dict[str, Any]] = []
        if not text:
            return timeline

        symptom_aliases = {
            "fatigue": ["fatigue", "tired", "exhaustion"],
            "increased thirst": ["increased thirst", "polydipsia", "thirst"],
            "polyuria": ["polyuria", "frequent urination", "urination at night", "nocturia"],
            "blurred vision": ["blurred vision", "vision worsening", "visual symptoms"],
            "neuropathy symptoms": ["tingling", "numbness", "decreased sensation", "nerve pain"],
            "slow wound healing": ["slow healing", "wound healing"],
            "frequent infections": ["frequent infections", "recurrent infection"],
            "chest discomfort": ["chest discomfort", "chest pain"],
            "shortness of breath": ["shortness of breath", "breathlessness", "dyspnea"],
            "leg cramps": ["leg cramps", "muscle cramps"],
            "ankle swelling": ["ankle swelling", "pedal edema", "swelling in ankles"],
            "confusion": ["confusion", "altered mental status"],
        }

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        current_time = "unknown"

        for line in lines:
            low = line.lower()
            time_match = re.search(
                r"\b(\d+\s+(?:day|week|month|year)s?\s+ago|recent\s+months?|current(?:\s+presentation)?)\b",
                low,
            )
            if time_match:
                current_time = time_match.group(1)

            severity = "reported"
            if "critical" in low or "severe" in low:
                severity = "severe"
            elif "moderate" in low:
                severity = "moderate"
            elif "mild" in low:
                severity = "mild"

            for canonical, aliases in symptom_aliases.items():
                if any(alias in low for alias in aliases):
                    timeline.append(
                        {
                            "time": current_time,
                            "symptom": canonical,
                            "severity": severity,
                        }
                    )

        deduped: List[Dict[str, Any]] = []
        seen = set()
        for item in timeline:
            key = (item["time"], item["symptom"])
            if key in seen:
                continue
            seen.add(key)
            deduped.append(item)

        return deduped[:30]

    def _merge_timeline(self, existing: List[Dict[str, Any]], extracted: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        merged: List[Dict[str, Any]] = []
        seen = set()
        for item in (existing or []) + (extracted or []):
            if not isinstance(item, dict):
                continue
            symptom = str(item.get("symptom", "")).strip()
            time_tag = str(item.get("time", "unknown")).strip() or "unknown"
            if not symptom:
                continue
            key = (time_tag.lower(), symptom.lower())
            if key in seen:
                continue
            seen.add(key)
            merged.append(
                {
                    "time": time_tag,
                    "symptom": symptom,
                    "severity": str(item.get("severity", "reported")),
                }
            )
        return merged[:40]

    def _fallback_differentials(self, primary: str) -> List[str]:
        primary_low = str(primary or "").lower()
        if "diabetes" in primary_low:
            return [
                "Type 1 diabetes mellitus (adult-onset/LADA)",
                "Secondary diabetes due to endocrine disorder",
                "Stress hyperglycemia with metabolic syndrome",
            ]
        if "renal" in primary_low or "kidney" in primary_low:
            return [
                "Diabetic kidney disease",
                "Hypertensive nephropathy",
                "Acute kidney injury on chronic kidney disease",
            ]
        if "myocard" in primary_low or "cardiac" in primary_low:
            return [
                "Unstable angina",
                "Myocarditis",
                "Demand ischemia secondary to metabolic stress",
            ]
        return [
            "Metabolic syndrome",
            "Inflammatory systemic process",
            "Endocrine disorder requiring targeted workup",
        ]

    def _extract_red_flags_from_text(self, text: str) -> List[str]:
        low = text.lower()
        rules = [
            ("severe chest pain", "Possible acute coronary syndrome"),
            ("shortness of breath", "Respiratory compromise risk"),
            ("altered mental status", "Neurologic emergency concern"),
            ("very high fever", "Potential severe infection"),
            ("focal neurological deficit", "Potential stroke/space-occupying lesion"),
            ("confusion", "Altered cognition requires urgent metabolic and neurologic review"),
            ("severe fatigue", "Severe fatigue may indicate systemic decompensation"),
            ("pedal edema", "Volume overload or cardiac/renal decompensation risk"),
        ]
        flags: List[str] = []
        for needle, msg in rules:
            if needle in low:
                flags.append(msg)
        return flags

    def _heuristic_lab_findings(self, case: CaseDocument) -> Dict[str, Any]:
        import re

        labs: Dict[str, float] = {}
        abnormal_labs: List[Dict[str, Any]] = []
        patterns: List[str] = []
        risk_flags: List[str] = []
        red_flags: List[str] = []

        for fact in case.facts.labs:
            label = str(fact.label).lower()
            value_text = str(fact.value)
            num_match = re.search(r"-?\d+(?:\.\d+)?", value_text)
            if not num_match:
                continue
            value = float(num_match.group(0))
            labs[label] = value

            # Generic abnormal marker thresholds (best-effort fallback)
            if ("glucose" in label and value >= 126) or ("hba1c" in label and value >= 6.5):
                abnormal_labs.append({"test": fact.label, "value": value_text, "status": "high"})
            if ("troponin" in label and value > 0.04) or ("ck-mb" in label and value > 5):
                abnormal_labs.append({"test": fact.label, "value": value_text, "status": "high"})
            if ("creatinine" in label and value > 1.3) or ("egfr" in label and value < 60):
                abnormal_labs.append({"test": fact.label, "value": value_text, "status": "abnormal"})
            if ("wbc" in label and value > 11000):
                abnormal_labs.append({"test": fact.label, "value": value_text, "status": "high"})
            if ("ceruloplasmin" in label and value < 20):
                abnormal_labs.append({"test": fact.label, "value": value_text, "status": "low"})
            if ("urine copper" in label and value > 100):
                abnormal_labs.append({"test": fact.label, "value": value_text, "status": "high"})
            if ("ldl" in label and value >= 160) or ("triglyceride" in label and value >= 300):
                abnormal_labs.append({"test": fact.label, "value": value_text, "status": "high"})

        raw = case.raw_text.lower()
        primary = ""

        diabetic = any(("glucose" in k and v >= 126) for k, v in labs.items()) or any(("hba1c" in k and v >= 6.5) for k, v in labs.items())
        mi = any(("troponin" in k and v > 0.04) for k, v in labs.items()) or "st elevation" in raw
        ckd = any(("creatinine" in k and v > 1.3) for k, v in labs.items()) or any(("egfr" in k and v < 60) for k, v in labs.items())
        pneumonia = ("cough" in raw and "fever" in raw and any(("wbc" in k and v > 11000) for k, v in labs.items()))
        wilson = any(("ceruloplasmin" in k and v < 20) for k, v in labs.items()) or any(("urine copper" in k and v > 100) for k, v in labs.items())
        tumor = "glioblastoma" in raw or "brain mass" in raw or "tumor" in raw

        if wilson:
            primary = "Wilson disease (suspected)"
            patterns.append("Low ceruloplasmin and/or elevated urine copper pattern")
            risk_flags.append("Potential hepatic/neurologic progression risk")
        elif mi:
            primary = "Acute myocardial infarction (suspected)"
            patterns.append("Cardiac injury marker elevation pattern")
            risk_flags.append("Cardiac emergency red flag")
        elif diabetic:
            primary = "Uncontrolled type 2 diabetes mellitus"
            patterns.append("Hyperglycemia pattern")
            risk_flags.append("Metabolic decompensation risk")
        elif ckd:
            primary = "Chronic kidney disease (suspected)"
            patterns.append("Renal impairment pattern")
            risk_flags.append("Progressive renal dysfunction risk")
        elif pneumonia:
            primary = "Infective pneumonia (suspected)"
            patterns.append("Infection/inflammation pattern")
            risk_flags.append("Respiratory deterioration risk")
        elif tumor:
            primary = "Intracranial neoplasm (suspected)"
            patterns.append("Imaging/neuro-oncology pattern")
            risk_flags.append("Neurologic compromise risk")
        else:
            primary = "Metabolic or inflammatory disorder (needs validation)"
            if not patterns:
                patterns.append("Non-specific lab abnormality pattern")

        if not abnormal_labs and case.facts.labs:
            # Ensure downstream contract always has meaningful items.
            for fact in case.facts.labs[:6]:
                abnormal_labs.append({"test": fact.label, "value": str(fact.value), "status": "review"})

        hba1c = next((v for k, v in labs.items() if "hba1c" in k), None)
        fbg = next((v for k, v in labs.items() if "fasting" in k and "glucose" in k), None)
        ppg = next((v for k, v in labs.items() if ("post" in k and "glucose" in k) or "pp glucose" in k), None)
        ldl = next((v for k, v in labs.items() if "ldl" in k), None)
        tg = next((v for k, v in labs.items() if "triglyceride" in k), None)

        confidence = 0.62
        if hba1c is not None and hba1c >= 10 and ((fbg is not None and fbg >= 200) or (ppg is not None and ppg >= 300)):
            confidence = 0.92
        elif hba1c is not None and hba1c >= 8:
            confidence = 0.84
        elif diabetic:
            confidence = 0.75

        if hba1c is not None and hba1c >= 10:
            red_flags.append("HbA1c >= 10% indicates critical chronic hyperglycemia.")
        if ppg is not None and ppg >= 300:
            red_flags.append("Post-prandial glucose >= 300 mg/dL indicates severe uncontrolled diabetes.")
        if fbg is not None and fbg >= 200:
            red_flags.append("Fasting blood glucose >= 200 mg/dL indicates severe hyperglycemia.")
        if ldl is not None and ldl >= 160:
            red_flags.append("LDL >= 160 mg/dL indicates high cardiovascular risk.")
        if tg is not None and tg >= 300:
            red_flags.append("Triglycerides >= 300 mg/dL indicate pancreatitis and cardiovascular risk.")

        differentials = [
            {
                "diagnosis": diag,
                "confidence": 0.28 - (index * 0.04),
                "reason": "Rule-out diagnosis generated by deterministic fallback.",
            }
            for index, diag in enumerate(self._fallback_differentials(primary)[:3])
        ]

        return {
            "abnormal_labs": abnormal_labs[:20],
            "patterns": patterns[:8],
            "risk_flags": risk_flags[:8],
            "red_flags": red_flags[:8],
            "differentials": differentials,
            "primary_suspect": primary,
            "_confidence": confidence,
        }


layer1_specialists = Layer1Specialists()
