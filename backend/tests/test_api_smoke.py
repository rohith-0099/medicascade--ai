"""Smoke tests for the FastAPI app.

Importing ``main`` pulls the full pipeline (pdfplumber, spaCy, ReportLab …).
Where those heavy dependencies are not installed (e.g. a lean CI lane), the
whole module is skipped rather than failing collection.
"""
import pytest

pytest.importorskip("fastapi")
main = pytest.importorskip("main", reason="pipeline dependencies not installed")
from fastapi.testclient import TestClient  # noqa: E402

client = TestClient(main.app)


def test_health_endpoint_ok():
    response = client.get("/health")
    assert response.status_code == 200


def test_root_endpoint_responds():
    response = client.get("/")
    assert response.status_code == 200


def test_diagnose_rejects_non_pdf():
    response = client.post(
        "/api/diagnose",
        files={"file": ("note.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 400
