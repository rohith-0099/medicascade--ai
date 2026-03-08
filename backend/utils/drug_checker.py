"""
FDA OpenFDA drug interaction and safety checker.
Completely free — no API key required.
Checks each medication against FDA drug labels for interactions, warnings, and contraindications.
"""
import re
import time
from typing import Dict, List, Optional

import requests

_DRUG_LABEL_URL = "https://api.fda.gov/drug/label.json"
_cache: Dict[str, Optional[Dict]] = {}

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
    }

    seen = set()
    for raw in medications[:8]:           # cap to avoid rate limiting
        name = _clean_name(raw)
        if not name or name.lower() in seen:
            continue
        seen.add(name.lower())

        info = _fetch_label(name)
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

        time.sleep(0.2)   # OpenFDA rate limit

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

    # Try brand name first, then generic name
    for field in ("openfda.brand_name", "openfda.generic_name"):
        result = _query_fda(field, drug_name)
        if result:
            _cache[drug_name] = result
            return result

    _cache[drug_name] = None
    return None


def _query_fda(field: str, drug_name: str) -> Optional[Dict]:
    try:
        resp = requests.get(
            _DRUG_LABEL_URL,
            params={
                "search": f'{field}:"{drug_name}"',
                "limit": 1,
            },
            timeout=8,
        )
        if resp.status_code == 404:
            return None
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
        print(f"[FDA] Query failed for '{drug_name}': {e}")
        return None
