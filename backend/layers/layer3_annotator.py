import logging
import os

from config import settings
from schemas import (
    AnnotatedReport,
    CaseDocument,
    Evidence,
    FinalAssessment,
    FinalDiagnosis,
    Layer1Findings,
)
from utils.icd_mapper import get_icd10_for_differential, map_to_icd10
from utils.pdf_annotator import pdf_annotator

logger = logging.getLogger(__name__)

try:
    from groq import Groq
except ImportError:
    Groq = None


class Layer3Annotator:
    """
    Layer 3: doctor-ready output with explicit sections and annotations.
    """

    def __init__(self):
        self.groq_client = None
        if settings.GROQ_API_KEY and Groq:
            try:
                self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
            except Exception as e:
                logger.info(f"[Layer 3] Groq client init failed, narrative fallback enabled: {e}")

    def process(self, case: CaseDocument, layer1: Layer1Findings, final: FinalAssessment) -> AnnotatedReport:
        explanation = self._narrate(final, layer1)
        evidence_items = self._build_evidence(final)

        # ICD-10 coding for primary diagnosis and differentials
        icd_result = map_to_icd10(final.primary_diagnosis or "")
        icd_code = icd_result["icd10_code"]
        icd_desc = icd_result["icd10_description"]
        enriched_differentials = get_icd10_for_differential(final.final_differentials)

        # Collect FDA drug safety warnings from medication specialist
        drug_safety = self._extract_drug_safety(layer1)

        final_dx = FinalDiagnosis(
            primary_diagnosis=final.primary_diagnosis or "Undetermined",
            confidence=final.confidence,
            secondary_diagnoses=enriched_differentials,
            reasoning=explanation,
            cross_validation_score=0.0,
            anomaly_detected=False,
            anomaly_description="",
            conflicts_resolved=[],
            critical_points=self._critical_points_from_highlights(final),
        )

        # Attach ICD code and drug safety to the report metadata
        self._icd_code = icd_code
        self._icd_desc = icd_desc
        self._icd_match_type = icd_result.get("match_type", "")
        self._icd_warning = icd_result.get("warning", "")
        self._drug_safety = drug_safety

        pdf_path = self._build_pdf(case, layer1, final, final_dx, explanation, evidence_items)

        return AnnotatedReport(
            diagnosis=final_dx,
            evidence_items=evidence_items,
            explanation_text=explanation,
            annotated_pdf_path=pdf_path,
            annotated_images_paths=[],
            visualization_data={
                "layer1_agents": [v.agent for v in layer1.views],
                "red_flags": final.final_red_flags,
                "icd10_code": icd_code,
                "icd10_description": icd_desc,
                "icd10_match_type": icd_result.get("match_type", ""),
                "icd10_warning": icd_result.get("warning", ""),
                "drug_safety": drug_safety,
            },
        )

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _build_evidence(self, final: FinalAssessment) -> list[Evidence]:
        items: list[Evidence] = []
        for ev in final.evidence_pack:
            text = f"{ev.source}: {ev.snippet}".strip()
            items.append(
                Evidence(
                    text=text[:400],
                    location=ev.url or ev.title,
                    relevance_score=0.9,
                    annotation_type="highlight",
                )
            )
        for prov in final.highlight_targets:
            items.append(
                Evidence(
                    text=prov.text_span or "Critical span",
                    location=f"Page {prov.page}",
                    relevance_score=0.85,
                    annotation_type="circle",
                )
            )
        return items[:30]

    def _critical_points_from_highlights(self, final: FinalAssessment) -> list[dict[str, str]]:
        points: list[dict[str, str]] = []
        for p in final.highlight_targets[:12]:
            points.append(
                {
                    "phrase": p.text_span or "Critical phrase",
                    "reason": "Marked as a key data point for clinical review.",
                    "severity": "CRITICAL",
                }
            )
        return points

    def _narrate(self, final: FinalAssessment, layer1: Layer1Findings) -> str:
        fallback = self._build_rule_based_narrative(final, layer1)
        if not self.groq_client:
            return fallback
        try:
            evidence_lines = []
            for ev in final.evidence_pack[:12]:
                evidence_lines.append(
                    f"- [{ev.source}] {ev.title} | {ev.url} | snippet: {ev.snippet[:220]}"
                )

            layer1_lines = []
            for cand in layer1.candidate_diagnoses[:8]:
                layer1_lines.append(
                    f"- {cand.get('agent','agent')}: {cand.get('diagnosis','')} "
                    f"({float(cand.get('confidence', 0.0) or 0.0):.0%})"
                )

            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a senior clinical decision support explainer. "
                        "Write a detailed doctor-facing XAI narrative using ONLY provided validated findings. "
                        "No new claims, no invented evidence. If evidence is insufficient, state uncertainty explicitly."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Build the explanation with these sections:\n"
                        "1) Clinical summary\n"
                        "2) Why primary diagnosis is most likely\n"
                        "3) Differential reasoning\n"
                        "4) Red-flag interpretation\n"
                        "5) Evidence grounding (with source names)\n"
                        "6) Uncertainty and missing data\n"
                        "7) Recommended next tests/actions\n\n"
                        f"Primary diagnosis: {final.primary_diagnosis}\n"
                        f"Confidence: {final.confidence:.2f}\n"
                        f"Final problem list: {final.final_problem_list}\n"
                        f"Final differentials: {final.final_differentials}\n"
                        f"Final red flags: {final.final_red_flags}\n"
                        f"Supported findings: {final.supported_findings}\n"
                        f"Uncertain findings: {final.uncertain_findings}\n"
                        f"Contradicted findings: {final.contradicted_findings}\n"
                        f"Missing data: {final.missing_data}\n"
                        f"Layer1 candidate diagnoses:\n{chr(10).join(layer1_lines) if layer1_lines else '- none'}\n"
                        f"Evidence pack:\n{chr(10).join(evidence_lines) if evidence_lines else '- none'}\n"
                        f"Highlight targets count: {len(final.highlight_targets)}\n"
                        "Keep tone clinical, precise, and practical."
                    ),
                },
            ]
            resp = self.groq_client.chat.completions.create(
                model=settings.GROQ_MODEL,
                temperature=0.15,
                max_tokens=1100,
                messages=messages,
            )
            text = resp.choices[0].message.content or ""
            return text.strip() if text.strip() else fallback
        except Exception as e:
            logger.info(f"[Layer 3] Narrative generation failed: {e}")
            return fallback

    def _build_rule_based_narrative(self, final: FinalAssessment, layer1: Layer1Findings) -> str:
        candidate_lines = [
            f"- {c.get('diagnosis', '')} ({float(c.get('confidence', 0.0) or 0.0):.0%})"
            for c in layer1.candidate_diagnoses[:5]
        ]
        diff_lines = [
            f"- {d.get('diagnosis', '')}: {d.get('reason', '')}"
            for d in final.final_differentials[:5]
            if isinstance(d, dict)
        ]
        red_flag_lines = [f"- {flag}" for flag in final.final_red_flags[:8]]
        evidence_lines = [
            f"- {ev.source}: {ev.title} ({ev.url})"
            for ev in final.evidence_pack[:8]
        ]
        missing_lines = [f"- {item}" for item in final.missing_data[:6]]

        sections = [
            "1) Clinical summary",
            f"Primary diagnosis: {final.primary_diagnosis or 'undetermined'}",
            f"Confidence: {final.confidence:.0%}",
            "Layer 1 candidates:",
            "\n".join(candidate_lines) if candidate_lines else "- none",
            "",
            "2) Why primary diagnosis is likely",
            "\n".join([f"- {item}" for item in final.supported_findings[:8]]) if final.supported_findings else "- Supported findings not explicitly listed.",
            "",
            "3) Differential reasoning",
            "\n".join(diff_lines) if diff_lines else "- No differentials were provided by validator output.",
            "",
            "4) Red-flag interpretation",
            "\n".join(red_flag_lines) if red_flag_lines else "- No urgent red flags identified.",
            "",
            "5) Evidence grounding",
            "\n".join(evidence_lines) if evidence_lines else "- Evidence links unavailable.",
            "",
            "6) Uncertainty and missing data",
            "\n".join([f"- {item}" for item in final.uncertain_findings[:6]]) if final.uncertain_findings else "- No explicit uncertainty notes.",
            "\n".join(missing_lines) if missing_lines else "- No missing-data notes.",
            "",
            "7) Recommended next tests/actions",
            "- Repeat key abnormal labs and correlate with bedside findings.",
            "- Review highlighted source spans in the PDF before treatment decisions.",
            "- Prioritize urgent red flags and specialist follow-up where indicated.",
        ]
        return "\n".join(sections).strip()

    def _recommended_next_steps(self, final: FinalAssessment) -> list[str]:
        steps = [
            "Review urgent red flags immediately.",
            "Correlate highlighted values with bedside clinical assessment.",
            "Confirm key abnormalities with repeat or targeted tests.",
        ]
        for missing in final.missing_data[:4]:
            steps.append(f"Obtain missing data: {missing}")
        # Add drug safety steps if warnings exist
        if getattr(self, "_drug_safety", None):
            ds = self._drug_safety
            if ds.get("warnings"):
                steps.append("REVIEW: FDA drug warnings identified — verify medication safety before prescribing.")
            if ds.get("interactions"):
                steps.append("REVIEW: Potential drug-drug interactions flagged — consult pharmacist.")
        return steps[:10]

    def _extract_drug_safety(self, layer1: Layer1Findings) -> dict:
        """Pull FDA drug safety data from the medication specialist view."""
        for view in layer1.views:
            if view.agent == "medication":
                findings = view.findings or {}
                return {
                    "warnings":        findings.get("fda_drug_warnings", []),
                    "interactions":    findings.get("fda_interactions", []),
                    "contraindications": findings.get("fda_contraindications", []),
                }
        return {}

    def _build_pdf(
        self,
        case: CaseDocument,
        layer1: Layer1Findings,
        final: FinalAssessment,
        dx: FinalDiagnosis,
        explanation: str,
        evidence: list[Evidence],
    ) -> str:
        case_dir = os.path.join(settings.CASE_DIR, case.case_id)
        os.makedirs(case_dir, exist_ok=True)
        output_path = os.path.join(case_dir, f"MediCascade_Report_{case.case_id}.pdf")

        patient_summary = {
            "demographics": {f.label: str(f.value) for f in case.facts.demographics[:12]},
            "vitals": {f.label: f"{f.value} {f.unit or ''}".strip() for f in case.facts.vitals[:12]},
            "key_facts": [f"{f.label}: {f.value}" for f in case.facts.labs[:8]],
        }

        layer1_section = {
            "candidate_diagnoses": layer1.candidate_diagnoses,
            "red_flags": layer1.red_flags,
            "abnormal_labs": layer1.abnormal_labs,
            "symptom_timeline": layer1.symptom_timeline,
            "risk_factors": layer1.risk_factors,
        }

        layer2_section = {
            "final_problem_list": final.final_problem_list,
            "supported_findings": final.supported_findings,
            "uncertain_findings": final.uncertain_findings,
            "contradicted_findings": final.contradicted_findings,
            "missing_data": final.missing_data,
        }

        drug_safety = getattr(self, "_drug_safety", {})

        pdf_data = {
            "case_id": case.case_id,
            "patient_summary": patient_summary,
            "urgent_red_flags": final.final_red_flags,
            "diagnosis": dx.primary_diagnosis,
            "confidence": dx.confidence,
            "icd10_code": getattr(self, "_icd_code", "R69"),
            "icd10_description": getattr(self, "_icd_desc", "Illness, unspecified"),
            "icd10_match_type": getattr(self, "_icd_match_type", ""),
            "icd10_warning": getattr(self, "_icd_warning", ""),
            "secondary_diagnoses": dx.secondary_diagnoses,
            "drug_safety": drug_safety,
            "evidence_links": [
                {
                    "source": e.source,
                    "title": e.title,
                    "url": e.url,
                    "snippet": e.snippet,
                }
                for e in final.evidence_pack
            ],
            "layer1_findings": layer1_section,
            "layer2_validated": layer2_section,
            "reasoning": explanation,
            "recommendations": self._recommended_next_steps(final),
            "critical_points": dx.critical_points,
            "highlight_targets": [p.model_dump(mode="json") for p in final.highlight_targets],
            "evidence": [{"text": ev.text, "location": ev.location} for ev in evidence],
            "data_flow_trace": [
                {
                    "layer": "Layer 0 - Document Intake",
                    "input": "Uploaded patient PDF (and optional scan)",
                    "output": "case.json with structured facts + provenance",
                    "status": "completed",
                },
                {
                    "layer": "Layer 1 - Multi-model Specialists",
                    "input": "case.json",
                    "output": "layer1_findings.json with candidate diagnoses/red flags/risk factors",
                    "status": "completed",
                },
                {
                    "layer": "Layer 2 - Evidence Validator",
                    "input": "layer1_findings.json + PubMed/NICE/WHO evidence",
                    "output": "final_assessment.json with supported/uncertain/contradicted findings",
                    "status": "completed",
                },
                {
                    "layer": "Layer 3 - Report Builder",
                    "input": "final_assessment.json + ICD-10 coding + drug safety",
                    "output": f"MediCascade_Report_{case.case_id}.pdf",
                    "status": "completed",
                },
            ],
        }

        try:
            pdf_annotator.create_annotated_report(output_path, pdf_data)
        except Exception as e:
            logger.info(f"[Layer 3] PDF generation error: {e}")
            return ""
        return output_path


layer3_annotator = Layer3Annotator()
