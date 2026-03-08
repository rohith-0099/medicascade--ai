"""
Real PubMed evidence fetching via NIH eUtils.
Completely free — no API key required (rate-limited to 3 req/sec without key).
Fetches actual titles + abstracts instead of placeholder links.
"""
import time
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional

import requests

_ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
_EFETCH  = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

# Simple in-process cache so repeated pipeline runs don't hammer NIH
_cache: Dict[str, List[Dict]] = {}


def get_evidence_for_diagnosis(diagnosis: str, max_results: int = 3) -> List[Dict]:
    """
    Search PubMed for a diagnosis and return real abstracts.
    Returns a list of dicts: {pmid, title, abstract, year, journal, url, snippet}
    """
    if not diagnosis or len(diagnosis) < 4:
        return []

    cache_key = f"{diagnosis.lower()}:{max_results}"
    if cache_key in _cache:
        return _cache[cache_key]

    pmids = _search(diagnosis, max_results)
    if not pmids:
        _cache[cache_key] = []
        return []

    # Respect NIH rate limit: 3 requests/sec without API key
    time.sleep(0.35)
    articles = _fetch_abstracts(pmids)
    _cache[cache_key] = articles
    return articles


def _search(query: str, max_results: int) -> List[str]:
    # Use title/abstract + clinical filter for relevance
    focused = f'({query}[Title/Abstract]) AND (clinical[Title/Abstract] OR diagnosis[Title/Abstract] OR treatment[Title/Abstract])'
    try:
        resp = requests.get(
            _ESEARCH,
            params={
                "db": "pubmed",
                "term": focused,
                "retmax": max_results,
                "retmode": "json",
                "sort": "relevance",
            },
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get("esearchresult", {}).get("idlist", [])
    except Exception as e:
        print(f"[PubMed] Search failed for '{query}': {e}")
        return []


def _fetch_abstracts(pmids: List[str]) -> List[Dict]:
    if not pmids:
        return []
    try:
        resp = requests.get(
            _EFETCH,
            params={
                "db": "pubmed",
                "id": ",".join(pmids),
                "retmode": "xml",
                "rettype": "abstract",
            },
            timeout=15,
        )
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
    except Exception as e:
        print(f"[PubMed] Fetch failed: {e}")
        return []

    articles = []
    for article in root.findall(".//PubmedArticle"):
        pmid   = _text(article, ".//PMID")
        title  = _text(article, ".//ArticleTitle") or "No title"
        year   = _text(article, ".//PubDate/Year") or _text(article, ".//PubDate/MedlineDate", default="")
        journal = _text(article, ".//Journal/Title") or ""

        # Abstract may be structured (multiple AbstractText labels)
        abstract_parts = article.findall(".//AbstractText")
        if abstract_parts:
            abstract = " ".join(
                (el.get("Label", "") + ": " if el.get("Label") else "") + (el.text or "")
                for el in abstract_parts
            ).strip()
        else:
            abstract = "Abstract not available."

        snippet = abstract[:300].rstrip() + ("…" if len(abstract) > 300 else "")

        articles.append({
            "pmid":    pmid,
            "title":   title,
            "abstract": abstract[:1000],
            "snippet": snippet,
            "year":    year,
            "journal": journal,
            "url":     f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            "source":  "PubMed",
        })

    return articles


def _text(element, xpath: str, default: str = "") -> str:
    el = element.find(xpath)
    return (el.text or default) if el is not None else default
