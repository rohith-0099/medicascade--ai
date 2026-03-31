"""
Medical content screener for MediCascade.

Performs a fast AI-based check using Groq before the full 4-layer pipeline
runs. If the uploaded PDF is not a medical/clinical/healthcare document, it
is rejected with a clear error message.

Graceful degradation: if Groq is unavailable or the API key is missing,
screening is skipped and the pipeline proceeds normally.
"""

import logging
from typing import Tuple

logger = logging.getLogger(__name__)

# Maximum characters of PDF text to send to the screener (keeps it fast and cheap).
_SAMPLE_CHARS = 1500


def _extract_text_sample(pdf_path: str) -> str:
    """Extract a short text sample from the first few pages of the PDF."""
    # Primary: pdfplumber (already used by Layer 0)
    try:
        import pdfplumber
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages[:4]:
                page_text = page.extract_text() or ""
                text += page_text
                if len(text) >= _SAMPLE_CHARS:
                    break
        if text.strip():
            return text[:_SAMPLE_CHARS].strip()
    except Exception as e:
        logger.warning(f"[Screener] pdfplumber extraction failed: {e}")

    # Fallback: PyPDF2 (also already installed)
    try:
        import PyPDF2
        text = ""
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages[:4]:
                page_text = page.extract_text() or ""
                text += page_text
                if len(text) >= _SAMPLE_CHARS:
                    break
        return text[:_SAMPLE_CHARS].strip()
    except Exception as e:
        logger.warning(f"[Screener] PyPDF2 fallback failed: {e}")

    return ""


def screen_medical_document(pdf_path: str) -> Tuple[bool, str]:
    """
    Check whether the given PDF is a medical/clinical/healthcare document.

    Returns:
        (True, "")           — document is medical, proceed with pipeline.
        (False, reason)      — document is NOT medical, reason explains why.
        (True, "skipped")    — screener unavailable, pipeline proceeds normally.
    """
    # Import here to avoid circular import issues
    try:
        from config import settings
        from groq import Groq
    except ImportError:
        logger.warning("[Screener] Groq library not installed, skipping screening.")
        return True, "skipped: groq not installed"

    if not settings.GROQ_API_KEY:
        logger.warning("[Screener] GROQ_API_KEY not set, skipping screening.")
        return True, "skipped: no api key"

    text_sample = _extract_text_sample(pdf_path)

    if not text_sample:
        # Could not extract any text (scanned image PDF, etc.) — let later
        # layers handle it rather than blocking unconditionally.
        logger.warning("[Screener] Empty text sample, skipping screening.")
        return True, "skipped: no extractable text"

    prompt = (
        "You are a strict medical document classifier.\n"
        "Your ONLY task is to determine if the text excerpt below is from a "
        "medical, clinical, or healthcare-related document (e.g. patient record, "
        "lab report, discharge summary, prescription, radiology report, clinical notes).\n\n"
        "Reply with exactly ONE word: YES or NO. No explanation.\n\n"
        f"--- Document excerpt ---\n{text_sample}\n--- End of excerpt ---"
    )

    try:
        client = Groq(api_key=settings.GROQ_API_KEY)
        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=5,
            temperature=0.0,
        )
        answer = response.choices[0].message.content.strip().upper()
        logger.info(f"[Screener] Groq classifier answered: '{answer}'")

        if answer.startswith("YES"):
            return True, ""
        elif answer.startswith("NO"):
            return False, (
                "This does not appear to be a medical or clinical document. "
                "MediCascade only processes patient records, lab reports, "
                "discharge summaries, and similar healthcare documents."
            )
        else:
            # Unexpected answer — fail open to avoid blocking valid documents.
            logger.warning(f"[Screener] Unexpected classifier response: '{answer}', allowing through.")
            return True, "skipped: ambiguous response"

    except Exception as e:
        logger.warning(f"[Screener] Groq call failed ({e}), skipping screening.")
        return True, f"skipped: {e}"
