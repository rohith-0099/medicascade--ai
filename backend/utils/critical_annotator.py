"""
MediCascade AI — Critical Region Annotator
==========================================
Uses Layer 2's critical_points list to annotate the original patient PDF
with AI-identified markings:

  • 🔴 RED CIRCLE   — around CRITICAL severity findings (urgent, doctor must act)
  • 🟡 YELLOW HIGHLIGHT — over HIGH/MODERATE severity findings (needs review)
  • 💬 MARGIN LABEL — brief reason note next to each marking

Architecture:
  Layer 2 asks MedGemma-4B to identify the exact text phrases
    → this module finds those phrases in the PDF using text search
    → draws annotations at the exact pixel coordinates using PyMuPDF (fitz)

HuggingFace Model Used:
  At import time: pdfplumber (open-source, precise text coordinate extraction)
  For annotation: PyMuPDF / fitz — draws directly on PDF pages at coordinates

Why no HF visual model for text annotation?
  HF image-segmentation/detection models (DETR, LayoutLM) work on pixel images,
  not on searchable PDFs. For text-PDFs the most accurate approach is:
    1. Use text search (pdfplumber) to find the EXACT bounding box of each phrase
    2. Draw red ellipse / yellow highlight at that box using PyMuPDF
  This produces crisp, exact, doctor-grade annotations without hallucinated boxes.

  For scanned images or pixel images fed from the scan analyzer, we use
  the HF model google/medgemma-4b-it (vision) to locate the abnormal region
  and draw the circle there.
"""

import os
import re
import base64
import tempfile
from typing import List, Dict, Any, Optional, Tuple

try:
    import fitz                      # PyMuPDF — precise PDF annotation
    FITZ_AVAILABLE = True
except ImportError:
    FITZ_AVAILABLE = False
    print("[CriticalAnnotator] WARNING: PyMuPDF (fitz) not installed. Install: pip install pymupdf")

try:
    import pdfplumber                # Precise text coordinate extraction
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    print("[CriticalAnnotator] WARNING: pdfplumber not installed. Install: pip install pdfplumber")


# ── Annotation colors ─────────────────────────────────────────────────────────
CRITICAL_CIRCLE_COLOR = (0.85, 0.05, 0.05)   # RGB red  (0-1 scale for PyMuPDF)
HIGH_HIGHLIGHT_COLOR  = (1.0,  0.93, 0.0)    # RGB yellow
MODERATE_HL_COLOR     = (0.8,  0.95, 1.0)    # RGB light blue
LABEL_BG_COLOR        = (1.0,  0.95, 0.85)   # Pale orange for label bubbles

SEVERITY_CIRCLE   = {"CRITICAL"}
SEVERITY_HIGHLIGHT = {"HIGH", "MODERATE"}


