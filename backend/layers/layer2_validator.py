import json
import os
import re
import textwrap
from typing import Any, Dict, List, Optional, Tuple

import requests

from config import settings
from schemas import CaseDocument, EvidenceSnippet, FinalAssessment, Layer1Findings, Provenance


class Layer2Validator:
    """
    Layer 2: evidence retrieval + validator ("truth check").
    Primary model: Groq llama-3.3-70b-versatile (fast, reliable)
    Fallback: OpenRouter free models
    """

    def __init__(self):
        self.base_url = settings.OPENROUTER_BASE_URL.rstrip("/")
        self.model = settings.OPENROUTER_VALIDATOR_MODEL
        self.api_key = settings.OPENROUTER_API_KEY
        self.groq_api_key = settings.GROQ_API_KEY
        self.groq_model = settings.GROQ_MODEL or "llama-3.3-70b-versatile"

        if self.groq_api_key:
            print(f"[Layer 2] Groq primary validator: {self.groq_model}")
        if self.api_key:
            print(f"[Layer 2] OpenRouter fallback: {self.model}")
        if not self.groq_api_key and not self.api_key:
            print("[Layer 2] No API keys set. Heuristic fallback will be used.")

    def process(self, case: CaseDocument, layer1: Layer1Findings) -> FinalAssessment:
        retrieval_context = self._retrieve_evidence_context(layer1)
        payload = self._build_payload(case, layer1, retrieval_context)

        errors: List[str] = []
        validator_source = ""
        result: Dict[str, Any] = {}

        # Try Groq first (fast, reliable), then OpenRouter as fallback
        if self.groq_api_key:
            result, err = self._call_groq(payload)
            if result:
                validator_source = f"groq:{self.groq_model}"
            elif err:
                errors.append(f"Groq failed: {err}")

        if not result and self.api_key:
            result, err = self._call_openrouter(payload)
            if result:
                validator_source = f"openrouter:{self.model}"
            elif err:
                errors.append(f"OpenRouter fallback failed: {err}")

        if not result and not self.groq_api_key and not self.api_key:
            errors.append("No API keys configured")

        if result:
            assessment = self._parse_validator_output(result, case.case_id)
            if not assessment.primary_diagnosis and not assessment.final_problem_list:
                errors.append("Validator response was empty or malformed")
                assessment = self._heuristic_result(
                    case,
                    layer1,
                    reason="; ".join(errors),
                    retrieval_context=retrieval_context,
                )
            else:
                assessment.decision_log = f"Validator source: {validator_source}\n{assessment.decision_log}"
        else:
            assessment = self._heuristic_result(
                case,
                layer1,
                reason="; ".join(errors) if errors else "Validator unavailable",
                retrieval_context=retrieval_context,
            )

        # Deterministic guards run on every path so high-risk labs and confidence are never dropped.
        assessment = self._merge_rule_based_guards(assessment, case, layer1, retrieval_context)
        self._persist_assessment(assessment, case.case_id)
        return assessment

    # ------------------------------------------------------------------ #
    # Evidence retrieval
    # ------------------------------------------------------------------ #
    def _retrieve_evidence_context(self, layer1: Layer1Findings) -> List[Dict[str, str]]:
        """
        Retrieves lightweight evidence links/snippets from trusted sources.
        This is kept short and passed into the validator prompt.
        """
        contexts: List[Dict[str, str]] = []

        diagnoses = [d.get("diagnosis", "") for d in layer1.candidate_diagnoses if d.get("diagnosis")]
        seed_terms = diagnoses[:2] if diagnoses else []
        if not seed_terms and layer1.red_flags:
            seed_terms = layer1.red_flags[:2]

        for term in seed_terms:
            contexts.extend(self._pubmed_links(term))
            contexts.append(
                {
                    "source": "NICE",
                    "title": f"NICE search: {term}",
                    "url": f"https://www.nice.org.uk/search?q={requests.utils.quote(term)}",
                    "snippet": "NICE guideline search result entry point.",
                }
            )
            contexts.append(
                {
                    "source": "WHO",
                    "title": f"WHO publications search: {term}",
                    "url": f"https://www.who.int/publications/i/search?query={requests.utils.quote(term)}",
                    "snippet": "WHO publications search result entry point.",
                }
            )

        return contexts[:12]

    def _pubmed_links(self, term: str) -> List[Dict[str, str]]:
        """Fetch real PubMed abstracts (not placeholder links)."""
        from utils.pubmed_client import get_evidence_for_diagnosis
        articles = get_evidence_for_diagnosis(term, max_results=3)
        out: List[Dict[str, str]] = []
        for art in articles:
            out.append({
                "source": "PubMed",
                "title":   art["title"],
                "url":     art["url"],
                "snippet": art["snippet"],   # real abstract excerpt
                "pmid":    art.get("pmid", ""),
                "journal": art.get("journal", ""),
                "year":    art.get("year", ""),
            })
        if not out:
            # Graceful fallback: search-page link (no fake snippet)
            import requests as _r
            q = _r.utils.quote(term)
            out.append({
                "source": "PubMed",
                "title":  f"PubMed search: {term}",
                "url":    f"https://pubmed.ncbi.nlm.nih.gov/?term={q}",
                "snippet": "Search PubMed for peer-reviewed evidence on this topic.",
            })
        return out

    # ------------------------------------------------------------------ #
    # LLM validator call
    # ------------------------------------------------------------------ #
    def _build_payload(
        self,
        case: CaseDocument,
        layer1: Layer1Findings,
        retrieval_context: List[Dict[str, str]],
    ) -> Dict[str, Any]:
        spec = textwrap.dedent(
            """
            You are Layer-2 Validator. Use only evidence-based reasoning.
            Return strict JSON with this schema:
            {
              "primary_diagnosis": "string",
              "confidence": 0.0,
              "final_problem_list": ["string"],
              "final_differentials": [{"diagnosis":"string","confidence":0.0,"reason":"string"}],
              "final_red_flags": ["string"],
              "supported_findings": ["string"],
              "uncertain_findings": ["string"],
              "contradicted_findings": ["string"],
              "missing_data": ["string"],
              "evidence_pack": [
                {
                  "source":"PubMed|NICE|WHO",
                  "title":"string",
                  "url":"https://...",
                  "snippet":"short snippet",
                  "claim":"string",
                  "verdict":"supported|uncertain|contradicted"
                }
              ],
              "highlight_targets":[{"page":1,"text_span":"exact phrase from source PDF"}]
            }
            Rules:
            - Every major decision must have at least one evidence_pack item.
            - If evidence is weak, mark uncertain and add to missing_data.
            - Do not invent sources or URLs.
            """
        ).strip()

        # Truncate case_facts to stay under Groq's token limit (~12k)
        facts_dump = case.facts.model_dump(mode="json")
        # Keep only essential fields, drop verbose raw text
        compact_facts = {
            "demographics": facts_dump.get("demographics", {}),
            "vitals": facts_dump.get("vitals", {}),
            "labs": facts_dump.get("labs", [])[:20],
            "medications": facts_dump.get("medications", [])[:15],
            "history": facts_dump.get("history", [])[:10],
        }

        # Summarize views — only include agent name, top findings (not full text)
        compact_views = []
        for v in layer1.views[:4]:
            vd = v.model_dump(mode="json")
            compact_views.append({
                "agent": vd.get("agent", ""),
                "role": vd.get("role", ""),
                "confidence": vd.get("confidence", 0),
                "findings": str(vd.get("findings", ""))[:400],
            })

        user_payload = {
            "case_id": case.case_id,
            "case_facts": compact_facts,
            "layer1_findings": {
                "candidate_diagnoses": layer1.candidate_diagnoses[:5],
                "red_flags": layer1.red_flags[:8],
                "abnormal_labs": layer1.abnormal_labs[:10],
                "symptom_timeline": layer1.symptom_timeline[:6],
                "risk_factors": layer1.risk_factors[:8],
                "views": compact_views,
            },
            "retrieval_context": retrieval_context[:6],
        }

        return {
            "model": self.model,
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": spec},
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
            ],
        }

    def _call_openrouter(self, payload: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
        url = f"{self.base_url}/chat/completions"
        try:
            resp = requests.post(
                url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://medi-cascade.local",
                    "X-Title": "MediCascade Validator",
                },
                json=payload,
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            parsed = self._coerce_json_content(content)
            if not parsed:
                return {}, "response did not contain valid JSON"
            return parsed, ""
        except Exception as e:
            message = str(e)
            if hasattr(e, "response") and getattr(e, "response", None) is not None:
                body = getattr(e.response, "text", "")
                if body:
                    message = f"{message} | body={body[:300]}"
            print(f"[Layer 2] OpenRouter error: {message}")
            return {}, message

    def _call_groq(self, payload: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
        if not self.groq_api_key:
            return {}, "GROQ_API_KEY missing"
        try:
            groq_payload = {
                "model": self.groq_model,
                "temperature": 0.1,
                "response_format": {"type": "json_object"},
                "messages": payload.get("messages", []),
            }
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.groq_api_key}",
                    "Content-Type": "application/json",
                },
                json=groq_payload,
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            parsed = self._coerce_json_content(content)
            if not parsed:
                return {}, "response did not contain valid JSON"
            return parsed, ""
        except Exception as e:
            message = str(e)
            if hasattr(e, "response") and getattr(e, "response", None) is not None:
                body = getattr(e.response, "text", "")
                if body:
                    message = f"{message} | body={body[:300]}"
            print(f"[Layer 2] Groq fallback error: {message}")
            return {}, message

    # ------------------------------------------------------------------ #
    # Output parsing
    # ------------------------------------------------------------------ #
    def _parse_validator_output(self, data: Dict[str, Any], case_id: str) -> FinalAssessment:
        evidence_pack = [
            EvidenceSnippet(
                source=item.get("source", "unknown"),
                title=item.get("title", ""),
                url=item.get("url", ""),
                snippet=item.get("snippet", ""),
            )
            for item in data.get("evidence_pack", [])
            if isinstance(item, dict)
        ]

        highlight_targets = [
            Provenance(
                pdf_id="source_pdf",
                page=int(item.get("page", 1)),
                bbox=None,
                text_span=item.get("text_span", ""),
            )
            for item in data.get("highlight_targets", [])
            if isinstance(item, dict)
        ]

        return FinalAssessment(
            case_id=case_id,
            final_problem_list=data.get("final_problem_list", []),
            final_differentials=data.get("final_differentials", []),
            final_red_flags=data.get("final_red_flags", []),
            supported_findings=data.get("supported_findings", []),
            uncertain_findings=data.get("uncertain_findings", []),
            contradicted_findings=data.get("contradicted_findings", []),
            missing_data=data.get("missing_data", []),
            evidence_pack=evidence_pack,
            highlight_targets=highlight_targets,
            decision_log=json.dumps(data, indent=2),
            primary_diagnosis=data.get("primary_diagnosis"),
            confidence=max(0.0, min(1.0, float(data.get("confidence", 0.0) or 0.0))),
        )

    def _heuristic_result(
        self,
        case: CaseDocument,
        layer1: Layer1Findings,
        reason: str,
        retrieval_context: Optional[List[Dict[str, str]]] = None,
    ) -> FinalAssessment:
        rule = self._derive_rule_based_signals(case, layer1)
        evidence_items = self._build_evidence_snippets(retrieval_context or [])
        # Sanitize reason — never expose raw API error messages
        clean_reason = self._sanitize_error(reason)
        return FinalAssessment(
            case_id=case.case_id,
            final_problem_list=rule["final_problem_list"],
            final_differentials=rule["differentials"],
            final_red_flags=rule["red_flags"],
            supported_findings=rule["supported_findings"],
            uncertain_findings=[
                f"Layer-2 model unavailable; used deterministic fallback for {rule['primary_diagnosis']}.",
            ],
            contradicted_findings=[],
            missing_data=[clean_reason] if clean_reason else [],
            evidence_pack=evidence_items,
            highlight_targets=rule["highlight_targets"],
            decision_log=f"Heuristic fallback: {reason}",
            primary_diagnosis=rule["primary_diagnosis"],
            confidence=rule["confidence"],
        )

    @staticmethod
    def _sanitize_error(text: str) -> str:
        """Replace raw API error messages with clean clinical-friendly text."""
        if not text:
            return text
        error_patterns = [
            "Client Error", "Server Error", "Too Many Requests", "Payload Too Large",
            "rate_limit", "413", "429", "500", "502", "503", "body=",
            "HTTPSConnectionPool", "Connection aborted", "RemoteDisconnected",
        ]
        for pat in error_patterns:
            if pat.lower() in text.lower():
                return "Validator model temporarily unavailable; deterministic analysis was used instead."
        return text

    # ------------------------------------------------------------------ #
    # Deterministic safety guards
    # ------------------------------------------------------------------ #
    def _merge_rule_based_guards(
        self,
        assessment: FinalAssessment,
        case: CaseDocument,
        layer1: Layer1Findings,
        retrieval_context: List[Dict[str, str]],
    ) -> FinalAssessment:
        rule = self._derive_rule_based_signals(case, layer1)

        if not assessment.primary_diagnosis:
            assessment.primary_diagnosis = rule["primary_diagnosis"]
        if not assessment.final_problem_list and assessment.primary_diagnosis:
            assessment.final_problem_list = [assessment.primary_diagnosis]

        # Confidence guard: avoid collapsing to 0.30 when model endpoints fail.
        assessment.confidence = max(assessment.confidence, rule["confidence"])

        assessment.final_problem_list = self._merge_string_lists(
            assessment.final_problem_list,
            rule["final_problem_list"],
        )
        assessment.final_red_flags = self._merge_string_lists(
            assessment.final_red_flags,
            self._merge_string_lists(layer1.red_flags, rule["red_flags"]),
        )
        assessment.supported_findings = self._merge_string_lists(
            assessment.supported_findings,
            rule["supported_findings"],
        )

        if not assessment.final_differentials:
            assessment.final_differentials = rule["differentials"]
        elif len(assessment.final_differentials) < 3:
            existing = {str(d.get("diagnosis", "")).lower() for d in assessment.final_differentials if isinstance(d, dict)}
            for diff in rule["differentials"]:
                name = str(diff.get("diagnosis", "")).lower()
                if name and name not in existing:
                    assessment.final_differentials.append(diff)
                    existing.add(name)
                if len(assessment.final_differentials) >= 3:
                    break

        assessment.highlight_targets = self._merge_highlights(
            assessment.highlight_targets,
            rule["highlight_targets"],
        )

        if not assessment.evidence_pack:
            assessment.evidence_pack = self._build_evidence_snippets(retrieval_context)

        if not assessment.missing_data and "Heuristic fallback" in assessment.decision_log:
            assessment.missing_data = ["Validator model unavailable during this run."]

        return assessment

    def _derive_rule_based_signals(self, case: CaseDocument, layer1: Layer1Findings) -> Dict[str, Any]:
        labs = self._extract_numeric_labs(case)

        hba1c = self._pick_lab_entry(labs, ["hba1c", "glycatedhemoglobin"])
        fasting_glucose = self._pick_lab_entry(
            labs,
            ["fastingbloodglucose", "fastingglucose", "fbg"],
        )
        post_prandial = self._pick_lab_entry(
            labs,
            ["postprandialglucose", "ppglucose", "postmealglucose"],
        )
        random_glucose = self._pick_lab_entry(labs, ["randombloodglucose", "randomglucose", "rbg"])
        ldl = self._pick_lab_entry(labs, ["ldlcholesterol", "ldl"])
        triglycerides = self._pick_lab_entry(labs, ["triglycerides", "triglyceride"])
        creatinine = self._pick_lab_entry(labs, ["serumcreatinine", "creatinine"])
        egfr = self._pick_lab_entry(labs, ["egfr"])
        microalbumin = self._pick_lab_entry(labs, ["microalbumin", "albuminuria", "albumincreatinineratio"])

        layer1_primary = (
            layer1.candidate_diagnoses[0].get("diagnosis")
            if layer1.candidate_diagnoses
            else "Undetermined"
        )
        layer1_conf = max(
            [float(d.get("confidence", 0.0) or 0.0) for d in layer1.candidate_diagnoses] or [0.3]
        )

        has_diabetes_pattern = any(
            [
                hba1c and hba1c["value"] >= 6.5,
                fasting_glucose and fasting_glucose["value"] >= 126,
                post_prandial and post_prandial["value"] >= 200,
                random_glucose and random_glucose["value"] >= 200,
            ]
        )
        severe_hyperglycemia = any(
            [
                hba1c and hba1c["value"] >= 10.0,
                fasting_glucose and fasting_glucose["value"] >= 200,
                post_prandial and post_prandial["value"] >= 300,
            ]
        )

        if has_diabetes_pattern:
            primary = "Uncontrolled type 2 diabetes mellitus"
        else:
            primary = str(layer1_primary or "Undetermined")

        confidence = layer1_conf
        if severe_hyperglycemia:
            confidence = max(confidence, 0.92)
        elif has_diabetes_pattern and hba1c and hba1c["value"] >= 8.0:
            confidence = max(confidence, 0.85)
        elif has_diabetes_pattern:
            confidence = max(confidence, 0.75)
        confidence = max(0.3, min(0.99, confidence))

        red_flags: List[str] = []
        supported_findings: List[str] = []
        highlight_targets: List[Provenance] = []

        def add_flag(entry: Optional[Dict[str, Any]], threshold: float, msg: str):
            if entry and entry["value"] >= threshold:
                red_flags.append(msg)
                supported_findings.append(f"{entry['label']} {entry['value']} crossed critical threshold {threshold}.")
                highlight_targets.append(self._to_provenance(case, entry))

        add_flag(hba1c, 10.0, "HbA1c >= 10%: critical chronic hyperglycemia risk.")
        add_flag(post_prandial, 300.0, "Post-prandial glucose >= 300 mg/dL: severe uncontrolled hyperglycemia.")
        add_flag(fasting_glucose, 200.0, "Fasting glucose >= 200 mg/dL: severe fasting hyperglycemia.")
        add_flag(triglycerides, 300.0, "Triglycerides >= 300 mg/dL: pancreatitis and cardiovascular risk.")
        add_flag(ldl, 160.0, "LDL >= 160 mg/dL: high cardiovascular risk.")

        if egfr and egfr["value"] < 60:
            red_flags.append("eGFR < 60 mL/min: renal impairment pattern.")
            supported_findings.append(f"{egfr['label']} {egfr['value']} indicates reduced renal function.")
            highlight_targets.append(self._to_provenance(case, egfr))
        if creatinine and creatinine["value"] > 1.3:
            supported_findings.append(f"{creatinine['label']} {creatinine['value']} indicates kidney stress.")
            highlight_targets.append(self._to_provenance(case, creatinine))
        if microalbumin and microalbumin["value"] >= 300:
            red_flags.append("Microalbumin >= 300 suggests significant albuminuria.")
            supported_findings.append(f"{microalbumin['label']} {microalbumin['value']} suggests diabetic nephropathy risk.")
            highlight_targets.append(self._to_provenance(case, microalbumin))

        final_problem_list: List[str] = [primary] if primary else []
        if ldl and ldl["value"] >= 160:
            final_problem_list.append("Severe dyslipidemia")
        if triglycerides and triglycerides["value"] >= 300:
            final_problem_list.append("Severe hypertriglyceridemia")
        if (egfr and egfr["value"] < 60) or (microalbumin and microalbumin["value"] >= 300):
            final_problem_list.append("Probable diabetic kidney disease / renal impairment")

        differentials = self._rule_based_differentials(primary)
        return {
            "primary_diagnosis": primary,
            "confidence": confidence,
            "red_flags": self._merge_string_lists(layer1.red_flags, red_flags),
            "supported_findings": supported_findings,
            "highlight_targets": self._merge_highlights([], highlight_targets),
            "final_problem_list": self._merge_string_lists(final_problem_list, []),
            "differentials": differentials,
        }

    def _rule_based_differentials(self, primary: str) -> List[Dict[str, Any]]:
        primary_low = str(primary or "").lower()
        if "diabetes" in primary_low:
            return [
                {
                    "diagnosis": "Type 1 diabetes mellitus (adult-onset or LADA)",
                    "confidence": 0.28,
                    "reason": "Severe hyperglycemia can overlap; autoantibodies and C-peptide are needed for exclusion.",
                },
                {
                    "diagnosis": "Secondary diabetes due to endocrine disorder",
                    "confidence": 0.22,
                    "reason": "Endocrine contributors should be excluded when hyperglycemia is severe or rapidly progressive.",
                },
                {
                    "diagnosis": "Stress hyperglycemia with metabolic syndrome",
                    "confidence": 0.18,
                    "reason": "Acute illness can worsen glucose; persistent HbA1c elevation still favors chronic diabetes.",
                },
            ]
        return [
            {
                "diagnosis": "Metabolic syndrome with insulin resistance",
                "confidence": 0.25,
                "reason": "Pattern overlaps with obesity, dyslipidemia, and abnormal glucose markers.",
            },
            {
                "diagnosis": "Endocrine/metabolic disorder requiring targeted workup",
                "confidence": 0.2,
                "reason": "Current data is suggestive but not disease-specific.",
            },
            {
                "diagnosis": "Inflammatory or organ-system secondary process",
                "confidence": 0.15,
                "reason": "Abnormal labs may reflect a secondary process and need clinical correlation.",
            },
        ]

    def _extract_numeric_labs(self, case: CaseDocument) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        for fact in case.facts.labs:
            value = self._extract_first_number(str(fact.value))
            if value is None:
                continue
            label = str(fact.label)
            rows.append(
                {
                    "label": label,
                    "normalized": self._normalize_label(label),
                    "value": value,
                    "fact": fact,
                }
            )
        return rows

    def _pick_lab_entry(self, labs: List[Dict[str, Any]], aliases: List[str]) -> Optional[Dict[str, Any]]:
        matches = [
            lab
            for lab in labs
            if any(alias in lab["normalized"] for alias in aliases)
        ]
        if not matches:
            return None
        return max(matches, key=lambda row: row["value"])

    def _to_provenance(self, case: CaseDocument, lab_entry: Dict[str, Any]) -> Provenance:
        fact = lab_entry["fact"]
        if fact.provenance:
            return fact.provenance
        return Provenance(
            pdf_id=case.pdf_id,
            page=1,
            bbox=None,
            text_span=f"{fact.label}: {fact.value}",
        )

    def _extract_first_number(self, value: str) -> Optional[float]:
        match = re.search(r"-?\d+(?:\.\d+)?", value)
        if not match:
            return None
        try:
            return float(match.group(0))
        except Exception:
            return None

    def _normalize_label(self, label: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", label.lower())

    def _coerce_json_content(self, content: Any) -> Dict[str, Any]:
        if isinstance(content, dict):
            return content
        text = str(content or "").strip()
        if not text:
            return {}
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?", "", text, flags=re.IGNORECASE).strip()
            text = re.sub(r"```$", "", text).strip()
        try:
            return json.loads(text)
        except Exception:
            match = re.search(r"\{[\s\S]*\}", text)
            if not match:
                return {}
            try:
                return json.loads(match.group(0))
            except Exception:
                return {}

    def _merge_string_lists(self, left: List[str], right: List[str]) -> List[str]:
        merged: List[str] = []
        for item in (left or []) + (right or []):
            text = str(item).strip()
            if text and text not in merged:
                merged.append(text)
        return merged

    def _merge_highlights(self, left: List[Provenance], right: List[Provenance]) -> List[Provenance]:
        seen = set()
        merged: List[Provenance] = []
        for item in (left or []) + (right or []):
            key = (item.pdf_id, item.page, item.text_span or "")
            if key in seen:
                continue
            seen.add(key)
            merged.append(item)
        return merged[:30]

    def _build_evidence_snippets(self, retrieval_context: List[Dict[str, str]]) -> List[EvidenceSnippet]:
        return [
            EvidenceSnippet(
                source=e.get("source", "unknown"),
                title=e.get("title", ""),
                url=e.get("url", ""),
                snippet=e.get("snippet", ""),
            )
            for e in retrieval_context[:12]
        ]

    def _persist_assessment(self, assessment: FinalAssessment, case_id: str) -> None:
        case_dir = os.path.join(settings.CASE_DIR, case_id)
        os.makedirs(case_dir, exist_ok=True)
        out_path = os.path.join(case_dir, "final_assessment.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(assessment.model_dump(mode="json"), f, indent=2)
        assessment.final_assessment_path = out_path
        print(f"[Layer 2] final_assessment.json saved -> {out_path}")


layer2_validator = Layer2Validator()
