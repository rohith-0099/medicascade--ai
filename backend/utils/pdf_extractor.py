"""
PDF Extractor — Layer 0 Data Extraction
Uses pdfplumber (primary) and PyPDF2 (fallback) only.
pdf2image / Pillow intentionally removed — not compatible with Python 3.14.
OCR via pytesseract is attempted only when pytesseract is available.
"""

import io
import base64
import re
import PyPDF2
import pdfplumber
from typing import List, Dict, Any, Tuple


class PDFExtractor:

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path

    # ── Text extraction ────────────────────────────────────────────────────────

    def extract_text(self) -> str:
        """Extract raw text. Tries pdfplumber first (better layout), then PyPDF2."""
        text = ""

        # Primary: pdfplumber (handles complex layouts + tables better)
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            if len(text.strip()) >= 100:
                return text.strip()
        except Exception as e:
            print(f"[PDFExtractor] pdfplumber failed: {e}")

        # Fallback: PyPDF2
        try:
            with open(self.pdf_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print(f"[PDFExtractor] PyPDF2 fallback failed: {e}")

        return text.strip()

    def extract_text_with_ocr(self) -> str:
        """OCR using pytesseract (only if available and Pillow is installed)."""
        try:
            import pytesseract
            from PIL import Image as PilImage
            # Try to find page images via pdfplumber page renders
            pages_text = ""
            with pdfplumber.open(self.pdf_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    try:
                        img = page.to_image(resolution=200)
                        # page.to_image returns a PIL-backed image
                        pil_img = img.original
                        ocr_text = pytesseract.image_to_string(pil_img)
                        pages_text += f"\n--- Page {i+1} ---\n{ocr_text}\n"
                    except Exception as pe:
                        print(f"[PDFExtractor] OCR page {i+1} failed: {pe}")
            return pages_text.strip()
        except ImportError:
            print("[PDFExtractor] pytesseract / Pillow not available — skipping OCR")
            return ""
        except Exception as e:
            print(f"[PDFExtractor] OCR extraction failed: {e}")
            return ""

    # ── Table extraction ───────────────────────────────────────────────────────

    def extract_tables(self) -> List[Dict[str, Any]]:
        """Extract all tables from the PDF via pdfplumber."""
        tables = []
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    for table_num, table in enumerate(page.extract_tables() or []):
                        if not table:
                            continue
                        headers = table[0] or [f"Column {i}" for i in range(len(table[0] or []))]
                        rows = table[1:]
                        tables.append({
                            "page": page_num + 1,
                            "table_number": table_num + 1,
                            "headers": headers,
                            "rows": rows,
                            "data": [
                                {headers[i]: row[i] for i in range(min(len(headers), len(row)))}
                                for row in rows
                            ]
                        })
        except Exception as e:
            print(f"[PDFExtractor] Table extraction failed: {e}")
        return tables

    # ── Image extraction ──────────────────────────────────────────────────────

    def extract_images(self) -> List[str]:
        """
        Render each PDF page as an image (base64 PNG) via pdfplumber.
        Falls back to extracting embedded image bytes if rendering unavailable.
        """
        images_base64 = []

        # Attempt 1: pdfplumber page render (needs Pillow, gracefully skipped)
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for page in pdf.pages:
                    img = page.to_image(resolution=150)
                    buf = io.BytesIO()
                    img.save(buf, format="PNG")
                    images_base64.append(base64.b64encode(buf.getvalue()).decode())
            if images_base64:
                return images_base64
        except Exception:
            pass  # Pillow not available — fall through to embedded extraction

        # Attempt 2: extract raw embedded image bytes via PyPDF2
        return self.extract_embedded_images()

    def extract_embedded_images(self) -> List[str]:
        """Extract JPEG/raw image objects embedded in the PDF."""
        images_base64 = []
        try:
            with open(self.pdf_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    resources = page.get("/Resources", {})
                    xobjects = resources.get("/XObject", {})
                    if hasattr(xobjects, "get_object"):
                        xobjects = xobjects.get_object()
                    for obj_name in xobjects:
                        xobj = xobjects[obj_name]
                        if hasattr(xobj, "get_object"):
                            xobj = xobj.get_object()
                        if xobj.get("/Subtype") == "/Image":
                            try:
                                data = xobj.get_data()
                                images_base64.append(base64.b64encode(data).decode())
                            except Exception:
                                pass
        except Exception as e:
            print(f"[PDFExtractor] Embedded image extraction failed: {e}")
        return images_base64

    # ── Smart combined extract ─────────────────────────────────────────────────

    def smart_extract(self) -> Tuple[str, List[str]]:
        """
        Decides extraction strategy based on text density:
        - Text-rich PDFs: extract text + embedded images
        - Scanned/image PDFs: attempt OCR then page renders
        """
        text = self.extract_text()
        text_len = len(text.strip())

        if text_len >= 200:
            print(f"[PDFExtractor] Text-rich document ({text_len} chars). Using embedded images.")
            images = self.extract_embedded_images()
        else:
            print(f"[PDFExtractor] Low text ({text_len} chars). Attempting OCR + page renders.")
            ocr_text = self.extract_text_with_ocr()
            if len(ocr_text) > text_len:
                text = ocr_text
            images = self.extract_images()

        return text, images