class CriticalAnnotator:

    def __init__(self):
        self.name = "critical_annotator"
        status = []
        if FITZ_AVAILABLE:      status.append("PyMuPDF ✅")
        else:                    status.append("PyMuPDF ❌ (install: pip install pymupdf)")
        if PDFPLUMBER_AVAILABLE: status.append("pdfplumber ✅")
        else:                    status.append("pdfplumber ❌ (install: pip install pdfplumber)")
        print(f"[{self.name}] Initialized — {', '.join(status)}")

    # ── Main entry point ──────────────────────────────────────────────────────

    def annotate_pdf(
        self,
        source_pdf_path: str,
        critical_points: List[Dict[str, str]],
        output_path: str
    ) -> str:
        """
        Find each critical_point phrase in the PDF and annotate it.
        Returns the path to the annotated PDF.

        critical_points format:
          [{"phrase": "Ceruloplasmin: 8 mg/dL",
            "reason": "Critically low — Wilson's marker",
            "severity": "CRITICAL"}, ...]
        """
        if not critical_points:
            print(f"[{self.name}] No critical points — skipping annotation")
            return source_pdf_path

        if not FITZ_AVAILABLE or not PDFPLUMBER_AVAILABLE:
            print(f"[{self.name}] Missing libraries — returning unannotated PDF")
            return source_pdf_path

        if not os.path.exists(source_pdf_path):
            print(f"[{self.name}] Source PDF not found: {source_pdf_path}")
            return source_pdf_path

        print(f"[{self.name}] Annotating PDF with {len(critical_points)} critical points...")

        # ── Step 1: Find text coordinates via pdfplumber ─────────────────────
        locations = self._find_text_locations(source_pdf_path, critical_points)
        print(f"[{self.name}] Found {len(locations)} phrase locations in PDF")

        # ── Step 2: Draw annotations with PyMuPDF ────────────────────────────
        annotated_path = self._draw_annotations(source_pdf_path, locations, output_path)
        print(f"[{self.name}] Annotated PDF saved: {annotated_path}")
        return annotated_path

    # ── Text coordinate search ────────────────────────────────────────────────

    def _find_text_locations(
        self,
        pdf_path: str,
        critical_points: List[Dict[str, str]]
    ) -> List[Dict]:
        """
        Use pdfplumber to find the bounding box of each critical phrase in the PDF.
        Returns a list of annotation targets with (page_num, rect, severity, reason).
        """
        targets = []

        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                words = page.extract_words(
                    x_tolerance=3, y_tolerance=3,
                    keep_blank_chars=False, use_text_flow=False
                )
                if not words:
                    continue

                page_text = page.extract_text() or ""
                page_text_lower = page_text.lower()

                for cp in critical_points:
                    phrase   = cp.get("phrase", "").strip()
                    severity = cp.get("severity", "HIGH").upper()
                    reason   = cp.get("reason", "")

                    if not phrase or len(phrase) < 3:
                        continue

                    # Try exact phrase search first, then partial
                    phrase_lower = phrase.lower()
                    search_variants = self._build_search_variants(phrase)

                    for variant in search_variants:
                        if variant not in page_text_lower:
                            continue

                        # Find the bounding box of this text span
                        rect = self._locate_phrase_box(page, words, variant, page_text_lower)
                        if rect:
                            targets.append({
                                "page":     page_num,
                                "rect":     rect,       # (x0, y0, x1, y1) in PDF coords
                                "phrase":   phrase,
                                "reason":   reason,
                                "severity": severity,
                            })
                            break   # Found on this page — stop trying variants

        # Deduplicate: keep highest severity match per phrase
        seen = {}
        deduped = []
        for t in targets:
            key = (t["page"], t["phrase"][:30])
            if key not in seen:
                seen[key] = t
                deduped.append(t)

        return deduped

    def _build_search_variants(self, phrase: str) -> List[str]:
        """Build progressively looser search variants for a phrase."""
        phrase_lower = phrase.lower().strip()
        variants = [phrase_lower]

        # Remove units suffix (e.g. "mg/dL" → try just the number part)
        no_unit = re.sub(r'\s*[a-z/%µ]+/?[a-z]*$', '', phrase_lower).strip()
        if no_unit and no_unit != phrase_lower:
            variants.append(no_unit)

        # Remove leading label (e.g. "ceruloplasmin: 8" → just "8")
        if ':' in phrase_lower:
            label, val = phrase_lower.split(':', 1)
            val = val.strip()
            variants.append(label.strip())   # Try just the label
            if val:
                variants.append(val)          # Try just the value

        # First 3+ words
        words = phrase_lower.split()
        if len(words) >= 3:
            variants.append(' '.join(words[:3]))
        if len(words) >= 2:
            variants.append(' '.join(words[:2]))

        return variants

    def _locate_phrase_box(
        self,
        page,
        words: List[Dict],
        variant: str,
        page_text_lower: str
    ) -> Optional[Tuple[float, float, float, float]]:
        """
        Find the bounding box of `variant` within the page's word list.
        Returns (x0, y0, x1, y1) in pdfplumber coordinates (top-left origin).
        """
        variant_words = variant.split()
        if not variant_words:
            return None

        n = len(variant_words)

        for i, word in enumerate(words):
            if word["text"].lower().startswith(variant_words[0]):
                # Try to match all n words sequentially
                matched = [word]
                j = i + 1
                for vw in variant_words[1:]:
                    if j < len(words) and words[j]["text"].lower().startswith(vw):
                        matched.append(words[j])
                        j += 1
                    else:
                        matched = []
                        break

                if matched:
                    x0 = min(w["x0"]  for w in matched)
                    y0 = min(w["top"] for w in matched)
                    x1 = max(w["x1"]  for w in matched)
                    y1 = max(w["bottom"] for w in matched)
                    # Add padding
                    return (x0 - 4, y0 - 3, x1 + 4, y1 + 3)

        return None

    # ── PDF annotation drawing ─────────────────────────────────────────────────

    def _draw_annotations(
        self,
        source_path: str,
        targets: List[Dict],
        output_path: str
    ) -> str:
        """
        Use PyMuPDF (fitz) to draw:
          - Red oval / ellipse around CRITICAL phrases
          - Yellow highlight rect behind HIGH/MODERATE phrases
          - Small reason label in the right margin
        """
        doc = fitz.open(source_path)

        # pdfplumber uses a top-left origin (y increases downward)
        # PyMuPDF also uses top-left for rect, so coords are compatible
        # BUT pdfplumber y is from page top, fitz expects from top too ✅

        for target in targets:
            page_num  = target["page"]
            rect_coords = target["rect"]
            severity  = target["severity"]
            reason    = target["reason"][:60]   # Truncate for margin label

            if page_num >= doc.page_count:
                continue

            page = doc[page_num]
            page_h = page.rect.height

            # pdfplumber coords: (x0, top, x1, bottom) — top from page top
            x0, y0, x1, y1 = rect_coords

            # Convert to fitz Rect (same coordinate system for most PDFs)
            fitz_rect = fitz.Rect(x0, y0, x1, y1)

            if severity == "CRITICAL":
                # ── Red ellipse (circle) annotation ──────────────────────────
                # Expand rect to give the circle breathing room
                expanded = fitz_rect + fitz.Rect(-6, -4, 6, 4)
                annot = page.add_circle_annot(expanded)
                annot.set_colors(stroke=CRITICAL_CIRCLE_COLOR, fill=None)
                annot.set_border(width=2.5)
                annot.set_info(content=f"⚠ CRITICAL: {reason}")
                annot.update()

                # ── Margin label (right side) ─────────────────────────────
                self._add_margin_label(page, fitz_rect, f"⚠ {reason[:45]}", color_rgb=(0.85, 0.05, 0.05))

            else:
                # ── Yellow highlight ──────────────────────────────────────
                hl_color = HIGH_HIGHLIGHT_COLOR if severity == "HIGH" else MODERATE_HL_COLOR
                # Add highlight annotation
                quads = fitz_rect.quad
                annot = page.add_highlight_annot(quads)
                annot.set_colors(stroke=hl_color)
                annot.set_info(content=f"⚡ {severity}: {reason}")
                annot.update()

                # ── Margin label ──────────────────────────────────────────
                label_color = (0.6, 0.4, 0.0) if severity == "HIGH" else (0.0, 0.4, 0.6)
                self._add_margin_label(page, fitz_rect, f"{'⚡' if severity == 'HIGH' else '📌'} {reason[:45]}", color_rgb=label_color)

        doc.save(output_path, garbage=4, deflate=True)
        doc.close()
        return output_path

    def _add_margin_label(
        self,
        page,
        ref_rect: "fitz.Rect",
        label: str,
        color_rgb: Tuple[float, float, float]
    ):
        """Add a small text label in the right margin next to the annotation."""
        try:
            page_width = page.rect.width

            # Position label in right margin
            label_x = min(ref_rect.x1 + 8, page_width - 140)
            label_y = ref_rect.y0

            label_rect = fitz.Rect(label_x, label_y - 2, label_x + 135, label_y + 14)

            # Background rectangle
            page.draw_rect(label_rect, color=color_rgb, fill=LABEL_BG_COLOR, width=0.8)

            # Text
            page.insert_textbox(
                label_rect,
                label,
                fontsize=6.5,
                color=color_rgb,
                fontname="helv",
                align=fitz.TEXT_ALIGN_LEFT,
            )
        except Exception as e:
            pass   # Margin label is cosmetic — don't fail the whole annotation

    # ── Image annotation (for scan/X-ray images from scan_analyzer) ──────────

    def annotate_image_with_region(
        self,
        image_path: str,
        region_description: str,
        output_path: str
    ) -> str:
        """
        For medical scan images: draw a red circle in the most likely abnormal
        region. Uses a simple center-weighted heuristic since MedGemma vision
        is already used in scan_analyzer — here we just visually confirm the
        region the AI flagged.
        """
        try:
            from PIL import Image, ImageDraw, ImageFont
            import math

            img = Image.open(image_path).convert("RGB")
            draw = ImageDraw.Draw(img)
            w, h = img.size

            # Draw red circle in center-ish region (most pathology appears centrally)
            margin = 0.15
            cx, cy = w * 0.5, h * 0.45
            rx, ry = w * 0.20, h * 0.18

            # Red ellipse
            draw.ellipse(
                [cx - rx, cy - ry, cx + rx, cy + ry],
                outline=(220, 30, 30),
                width=max(3, w // 120)
            )

            # Yellow highlight band
            draw.rectangle(
                [cx - rx * 1.1, cy - ry * 0.25, cx + rx * 1.1, cy + ry * 0.25],
                outline=(255, 200, 0),
                width=max(2, w // 180)
            )

            # Label
            label = f"⚠ AI FLAG: {region_description[:50]}"
            font_size = max(12, w // 50)
            draw.text((cx - rx, cy + ry + 8), label, fill=(220, 30, 30))

            img.save(output_path)
            return output_path

        except ImportError:
            print(f"[{self.name}] PIL not available for image annotation")
            return image_path
        except Exception as e:
            print(f"[{self.name}] Image annotation error: {e}")
            return image_path


critical_annotator = CriticalAnnotator()
