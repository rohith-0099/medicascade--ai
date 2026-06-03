import re
from collections.abc import Iterable, Sequence
from datetime import datetime
from html import escape
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


class PDFAnnotator:
    def __init__(self):
        styles = getSampleStyleSheet()
        self.palette = {
            "ink": colors.HexColor("#0f172a"),
            "muted": colors.HexColor("#475569"),
            "line": colors.HexColor("#cbd5e1"),
            "panel": colors.HexColor("#f8fafc"),
            "panel_alt": colors.HexColor("#f1f5f9"),
            "blue": colors.HexColor("#1d4ed8"),
            "blue_dark": colors.HexColor("#1e3a8a"),
            "teal_dark": colors.HexColor("#065f46"),
            "slate_dark": colors.HexColor("#334155"),
            "red": colors.HexColor("#b91c1c"),
            "red_soft": colors.HexColor("#fef2f2"),
            "red_text": colors.HexColor("#7f1d1d"),
            "amber": colors.HexColor("#fef3c7"),
            "amber_border": colors.HexColor("#f59e0b"),
            "amber_text": colors.HexColor("#92400e"),
            "green_soft": colors.HexColor("#ecfdf5"),
        }

        self.title = ParagraphStyle(
            "title",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=21,
            alignment=TA_CENTER,
            textColor=self.palette["ink"],
            spaceAfter=4,
        )
        self.sub = ParagraphStyle(
            "sub",
            parent=styles["Normal"],
            fontSize=8.7,
            alignment=TA_CENTER,
            textColor=self.palette["muted"],
            leading=11,
            spaceAfter=8,
        )
        self.h2 = ParagraphStyle(
            "h2",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12.5,
            textColor=self.palette["ink"],
            spaceBefore=9,
            spaceAfter=5,
        )
        self.h3 = ParagraphStyle(
            "h3",
            parent=styles["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=10.2,
            textColor=self.palette["blue_dark"],
            spaceBefore=5,
            spaceAfter=3,
        )
        self.body = ParagraphStyle(
            "body",
            parent=styles["Normal"],
            fontSize=9.3,
            leading=13.2,
            textColor=self.palette["ink"],
            spaceAfter=4,
            wordWrap="CJK",
        )
        self.body_tight = ParagraphStyle(
            "body_tight",
            parent=self.body,
            fontSize=8.7,
            leading=11.4,
            spaceAfter=2,
        )
        self.bullet = ParagraphStyle(
            "bullet",
            parent=self.body,
            leftIndent=12,
            firstLineIndent=-8,
            spaceAfter=2,
        )
        self.small = ParagraphStyle(
            "small",
            parent=styles["Normal"],
            fontSize=8,
            leading=10,
            textColor=self.palette["muted"],
        )
        self.table_head = ParagraphStyle(
            "table_head",
            parent=self.body_tight,
            fontName="Helvetica-Bold",
            fontSize=8.1,
            textColor=colors.white,
            leading=10,
        )
        self.table_cell = ParagraphStyle(
            "table_cell",
            parent=self.body_tight,
            fontSize=8.5,
            leading=10.6,
            textColor=self.palette["ink"],
            wordWrap="CJK",
        )
        self.table_cell_sm = ParagraphStyle(
            "table_cell_sm",
            parent=self.table_cell,
            fontSize=7.9,
            leading=9.7,
        )
        self.link_cell = ParagraphStyle(
            "link_cell",
            parent=self.table_cell_sm,
            textColor=self.palette["blue"],
        )
        self.badge = ParagraphStyle(
            "badge",
            parent=self.body_tight,
            fontName="Helvetica-Bold",
            alignment=TA_CENTER,
            textColor=colors.white,
        )
        self.alert_banner = ParagraphStyle(
            "alert_banner",
            parent=self.body_tight,
            fontName="Helvetica-Bold",
            textColor=colors.white,
            backColor=self.palette["red"],
            borderPadding=6,
            leading=10.5,
            spaceAfter=4,
        )
        self.highlight_text = ParagraphStyle(
            "highlight_text",
            parent=self.table_cell,
            textColor=self.palette["red_text"],
            leading=11,
        )

    def create_annotated_report(self, output_path: str, data: dict[str, Any]) -> str:
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            leftMargin=14 * mm,
            rightMargin=14 * mm,
            topMargin=15 * mm,
            bottomMargin=18 * mm,
        )
        story: list[Any] = []
        self._header(story, data)
        self._patient_summary(story, data)
        self._urgent_red_flags(story, data)
        self._primary_diagnosis(story, data)
        self._icd10_section(story, data)
        self._differentials(story, data)
        self._drug_safety_section(story, data)
        self._evidence_links(story, data)
        self._layer1_findings(story, data)
        self._layer2_validated(story, data)
        self._data_flow_transparency(story, data)
        self._xai(story, data)
        self._next_steps(story, data)
        self._critical_highlights(story, data)
        self._footer(story)
        doc.build(story, onFirstPage=self._decorate_page, onLaterPages=self._decorate_page)
        return output_path

    # ------------------------------------------------------------------ #
    # Shared layout helpers
    # ------------------------------------------------------------------ #
    def _decorate_page(self, canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(self.palette["line"])
        canvas.setLineWidth(0.6)
        canvas.line(doc.leftMargin, 10 * mm, A4[0] - doc.rightMargin, 10 * mm)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(self.palette["muted"])
        canvas.drawString(doc.leftMargin, 6.5 * mm, "MediCascade AI")
        canvas.drawRightString(A4[0] - doc.rightMargin, 6.5 * mm, f"Page {doc.page}")
        canvas.restoreState()

    def _para(self, text: Any, style: ParagraphStyle | None = None) -> Paragraph:
        value = safe(self._stringify(text) or "—").replace("\n", "<br/>")
        return Paragraph(value, style or self.body)

    def _cell(self, value: Any, style: ParagraphStyle | None = None) -> Paragraph:
        if isinstance(value, Paragraph):
            return value
        text = safe(self._stringify(value) or "—").replace("\n", "<br/>")
        return Paragraph(text, style or self.table_cell)

    def _build_table(
        self,
        headers: Sequence[Any],
        rows: Sequence[Sequence[Any]],
        col_widths: Sequence[float],
        header_bg: colors.Color,
        *,
        cell_style: ParagraphStyle | None = None,
        extra_styles: Sequence[tuple] | None = None,
        header_style: ParagraphStyle | None = None,
    ) -> Table:
        data = [[self._cell(head, header_style or self.table_head) for head in headers]]
        for row in rows:
            data.append([self._cell(cell, cell_style or self.table_cell) for cell in row])

        table = Table(data, colWidths=list(col_widths), repeatRows=1, hAlign="LEFT")
        styles: list[tuple] = [
            ("BACKGROUND", (0, 0), (-1, 0), header_bg),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BACKGROUND", (0, 1), (-1, -1), colors.white),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, self.palette["panel"]]),
            ("GRID", (0, 0), (-1, -1), 0.35, self.palette["line"]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]
        if extra_styles:
            styles.extend(extra_styles)
        table.setStyle(TableStyle(styles))
        return table

    def _note_box(self, text: str, tone: str = "slate") -> Table:
        tone_map = {
            "slate": (self.palette["panel"], self.palette["line"], self.palette["muted"]),
            "amber": (self.palette["amber"], self.palette["amber_border"], self.palette["amber_text"]),
            "critical": (self.palette["red_soft"], self.palette["red"], self.palette["red_text"]),
            "success": (self.palette["green_soft"], self.palette["teal_dark"], self.palette["teal_dark"]),
        }
        bg, border, text_color = tone_map.get(tone, tone_map["slate"])
        style = ParagraphStyle(
            f"note_{tone}",
            parent=self.body_tight,
            textColor=text_color,
            leading=11,
        )
        box = Table([[Paragraph(safe(text), style)]], colWidths=[176 * mm], hAlign="LEFT")
        box.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), bg),
                    ("BOX", (0, 0), (-1, -1), 0.7, border),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        return box

    def _append_bullets(
        self,
        story: list[Any],
        items: Iterable[Any],
        *,
        empty_text: str = "None documented.",
        max_items: int = 10,
    ):
        clean_items = self._clean_items(items)[:max_items]
        if not clean_items:
            story.append(self._para(empty_text, self.body_tight))
            return
        for item in clean_items:
            story.append(Paragraph(f"&bull; {safe(item)}", self.bullet))

    def _clean_items(self, items: Iterable[Any]) -> list[str]:
        cleaned: list[str] = []
        for item in items:
            text = _filter_api_error(self._stringify(item))
            text = re.sub(r"\s+", " ", text).strip(" ;,-")
            if text:
                cleaned.append(text)
        return cleaned

    def _stringify(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, dict):
            ordered_bits: list[str] = []
            preferred_keys = [
                "test",
                "value",
                "status",
                "time",
                "symptom",
                "severity",
                "diagnosis",
                "reason",
                "drug",
                "detail",
                "source",
                "title",
                "url",
                "raw",
                "text",
            ]
            for key in preferred_keys:
                raw = value.get(key)
                if raw not in (None, "", [], {}):
                    ordered_bits.append(f"{key.replace('_', ' ').title()}: {raw}")
            if ordered_bits:
                return "; ".join(ordered_bits)
            return "; ".join(
                f"{str(k).replace('_', ' ').title()}: {v}"
                for k, v in value.items()
                if v not in (None, "", [], {})
            )
        if isinstance(value, list):
            return ", ".join(self._stringify(item) for item in value if item not in (None, "", [], {}))
        return str(value).strip()

    def _format_confidence(self, value: Any) -> str:
        try:
            return f"{float(value or 0.0):.0%}"
        except (TypeError, ValueError):
            return "—"

    def _format_url(self, value: Any, max_len: int = 96) -> str:
        text = self._truncate_middle(self._stringify(value), max_len)
        escaped = safe(text)
        return (
            escaped
            .replace("/", "/&#8203;")
            .replace("?", "?&#8203;")
            .replace("&amp;", "&amp;&#8203;")
            .replace("=", "=&#8203;")
        )

    def _truncate_middle(self, text: str, max_len: int) -> str:
        if len(text) <= max_len:
            return text
        keep = max(8, (max_len - 3) // 2)
        return f"{text[:keep]}...{text[-keep:]}"

    def _external_link_paragraph(
        self,
        url: Any,
        *,
        label: str = "Open source",
        caption: str | None = None,
    ) -> Paragraph:
        target = self._stringify(url)
        if not target:
            return self._cell("Unavailable", self.table_cell_sm)

        href = escape(target, quote=True)
        display_caption = self._format_url(caption or target, max_len=72)
        return Paragraph(
            (
                f'<link href="{href}"><u>{safe(label)}</u></link>'
                f'<br/><font color="#475569">{display_caption}</font>'
            ),
            self.link_cell,
        )

    # ------------------------------------------------------------------ #
    # Sections required by doctor-facing contract
    # ------------------------------------------------------------------ #
    def _header(self, story: list[Any], data: dict[str, Any]):
        case_id = data.get("case_id", "unknown")
        story.append(Paragraph("MediCascade Clinical Report", self.title))
        story.append(
            Paragraph(
                (
                    "Annotated doctor-facing output"
                    f" | Case ID: {safe(case_id)}"
                    f" | Generated: {datetime.utcnow().isoformat()}Z"
                ),
                self.sub,
            )
        )
        story.append(HRFlowable(width="100%", thickness=0.9, color=self.palette["line"]))
        story.append(Spacer(1, 6))

    def _patient_summary(self, story: list[Any], data: dict[str, Any]):
        story.append(Paragraph("Patient Summary", self.h2))
        summary = data.get("patient_summary", {}) or {}
        demographics = summary.get("demographics", {}) or {}
        vitals = summary.get("vitals", {}) or {}
        key_facts = summary.get("key_facts", []) or []

        demo_rows = [[str(k), str(v)] for k, v in demographics.items() if v not in (None, "")]
        if demo_rows:
            story.append(
                self._build_table(
                    ["Field", "Value"],
                    demo_rows[:12],
                    [52 * mm, 124 * mm],
                    self.palette["slate_dark"],
                )
            )
        else:
            story.append(self._note_box("No demographic fields were extracted from the uploaded record."))
        story.append(Spacer(1, 4))

        story.append(Paragraph("Vitals", self.h3))
        vital_rows = [[str(k), str(v)] for k, v in vitals.items() if v not in (None, "")]
        if vital_rows:
            story.append(
                self._build_table(
                    ["Vital", "Value"],
                    vital_rows[:12],
                    [64 * mm, 112 * mm],
                    self.palette["blue_dark"],
                )
            )
        else:
            story.append(self._note_box("Vitals were not available in the uploaded material."))
        story.append(Spacer(1, 4))

        story.append(Paragraph("Key Clinical Facts", self.h3))
        fact_rows: list[list[str]] = []
        for fact in self._clean_items(key_facts)[:10]:
            if ":" in fact:
                left, right = fact.split(":", 1)
                fact_rows.append([left.strip(), right.strip()])
            else:
                fact_rows.append(["Clinical note", fact])
        if fact_rows:
            story.append(
                self._build_table(
                    ["Finding", "Value"],
                    fact_rows,
                    [62 * mm, 114 * mm],
                    self.palette["slate_dark"],
                )
            )
        else:
            story.append(self._para("No key clinical facts were available for this report.", self.body_tight))

    def _urgent_red_flags(self, story: list[Any], data: dict[str, Any]):
        story.append(Paragraph("Urgent Red Flags", self.h2))
        red_flags = self._clean_items(data.get("urgent_red_flags", []) or [])
        if not red_flags:
            story.append(self._para("No urgent red flags were identified by the validator.", self.body))
            return

        story.append(
            Paragraph(
                "Immediate clinical review recommended based on high-risk findings in this case.",
                self.alert_banner,
            )
        )
        rows = [["High", flag] for flag in red_flags[:10]]
        story.append(
            self._build_table(
                ["Priority", "Critical finding"],
                rows,
                [24 * mm, 152 * mm],
                self.palette["red"],
                extra_styles=[
                    ("BACKGROUND", (0, 1), (0, -1), self.palette["red"]),
                    ("BACKGROUND", (1, 1), (1, -1), self.palette["red_soft"]),
                    ("TEXTCOLOR", (0, 1), (0, -1), colors.white),
                    ("TEXTCOLOR", (1, 1), (1, -1), self.palette["red_text"]),
                    ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                    ("ALIGN", (0, 1), (0, -1), "CENTER"),
                ],
            )
        )

    def _primary_diagnosis(self, story: list[Any], data: dict[str, Any]):
        story.append(Paragraph("Primary Diagnosis", self.h2))
        diagnosis = self._stringify(data.get("diagnosis", "Undetermined")) or "Undetermined"
        confidence = self._format_confidence(data.get("confidence", 0.0))
        card = Table(
            [[
                Paragraph(f"<b>{safe(diagnosis)}</b>", self.body),
                Paragraph(f"<b>Confidence:</b> {safe(confidence)}", self.body),
            ]],
            colWidths=[124 * mm, 52 * mm],
            hAlign="LEFT",
        )
        card.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), self.palette["panel"]),
                    ("BOX", (0, 0), (-1, -1), 0.6, self.palette["line"]),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ]
            )
        )
        story.append(card)

    def _icd10_section(self, story: list[Any], data: dict[str, Any]):
        icd_code = self._stringify(data.get("icd10_code", ""))
        icd_desc = self._stringify(data.get("icd10_description", ""))
        if not icd_code or icd_code == "R69":
            return

        story.append(Paragraph("ICD-10-CM Classification", self.h2))
        story.append(
            self._build_table(
                ["Code", "Description"],
                [[icd_code, icd_desc or "Not available"]],
                [28 * mm, 148 * mm],
                self.palette["amber_border"],
                extra_styles=[
                    ("BACKGROUND", (0, 1), (-1, -1), self.palette["amber"]),
                    ("TEXTCOLOR", (0, 1), (-1, -1), self.palette["amber_text"]),
                    ("GRID", (0, 0), (-1, -1), 0.5, self.palette["amber_border"]),
                ],
            )
        )

        match_type = self._stringify(data.get("icd10_match_type", "")).lower()
        warning = self._stringify(data.get("icd10_warning", ""))
        if match_type == "unmatched" or warning:
            note = warning or "ICD-10 code could not be automatically assigned. Please verify manually."
            story.append(Spacer(1, 4))
            story.append(self._note_box(note, tone="amber"))

    def _differentials(self, story: list[Any], data: dict[str, Any]):
        story.append(Paragraph("Differential Diagnoses", self.h2))
        differentials = data.get("secondary_diagnoses", []) or []
        rows: list[list[str]] = []
        for item in differentials[:8]:
            if isinstance(item, dict):
                rows.append(
                    [
                        self._stringify(item.get("diagnosis", "")) or "Differential",
                        self._stringify(item.get("icd10_code", "—")) or "—",
                        self._format_confidence(item.get("confidence", 0.0)),
                        self._stringify(item.get("reason", "")) or "Clinical rationale not provided.",
                    ]
                )
            else:
                rows.append([self._stringify(item), "—", "—", "Clinical rationale not provided."])

        if not rows:
            story.append(self._para("No additional differential diagnoses were listed.", self.body))
            return

        story.append(
            self._build_table(
                ["Diagnosis", "ICD-10", "Conf.", "Reason"],
                rows,
                [54 * mm, 18 * mm, 16 * mm, 88 * mm],
                self.palette["blue_dark"],
            )
        )

    def _drug_safety_section(self, story: list[Any], data: dict[str, Any]):
        ds = data.get("drug_safety", {}) or {}
        warnings = ds.get("warnings", []) or []
        interactions = ds.get("interactions", []) or []
        contraindications = ds.get("contraindications", []) or []
        if not any([warnings, interactions, contraindications]):
            return

        story.append(Paragraph("FDA Drug Safety", self.h2))
        story.append(
            self._para(
                "FDA label data was retrieved for medications identified in this case. "
                "High-priority safety details are summarized below.",
                self.body,
            )
        )

        self._drug_detail_table(
            story,
            "Boxed / Serious Warnings",
            warnings,
            header_bg=self.palette["red"],
            detail_bg=self.palette["red_soft"],
        )
        self._drug_detail_table(
            story,
            "Drug Interactions",
            interactions,
            header_bg=self.palette["amber_border"],
            detail_bg=self.palette["amber"],
        )
        self._drug_detail_table(
            story,
            "Contraindications",
            contraindications,
            header_bg=self.palette["red"],
            detail_bg=self.palette["red_soft"],
        )

    def _drug_detail_table(
        self,
        story: list[Any],
        title: str,
        items: list[dict[str, Any]],
        *,
        header_bg: colors.Color,
        detail_bg: colors.Color,
    ):
        rows: list[list[str]] = []
        for item in items[:6]:
            drug = self._stringify(item.get("drug", "")) or "Medication"
            detail = _filter_api_error(self._stringify(item.get("detail", "")))
            if detail:
                rows.append([drug, self._truncate_middle(detail, 420)])
        if not rows:
            return

        story.append(Paragraph(title, self.h3))
        story.append(
            self._build_table(
                ["Medication", "Clinical summary"],
                rows,
                [34 * mm, 142 * mm],
                header_bg,
                cell_style=self.table_cell_sm,
                extra_styles=[
                    ("BACKGROUND", (1, 1), (1, -1), detail_bg),
                ],
            )
        )
        story.append(Spacer(1, 4))

    def _evidence_links(self, story: list[Any], data: dict[str, Any]):
        story.append(Paragraph("Peer-Reviewed Evidence (PubMed / NICE / WHO)", self.h2))
        links = data.get("evidence_links", []) or []
        rows: list[list[Paragraph]] = []
        for item in links[:16]:
            source = self._stringify(item.get("source", "")) or "Source"
            source_url = self._stringify(item.get("url", ""))
            title = self._stringify(item.get("title", "")) or "Untitled reference"
            snippet = self._stringify(item.get("snippet", "")) or "No snippet available."
            if source_url:
                summary = Paragraph(
                    (
                        f'<link href="{escape(source_url, quote=True)}"><b><u>{safe(self._truncate_middle(title, 120))}</u></b></link>'
                        f'<br/>{safe(self._truncate_middle(snippet, 220))}'
                    ),
                    self.link_cell,
                )
                source_cell = self._external_link_paragraph(source_url, label=source, caption=source_url)
                url_cell = self._external_link_paragraph(source_url, label="Open source", caption=source_url)
            else:
                summary = Paragraph(
                    f"<b>{safe(self._truncate_middle(title, 120))}</b><br/>{safe(self._truncate_middle(snippet, 220))}",
                    self.table_cell_sm,
                )
                source_cell = self._cell(source, self.table_cell_sm)
                url_cell = self._cell("Unavailable", self.table_cell_sm)
            rows.append([source_cell, summary, url_cell])

        if not rows:
            story.append(self._para("No supporting evidence links were attached.", self.body))
            return

        table = Table(
            [[self._cell("Source", self.table_head), self._cell("Evidence summary", self.table_head), self._cell("Reference", self.table_head)]]
            + rows,
            colWidths=[22 * mm, 96 * mm, 58 * mm],
            repeatRows=1,
            hAlign="LEFT",
        )
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), self.palette["teal_dark"]),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.35, self.palette["line"]),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, self.palette["panel"]]),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(table)

    def _layer1_findings(self, story: list[Any], data: dict[str, Any]):
        story.append(Paragraph("Layer 1 Specialist Findings", self.h2))
        section = data.get("layer1_findings", {}) or {}

        candidates = section.get("candidate_diagnoses", []) or []
        story.append(Paragraph("Candidate Diagnoses", self.h3))
        candidate_rows: list[list[str]] = []
        for item in candidates[:8]:
            if not isinstance(item, dict):
                continue
            candidate_rows.append(
                [
                    self._stringify(item.get("agent", "")) or "Specialist",
                    self._stringify(item.get("diagnosis", "")) or "Not provided",
                    self._format_confidence(item.get("confidence", 0.0)),
                ]
            )
        if candidate_rows:
            story.append(
                self._build_table(
                    ["Specialist", "Diagnosis", "Confidence"],
                    candidate_rows,
                    [34 * mm, 122 * mm, 20 * mm],
                    self.palette["blue_dark"],
                )
            )
        else:
            story.append(self._para("No candidate diagnoses were returned by specialist agents.", self.body_tight))

        story.append(Spacer(1, 4))
        story.append(Paragraph("Red Flags", self.h3))
        self._append_bullets(
            story,
            section.get("red_flags", []) or [],
            empty_text="No Layer 1 red flags were listed.",
            max_items=10,
        )

        story.append(Spacer(1, 4))
        story.append(Paragraph("Abnormal Labs", self.h3))
        lab_rows: list[list[str]] = []
        for lab in (section.get("abnormal_labs", []) or [])[:12]:
            if isinstance(lab, dict):
                lab_rows.append(
                    [
                        self._stringify(lab.get("test", "")) or self._stringify(lab.get("raw", "")) or "Laboratory item",
                        self._stringify(lab.get("value", "")) or "Review",
                        self._stringify(lab.get("status", "")) or "Review",
                    ]
                )
            else:
                lab_rows.append([self._stringify(lab), "Review", "Review"])
        if lab_rows:
            story.append(
                self._build_table(
                    ["Test", "Value", "Status"],
                    lab_rows,
                    [88 * mm, 48 * mm, 40 * mm],
                    self.palette["slate_dark"],
                )
            )
        else:
            story.append(self._para("No abnormal laboratory results were structured by Layer 1.", self.body_tight))

        story.append(Spacer(1, 4))
        story.append(Paragraph("Symptom Timeline", self.h3))
        timeline_rows: list[list[str]] = []
        for item in (section.get("symptom_timeline", []) or [])[:12]:
            if isinstance(item, dict):
                timeline_rows.append(
                    [
                        self._stringify(item.get("time", "")) or "Not specified",
                        self._stringify(item.get("symptom", "")) or "Symptom",
                        self._stringify(item.get("severity", "")) or "Not specified",
                    ]
                )
            else:
                timeline_rows.append(["Not specified", self._stringify(item), "Not specified"])
        if timeline_rows:
            story.append(
                self._build_table(
                    ["Time", "Symptom", "Severity"],
                    timeline_rows,
                    [30 * mm, 116 * mm, 30 * mm],
                    self.palette["blue_dark"],
                )
            )
        else:
            story.append(self._para("No symptom timeline was extracted from the clinical notes.", self.body_tight))

        story.append(Spacer(1, 4))
        story.append(Paragraph("Risk Factors / Management Signals", self.h3))
        self._append_bullets(
            story,
            section.get("risk_factors", []) or [],
            empty_text="No risk factors or management signals were surfaced by Layer 1.",
            max_items=12,
        )

    def _layer2_validated(self, story: list[Any], data: dict[str, Any]):
        story.append(Paragraph("Layer 2 Validated Conclusions", self.h2))
        section = data.get("layer2_validated", {}) or {}
        labels = [
            ("Final Problem List", "final_problem_list", "No validated problem list was provided."),
            ("Supported Findings", "supported_findings", "No supported findings were explicitly listed."),
            ("Uncertain Findings", "uncertain_findings", "No uncertainty notes were recorded."),
            ("Contradicted Findings", "contradicted_findings", "No contradicted findings were recorded."),
            ("Missing Data", "missing_data", "No missing-data items were recorded."),
        ]
        for label, key, empty_text in labels:
            story.append(Paragraph(label, self.h3))
            self._append_bullets(story, section.get(key, []) or [], empty_text=empty_text, max_items=12)
            story.append(Spacer(1, 2))

    def _data_flow_transparency(self, story: list[Any], data: dict[str, Any]):
        story.append(Paragraph("Data Flow Transparency", self.h2))
        trace = data.get("data_flow_trace", []) or []
        rows: list[list[str]] = []
        for item in trace[:8]:
            rows.append(
                [
                    self._stringify(item.get("layer", "")) or "Layer",
                    self._stringify(item.get("input", "")) or "Input not provided",
                    self._stringify(item.get("output", "")) or "Output not provided",
                    self._stringify(item.get("status", "")) or "unknown",
                ]
            )
        if not rows:
            story.append(self._para("No trace metadata was provided.", self.body))
            return

        story.append(
            self._build_table(
                ["Layer", "Input", "Output", "Status"],
                rows,
                [36 * mm, 44 * mm, 74 * mm, 22 * mm],
                self.palette["slate_dark"],
                cell_style=self.table_cell_sm,
            )
        )

    def _xai(self, story: list[Any], data: dict[str, Any]):
        story.append(Paragraph("XAI Section (Why this diagnosis)", self.h2))
        reasoning = self._stringify(data.get("reasoning", "")).strip()
        if not reasoning:
            story.append(self._para("No XAI narrative was available.", self.body))
            return

        heading_pattern = re.compile(r"^\d+[\)\.]?\s+")
        for raw_line in reasoning.splitlines():
            line = raw_line.strip()
            if not line:
                story.append(Spacer(1, 2))
                continue

            cleaned = line.replace("**", "").strip()
            if not cleaned:
                continue

            lowered = cleaned.lower()
            if heading_pattern.match(cleaned) or lowered.startswith(
                (
                    "clinical summary",
                    "why primary diagnosis",
                    "differential reasoning",
                    "red-flag interpretation",
                    "evidence grounding",
                    "uncertainty and missing data",
                    "recommended next tests/actions",
                    "recommended next steps/actions",
                )
            ):
                story.append(Paragraph(safe(cleaned), self.h3))
                continue

            if cleaned.startswith("- "):
                story.append(Paragraph(f"&bull; {safe(cleaned[2:].strip())}", self.bullet))
                continue

            story.append(self._para(cleaned, self.body))

    def _next_steps(self, story: list[Any], data: dict[str, Any]):
        story.append(Paragraph("Recommended Next Steps / Tests", self.h2))
        steps = data.get("recommendations", []) or []
        self._append_bullets(
            story,
            steps,
            empty_text="No explicit recommendations were generated.",
            max_items=12,
        )

    def _critical_highlights(self, story: list[Any], data: dict[str, Any]):
        story.append(Paragraph("Critical Data Highlights", self.h2))
        points = data.get("critical_points", []) or []
        if not points:
            targets = data.get("highlight_targets", []) or []
            points = [
                {
                    "phrase": item.get("text_span", "Critical data point"),
                    "reason": "Marked as clinically relevant for manual review.",
                    "severity": "HIGH",
                }
                for item in targets
            ]
        if not points:
            story.append(self._para("No critical highlights were available.", self.body))
            return

        story.append(
            self._note_box(
                "Critical findings are summarized below in a print-friendly review format.",
                tone="critical",
            )
        )
        story.append(Spacer(1, 4))

        for item in points[:10]:
            severity = (self._stringify(item.get("severity", "")) or "HIGH").upper()
            phrase = self._stringify(item.get("phrase", "")) or "Critical value"
            reason = self._stringify(item.get("reason", "")) or "Marked as clinically relevant."
            detail = Paragraph(
                f"<b>{safe(phrase)}</b><br/>{safe(reason)}",
                self.highlight_text,
            )
            card = Table(
                [[Paragraph(safe(severity), self.badge), detail]],
                colWidths=[26 * mm, 150 * mm],
                hAlign="LEFT",
            )
            card.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), self.palette["red_soft"]),
                        ("BACKGROUND", (0, 0), (0, 0), self.palette["red"]),
                        ("TEXTCOLOR", (0, 0), (0, 0), colors.white),
                        ("BOX", (0, 0), (-1, -1), 0.55, self.palette["red"]),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 7),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                        ("TOPPADDING", (0, 0), (-1, -1), 7),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                    ]
                )
            )
            story.append(card)
            story.append(Spacer(1, 4))

    def _footer(self, story: list[Any]):
        story.append(Spacer(1, 6))
        story.append(
            Paragraph(
                "This report supports, but does not replace, clinician judgement.",
                self.small,
            )
        )


def _filter_api_error(text: str) -> str:
    lower = text.lower()
    error_markers = [
        "client error",
        "server error",
        "too many requests",
        "payload too large",
        "rate_limit",
        "413 ",
        "429 ",
        "500 ",
        "502 ",
        "503 ",
        "httpsconnectionpool",
        "connection aborted",
        "remotedisconnected",
        "groq failed:",
        "openrouter fallback failed:",
        "body=",
    ]
    for marker in error_markers:
        if marker in lower:
            return ""
    return text


def safe(text: Any) -> str:
    return escape(str(text), quote=False)


pdf_annotator = PDFAnnotator()
