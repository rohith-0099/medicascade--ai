"""
MediCascade AI — HuggingFace API Client
All URLs are defined here — paste your endpoint directly to override.

The HF Inference ecosystem has two endpoints:
  A) Chat/LLM models (MedGemma, OpenMed):
       https://router.huggingface.co/v1/chat/completions + {"model": "...", "messages": [...]}
  B) Classic pipeline models (BioGPT, GatorTron):
       https://router.huggingface.co/hf-inference/models/{model_id}  + {"inputs": "..."}

If a URL fails, set the override in config.py (HF_CHAT_URL / HF_INFERENCE_URL).
"""

import requests
import json
import re
import time
import os
from typing import Dict, Any, Optional, List
from pathlib import Path
from dotenv import load_dotenv

# Load .env before reading any env vars so the token is always available
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_env_path, override=False)


class MediCascadeHFClient:

    # ── Paste your working URL here if the default stops working ─────────────
    # Chat / OpenAI-compat endpoint (for MedGemma 4B, OpenMed)
    CHAT_URL = os.getenv("HF_CHAT_URL", "https://router.huggingface.co/v1/chat/completions")

    # Classic inference endpoint (for BioGPT-Large, GatorTron NER)
    INFERENCE_URL = os.getenv("HF_INFERENCE_URL", "https://router.huggingface.co/hf-inference/models")

    # Fallback: older style (set HF_BASE_URL env var to override)
    LEGACY_URL = os.getenv("HF_BASE_URL", "https://router.huggingface.co/models")

    def __init__(self):
        self.token = os.getenv("HF_API_TOKEN", "").strip()
        if not self.token:
            raise EnvironmentError(
                "HF_API_TOKEN is not set. "
                "Add it to backend/.env: HF_API_TOKEN=hf_..."
            )
        self.auth_header = {"Authorization": f"Bearer {self.token}"}
        print(f"[HF Client] Token loaded: {self.token[:12]}...")
        print(f"[HF Client] Chat URL  : {self.CHAT_URL}")
        print(f"[HF Client] Infer URL : {self.INFERENCE_URL}")

    # ─────────────────────────────────────────────────────────────────────────
    # Internal POST with retry
    # ─────────────────────────────────────────────────────────────────────────

    def _post(self, url: str, payload: Dict, timeout: int = 60, retries: int = 2) -> Any:
        headers = {**self.auth_header, "Content-Type": "application/json"}
        for attempt in range(retries + 1):
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
                if resp.status_code == 503:
                    wait = 20 * (attempt + 1)
                    print(f"[HF] 503 model loading, waiting {wait}s (attempt {attempt+1})...")
                    time.sleep(wait)
                    continue
                if resp.status_code in (401, 403):
                    print(f"[HF] {resp.status_code} auth error — check token or accept model license.")
                    print(f"[HF] URL: {url}")
                    return {"error": f"auth_{resp.status_code}"}
                if resp.status_code == 404:
                    print(f"[HF] 404 Not Found — URL may have changed: {url}")
                    return {"error": "not_found_404"}
                if resp.status_code == 400:
                    print(f"[HF] 400 Bad Request — {resp.text[:200]}")
                    return {"error": f"bad_request: {resp.text[:100]}"}
                resp.raise_for_status()
                return resp.json()
            except requests.exceptions.Timeout:
                if attempt >= retries:
                    return {"error": "timeout"}
            except requests.exceptions.RequestException as e:
                if attempt >= retries:
                    return {"error": str(e)}
        return {"error": "max_retries"}

    # ─────────────────────────────────────────────────────────────────────────
    # Text generation — tries chat endpoint first, then classic inference
    # ─────────────────────────────────────────────────────────────────────────

    def generate_text(self, model: str, prompt: str,
                      max_new_tokens: int = 512, temperature: float = 0.3) -> str:
        """
        Tries the OpenAI-compat chat endpoint (router /v1/chat/completions).
        Falls back to hf-inference/models/{model} classic endpoint.
        Falls back further to router.huggingface.co/models/{model} (legacy).
        """
        # ── Attempt 1: Chat completions (works for MedGemma, OpenMed) ─────────
        chat_payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_new_tokens,
            "temperature": temperature
        }
        result = self._post(self.CHAT_URL, chat_payload, timeout=90)
        if isinstance(result, dict) and "choices" in result:
            return result["choices"][0]["message"]["content"]
        if isinstance(result, dict) and "error" not in result:
            return str(result)

        print(f"[HF] Chat endpoint failed for {model}, trying classic inference...")

        # ── Attempt 2: Classic hf-inference/models ────────────────────────────
        classic_url = f"{self.INFERENCE_URL}/{model}"
        classic_payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": max_new_tokens,
                "temperature": temperature,
                "return_full_text": False,
                "do_sample": temperature > 0
            }
        }
        result2 = self._post(classic_url, classic_payload, timeout=90)
        if isinstance(result2, list) and len(result2) > 0:
            return result2[0].get("generated_text", "")
        if isinstance(result2, dict) and "generated_text" in result2:
            return result2["generated_text"]

        print(f"[HF] Classic inference failed for {model}, trying legacy URL...")

        # ── Attempt 3: Legacy router/models ──────────────────────────────────
        legacy_url = f"{self.LEGACY_URL}/{model}"
        result3 = self._post(legacy_url, classic_payload, timeout=90)
        if isinstance(result3, list) and len(result3) > 0:
            return result3[0].get("generated_text", "")
        if isinstance(result3, dict) and "generated_text" in result3:
            return result3["generated_text"]

        print(f"[HF] All endpoints failed for {model}")
        return ""

    # ─────────────────────────────────────────────────────────────────────────
    # NER / token-classification (GatorTron)
    # ─────────────────────────────────────────────────────────────────────────

    def ner(self, model: str, text: str) -> List[Dict]:
        """Token-classification via hf-inference (GatorTron NER)."""
        url = f"{self.INFERENCE_URL}/{model}"
        result = self._post(url, {"inputs": text[:512]}, timeout=60)
        if isinstance(result, list):
            return result
        # Try legacy as fallback
        url2 = f"{self.LEGACY_URL}/{model}"
        result2 = self._post(url2, {"inputs": text[:512]}, timeout=60)
        if isinstance(result2, list):
            return result2
        print(f"[HF] NER failed for {model}: {result}")
        return []

    # ─────────────────────────────────────────────────────────────────────────
    # Vision + Text (MedGemma multimodal)
    # ─────────────────────────────────────────────────────────────────────────

    def vision_query(self, model: str, image_bytes: bytes, prompt: str) -> str:
        """Vision+text via multimodal chat endpoint."""
        import base64
        img_b64 = base64.b64encode(image_bytes).decode("utf-8")
        # OpenAI-compat multimodal message format
        chat_payload = {
            "model": model,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                ]
            }],
            "max_tokens": 400
        }
        result = self._post(self.CHAT_URL, chat_payload, timeout=120)
        if isinstance(result, dict) and "choices" in result:
            return result["choices"][0]["message"]["content"]
        print(f"[HF] Vision query failed: {result}")
        return ""

    # ─────────────────────────────────────────────────────────────────────────
    # Feature extraction (for SHAP)
    # ─────────────────────────────────────────────────────────────────────────

    def feature_extraction(self, model: str, text: str) -> List[float]:
        url = f"{self.INFERENCE_URL}/{model}"
        result = self._post(url, {"inputs": text[:512]}, timeout=30)
        if isinstance(result, list) and len(result) > 0:
            first = result[0]
            if isinstance(first, list):
                return [sum(row[i] for row in first) / len(first) for i in range(len(first[0]))]
        return []

    # ─────────────────────────────────────────────────────────────────────────
    # JSON extraction helper
    # ─────────────────────────────────────────────────────────────────────────

    def extract_json(self, text: str) -> Dict:
        try:
            return json.loads(text)
        except Exception:
            pass
        for pat in [r'```json\s*([\s\S]*?)\s*```', r'```\s*(\{[\s\S]*?\})\s*```', r'(\{[\s\S]*?\})']:
            m = re.search(pat, text, re.DOTALL)
            if m:
                try:
                    return json.loads(m.group(1))
                except Exception:
                    continue
        return {}


_hf_client_instance: Optional["MediCascadeHFClient"] = None

def get_hf_client() -> "MediCascadeHFClient":
    """Lazy singleton — creates the client on first call, not at import time."""
    global _hf_client_instance
    if _hf_client_instance is None:
        _hf_client_instance = MediCascadeHFClient()
    return _hf_client_instance


class _LazyHFClient:
    """Transparent proxy so 'hf_client.generate_text(...)' works without eager init."""
    def __getattr__(self, name):
        return getattr(get_hf_client(), name)


hf_client = _LazyHFClient()
