from datetime import datetime
from html import escape
from typing import Any, Dict, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Flowable,
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


class CircledValue(Flowable):
    """Draws a red circle around a short text token."""

    def __init__(self, text: str):
        super().__init__()
        self.text = text[:40]
        self.width = max(90, len(self.text) * 6 + 20)
        self.height = 24

    def draw(self):
        self.canv.setStrokeColor(colors.red)
        self.canv.setLineWidth(1.8)
        self.canv.ellipse(2, 2, self.width - 2, self.height - 2)
        self.canv.setFont("Helvetica-Bold", 9)
        self.canv.setFillColor(colors.black)
        self.canv.drawCentredString(self.width / 2, 8, self.text)


class PDFAnnotator:
    def __init__(self):
        styles = getSampleStyleSheet()
        self.title = ParagraphStyle(
            "title",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=20,
            textColor=colors.HexColor("#1f2937"),
            spaceAfter=4,
        )
        self.sub = ParagraphStyle(
            "sub",
            parent=styles["Normal"],
            fontSize=9,
            textColor=colors.HexColor("#4b5563"),
            spaceAfter=8,
        )
        self.h2 = ParagraphStyle(
            "h2",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            textColor=colors.HexColor("#0f172a"),
            spaceBefore=8,
            spaceAfter=5,
        )
        self.body = ParagraphStyle(
            "body",
            parent=styles["Normal"],
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor("#111827"),
            spaceAfter=4,
        )
        self.small = ParagraphStyle(
            "small",
            parent=styles["Normal"],
            fontSize=8,
            textColor=colors.HexColor("#6b7280"),
        )
        self.red_alert = ParagraphStyle(
            "red_alert",
            parent=styles["Normal"],
            fontSize=10,
            fontName="Helvetica-Bold",
            textColor=colors.white,
            backColor=colors.HexColor("#b91c1c"),
            borderPadding=6,
            leading=13,
            spaceAfter=4,
        )
        self.red_note = ParagraphStyle(
            "red_note",
            parent=styles["Normal"],
            fontSize=9,
            textColor=colors.HexColor("#7f1d1d"),
            backColor=colors.HexColor("#fee2e2"),
            borderPadding=5,
            borderWidth=1,
            borderColor=colors.HexColor("#ef4444"),
            leading=12,
            spaceAfter=3,
        )

    def create_annotated_report(self, output_path: str, data: Dict[str, Any]) -> str:
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            leftMargin=14 * mm,
            rightMargin=14 * mm,
            topMargin=14 * mm,
            bottomMargin=14 * mm,
        )
        story: List[Any] = []
        self._header(story, data)
        self._patient_summary(story, data)
        self._urgent_red_flags(story, data)
        self._primary_diagnosis(story, data)
        self._differentials(story, data)
        self._evidence_links(story, data)
        self._layer1_findings(story, data)
        self._layer2_validated(story, data)
        self._data_flow_transparency(story, data)
        self._xai(story, data)
        self._next_steps(story, data)
        self._critical_highlights(story, data)
        self._footer(story)
        doc.build(story)
        return output_path

    # ------------------------------------------------------------------ #
    # Sections required by doctor-facing contract
    # ------------------------------------------------------------------ #
    def _header(self, story: List[Any], data: Dict[str, Any]):
        case_id = data.get("case_id", "unknown")
        story.append(Paragraph("MediCascade Clinical Report", self.title))
        story.append(
            Paragraph(
                f"Annotated doctor-facing output | Case ID: {case_id} | Generated: {datetime.utcnow().isoformat()}Z",
                self.sub,
            )
        )
        story.append(HRFlowable(width="100%", thickness=0.9, color=colors.HexColor("#d1d5db")))
        story.append(Spacer(1, 6))

    def _patient_summary(self, story: List[Any], data: Dict[str, Any]):
        story.append(Paragraph("Patient Summary", self.h2))
        summary = data.get("patient_summary", {})
        demographics = summary.get("demographics", {})
        vitals = summary.get("vitals", {})
        key_facts = summary.get("key_facts", [])

        demo_rows = [["Field", "Value"]]
        for k, v in demographics.items():
            demo_rows.append([str(k), str(v)])
        if len(demo_rows) == 1:
            demo_rows.append(["Demographics", "Not available"])
        table = Table(demo_rows, colWidths=[52 * mm, 120 * mm])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8.8),
                    ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cbd5e1")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ]
            )
        )
        story.append(table)
        story.append(Spacer(1, 5))

        vitals_text = ", ".join([f"{k}: {v}" for k, v in vitals.items()]) if vitals else "Not available"
        story.append(Paragraph(f"<b>Vitals:</b> {safe(vitals_text)}", self.body))
        if key_facts:
            facts_text = "; ".join([str(x) for x in key_facts[:8]])
            story.append(Paragraph("<b>Key Facts:</b> " + safe(facts_text), self.body))

    def _urgent_red_flags(self, story: List[Any], data: Dict[str, Any]):
        story.append(Paragraph("Urgent Red Flags", self.h2))
        red_flags = data.get("urgent_red_flags", [])
        if not red_flags:
            story.append(Paragraph("No urgent red flags identified by the validator.", self.body))
            return
        story.append(Paragraph("Immediate clinical review recommended.", self.red_alert))
        for flag in red_flags[:10]:
            story.append(Paragraph(safe(str(flag)), self.red_note))

    def _primary_diagnosis(self, story: List[Any], data: Dict[str, Any]):
        story.append(Paragraph("Primary Diagnosis", self.h2))
        diagnosis = data.get("diagnosis", "Undetermined")
        confidence = float(data.get("confidence", 0.0) or 0.0)
        story.append(Paragraph(f"<b>{safe(diagnosis)}</b>", self.body))
        story.append(Paragraph(f"Confidence: <b>{confidence:.0%}</b>", self.body))

    def _differentials(self, story: List[Any], data: Dict[str, Any]):
        story.append(Paragraph("Differential Diagnoses", self.h2))
        differentials = data.get("secondary_diagnoses", [])
        if not differentials:
            story.append(Paragraph("No additional differential diagnoses listed.", self.body))
            return
        rows = [["Diagnosis", "Confidence", "Reason"]]
        for d in differentials[:8]:
            if isinstance(d, dict):
                rows.append(
                    [
                        str(d.get("diagnosis", "")),
                        f"{float(d.get('confidence', 0.0) or 0.0):.0%}",
                        str(d.get("reason", ""))[:120],
                    ]
                )
            else:
                rows.append([str(d), "-", ""])
        t = Table(rows, colWidths=[64 * mm, 22 * mm, 86 * mm])
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8.3),
                    ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cbd5e1")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ]
            )
        )
        story.append(t)

    def _evidence_links(self, story: List[Any], data: Dict[str, Any]):
        story.append(Paragraph("Evidence Links (PubMed / NICE / WHO)", self.h2))
        links = data.get("evidence_links", [])
        if not links:
            story.append(Paragraph("No evidence links attached.", self.body))
            return
        rows = [["Source", "Title", "URL"]]
        for e in links[:16]:
            rows.append(
                [
                    str(e.get("source", "")),
                    str(e.get("title", ""))[:60],
                    str(e.get("url", ""))[:95],
                ]
            )
        t = Table(rows, colWidths=[22 * mm, 62 * mm, 88 * mm])
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#065f46")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8.0),
                    ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cbd5e1")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ]
            )
        )
        story.append(t)
        story.append(Spacer(1, 4))

    def _layer1_findings(self, story: List[Any], data: Dict[str, Any]):
        story.append(Paragraph("Layer 1 Specialist Findings", self.h2))
        l1 = data.get("layer1_findings", {})
        cand = l1.get("candidate_diagnoses", [])
        if cand:
            text = "; ".join([f"{c.get('agent', '')}: {c.get('diagnosis', '')} ({float(c.get('confidence', 0.0) or 0.0):.0%})" for c in cand[:8]])
            story.append(Paragraph(f"<b>Candidate diagnoses:</b> {text}", self.body))
        else:
            story.append(Paragraph("<b>Candidate diagnoses:</b> none", self.body))

        red_flags = l1.get("red_flags", [])
        story.append(Paragraph("<b>Red flags:</b> " + safe(", ".join([str(x) for x in red_flags[:10]]) if red_flags else "none"), self.body))

        abnormal_labs = l1.get("abnormal_labs", [])
        story.append(Paragraph("<b>Abnormal labs:</b> " + safe(json_like(abnormal_labs[:6]) if abnormal_labs else "none"), self.body))

        timeline = l1.get("symptom_timeline", [])
        story.append(Paragraph("<b>Symptom timeline:</b> " + safe(json_like(timeline[:6]) if timeline else "none"), self.body))

        risks = l1.get("risk_factors", [])
        story.append(Paragraph("<b>Risk factors:</b> " + safe(", ".join([str(x) for x in risks[:10]]) if risks else "none"), self.body))

    def _layer2_validated(self, story: List[Any], data: Dict[str, Any]):
        story.append(Paragraph("Layer 2 Validated Conclusions", self.h2))
        l2 = data.get("layer2_validated", {})
        for label, key in [
            ("Final problem list", "final_problem_list"),
            ("Supported findings", "supported_findings"),
            ("Uncertain findings", "uncertain_findings"),
            ("Contradicted findings", "contradicted_findings"),
            ("Missing data", "missing_data"),
        ]:
            values = l2.get(key, [])
            text = ", ".join([str(v) for v in values[:12]]) if values else "none"
            story.append(Paragraph(f"<b>{label}:</b> {safe(text)}", self.body))

    def _xai(self, story: List[Any], data: Dict[str, Any]):
        story.append(Paragraph("XAI Section (Why this diagnosis)", self.h2))
        reasoning = str(data.get("reasoning", "")).strip()
        if not reasoning:
            story.append(Paragraph("No XAI narrative available.", self.body))
            return
        # Preserve paragraph breaks for long Groq-generated narrative.
        for chunk in reasoning.split("\n"):
            chunk = chunk.strip()
            if not chunk:
                story.append(Spacer(1, 2))
                continue
            story.append(Paragraph(safe(chunk), self.body))

    def _next_steps(self, story: List[Any], data: Dict[str, Any]):
        story.append(Paragraph("Recommended Next Steps / Tests", self.h2))
        steps = data.get("recommendations", [])
        if not steps:
            steps = ["No explicit recommendations were generated."]
        for step in steps[:10]:
            story.append(Paragraph(f"- {safe(str(step))}", self.body))

    def _critical_highlights(self, story: List[Any], data: Dict[str, Any]):
        story.append(Paragraph("Critical Data Highlights", self.h2))
        points = data.get("critical_points", [])
        if not points:
            targets = data.get("highlight_targets", [])
            points = [{"phrase": t.get("text_span", "critical span"), "reason": "highlight target"} for t in targets]
        if not points:
            story.append(Paragraph("No critical highlights available.", self.body))
            return

        for cp in points[:10]:
            phrase = str(cp.get("phrase", "critical value"))[:45]
            reason = safe(str(cp.get("reason", "Marked as clinically relevant"))[:160])
            row = Table([[CircledValue(phrase), Paragraph(reason, self.body)]], colWidths=[48 * mm, 124 * mm])
            row.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 2),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                    ]
                )
            )
            story.append(row)
            story.append(Spacer(1, 2))

    def _data_flow_transparency(self, story: List[Any], data: Dict[str, Any]):
        story.append(Paragraph("Data Flow Transparency", self.h2))
        trace = data.get("data_flow_trace", [])
        if not trace:
            story.append(Paragraph("No trace metadata was provided.", self.body))
            return
        rows = [["Layer", "Input", "Output", "Status"]]
        for item in trace[:8]:
            rows.append(
                [
                    safe(item.get("layer", ""))[:35],
                    safe(item.get("input", ""))[:45],
                    safe(item.get("output", ""))[:60],
                    safe(item.get("status", ""))[:15],
                ]
            )
        t = Table(rows, colWidths=[40 * mm, 45 * mm, 72 * mm, 20 * mm])
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#334155")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cbd5e1")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ]
            )
        )
        story.append(t)

    def _footer(self, story: List[Any]):
        story.append(Spacer(1, 6))
        story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#d1d5db")))
        story.append(
            Paragraph(
                "This report supports, but does not replace, clinician judgement.",
                self.small,
            )
        )


def json_like(values: List[Any]) -> str:
    try:
        import json

        return json.dumps(values, ensure_ascii=True)
    except Exception:
        return str(values)


def safe(text: Any) -> str:
    return escape(str(text), quote=False)


pdf_annotator = PDFAnnotator()
