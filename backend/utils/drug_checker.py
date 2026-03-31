"""
FDA OpenFDA drug interaction and safety checker.
Completely free — no API key required.
Checks each medication against FDA drug labels for interactions, warnings, and contraindications.
"""
import re
import threading
import time
from typing import Dict, List, Optional
from urllib.parse import urlencode

import requests

_DRUG_LABEL_URL = "https://api.fda.gov/drug/label.json"
_cache: Dict[str, Optional[Dict]] = {}
_fda_lock = threading.Semaphore(3)
_fda_call_times: List[float] = []
_fda_call_times_lock = threading.Lock()
_fda_rate_limit = 35
_FDA_UNAVAILABLE = {"status": "fda_unavailable", "note": "FDA data temporarily unavailable"}

# Dosage / route noise to strip before searching
_DOSAGE_RE = re.compile(
    r"\d+(\.\d+)?\s*(mg|mcg|g|ml|iu|units?|mmol)",
    re.IGNORECASE,
)
_ROUTE_RE = re.compile(
    r"\b(tablet|capsule|injection|intravenous|oral|topical|inhaled|extended.release|"
    r"er|xr|sr|sustained.release|once.daily|twice.daily|bid|tid|qd)\b",
    re.IGNORECASE,
)


def check_medications(medications: List[str]) -> Dict:
    """
    Check a list of medication names/strings against FDA drug labels.

    Returns:
        {
            "drug_info": [...],          # per-drug label info
            "interactions": [...],       # drugs with flagged interactions
            "warnings": [...],           # boxed / serious warnings
            "contraindications": [...],  # absolute contraindications
            "source": "OpenFDA"
        }
    """
    result: Dict = {
        "drug_info": [],
        "interactions": [],
        "warnings": [],
        "contraindications": [],
        "source": "FDA OpenFDA",
        "status": "ok",
    }
    fda_unavailable = False

    seen = set()
    for raw in medications[:8]:           # cap to avoid rate limiting
        name = _clean_name(raw)
        if not name or name.lower() in seen:
            continue
        seen.add(name.lower())

        info = _fetch_label(name)
        if info and info.get("status") == "fda_unavailable":
            fda_unavailable = True
            continue
        if not info:
            continue

        result["drug_info"].append(info)

        if info.get("interactions"):
            result["interactions"].append({
                "drug": name,
                "detail": info["interactions"][:400],
            })
        if info.get("warnings"):
            result["warnings"].append({
                "drug": name,
                "detail": info["warnings"][:400],
            })
        if info.get("contraindications"):
            result["contraindications"].append({
                "drug": name,
                "detail": info["contraindications"][:400],
            })

    if not result["drug_info"] and fda_unavailable:
        return {
            "warnings": [],
            "interactions": [],
            "contraindications": [],
            "drug_info": [],
            "source": "FDA OpenFDA",
            "status": "fda_unavailable",
            "note": "FDA data temporarily unavailable",
        }

    return result


def _clean_name(raw: str) -> str:
    name = _DOSAGE_RE.sub("", raw)
    name = _ROUTE_RE.sub("", name)
    # Strip parentheticals like "(Metformin)"
    name = re.sub(r"\(.*?\)", "", name)
    name = re.sub(r"\s+", " ", name).strip(" ,;.")
    return name


def _fetch_label(drug_name: str) -> Optional[Dict]:
    if drug_name in _cache:
        return _cache[drug_name]

    saw_unavailable = False

    # Try brand name first, then generic name
    for field in ("openfda.brand_name", "openfda.generic_name"):
        result = _query_fda(field, drug_name)
        if result and result.get("status") == "fda_unavailable":
            saw_unavailable = True
            continue
        if result:
            _cache[drug_name] = result
            return result

    if saw_unavailable:
        _cache[drug_name] = dict(_FDA_UNAVAILABLE)
        return _cache[drug_name]

    _cache[drug_name] = None
    return None


def _prune_fda_call_times(now: Optional[float] = None) -> List[float]:
    current = now or time.time()
    with _fda_call_times_lock:
        _fda_call_times[:] = [t for t in _fda_call_times if current - t < 60]
        return list(_fda_call_times)


def get_fda_rate_limit_remaining() -> int:
    """Approximate remaining requests in the current 60-second FDA window."""
    recent_calls = _prune_fda_call_times()
    return max(0, _fda_rate_limit - len(recent_calls))


def _rate_limited_fda_call(url: str) -> requests.Response:
    with _fda_lock:
        while True:
            now = time.time()
            with _fda_call_times_lock:
                _fda_call_times[:] = [t for t in _fda_call_times if now - t < 60]
                if len(_fda_call_times) < _fda_rate_limit:
                    _fda_call_times.append(now)
                    break
                sleep_time = 60 - (now - _fda_call_times[0])
            if sleep_time > 0:
                time.sleep(sleep_time)

        return requests.get(url, timeout=10)


def _query_fda(field: str, drug_name: str) -> Optional[Dict]:
    query = urlencode(
        {
            "search": f'{field}:"{drug_name}"',
            "limit": 1,
        }
    )
    url = f"{_DRUG_LABEL_URL}?{query}"
    backoff_delays = [1, 2, 4]

    for attempt in range(len(backoff_delays) + 1):
        try:
            resp = _rate_limited_fda_call(url)
            if resp.status_code == 404:
                return None
            if resp.status_code == 429:
                raise requests.HTTPError("429 Too Many Requests", response=resp)
            resp.raise_for_status()
            results = resp.json().get("results", [])
            if not results:
                return None

            r = results[0]

            def pick(keys: List[str]) -> str:
                for k in keys:
                    val = r.get(k)
                    if val and isinstance(val, list) and val[0]:
                        return val[0][:600]
                    if val and isinstance(val, str):
                        return val[:600]
                return ""

            return {
                "drug": drug_name,
                "brand_names": r.get("openfda", {}).get("brand_name", [])[:3],
                "generic_names": r.get("openfda", {}).get("generic_name", [])[:3],
                "interactions": pick(["drug_interactions", "drug_and_or_laboratory_test_interactions"]),
                "warnings": pick(["boxed_warning", "warnings", "warnings_and_cautions"]),
                "contraindications": pick(["contraindications"]),
                "indications": pick(["indications_and_usage"])[:300],
            }

        except Exception as e:
            if attempt < len(backoff_delays):
                time.sleep(backoff_delays[attempt])
                continue
            print(f"[FDA] Query failed for '{drug_name}': {e}")
            return dict(_FDA_UNAVAILABLE)

    return dict(_FDA_UNAVAILABLE)
