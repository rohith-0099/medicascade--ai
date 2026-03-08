"""
SQLite case persistence for MediCascade.
Stores every processed case so clinicians can review history,
track longitudinal outcomes, and submit feedback.
No external dependencies — built-in Python sqlite3.
"""
import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

_DB_PATH: str = os.environ.get("DB_PATH", "outputs/medicascade.db")


def _conn() -> sqlite3.Connection:
    Path(_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(_DB_PATH, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


def init_db() -> None:
    """Create tables if they don't exist. Call once at startup."""
    with _conn() as con:
        con.executescript("""
            CREATE TABLE IF NOT EXISTS cases (
                case_id            TEXT PRIMARY KEY,
                source_pdf         TEXT,
                ingested_at        TEXT,
                primary_diagnosis  TEXT,
                icd10_code         TEXT,
                icd10_description  TEXT,
                confidence         REAL,
                processing_time    REAL,
                pdf_path           TEXT,
                layer1_json        TEXT,
                layer2_json        TEXT,
                drug_warnings      TEXT,
                created_at         TEXT DEFAULT (datetime('now'))
            );

            CREATE INDEX IF NOT EXISTS idx_cases_created
                ON cases(created_at);

            CREATE TABLE IF NOT EXISTS feedback (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id    TEXT NOT NULL,
                rating     INTEGER CHECK(rating BETWEEN 1 AND 5),
                comment    TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (case_id) REFERENCES cases(case_id)
            );

            CREATE TABLE IF NOT EXISTS audit_log (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id    TEXT,
                event      TEXT,
                detail     TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );
        """)


def save_case(
    *,
    case_id: str,
    source_pdf: str,
    ingested_at: str,
    primary_diagnosis: str,
    icd10_code: str = "R69",
    icd10_description: str = "Illness, unspecified",
    confidence: float = 0.0,
    processing_time: float = 0.0,
    pdf_path: str = "",
    layer1_findings: Optional[dict] = None,
    layer2_assessment: Optional[dict] = None,
    drug_warnings: Optional[list] = None,
) -> None:
    with _conn() as con:
        con.execute(
            """
            INSERT OR REPLACE INTO cases
                (case_id, source_pdf, ingested_at, primary_diagnosis,
                 icd10_code, icd10_description, confidence, processing_time,
                 pdf_path, layer1_json, layer2_json, drug_warnings)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                case_id, source_pdf, str(ingested_at), primary_diagnosis,
                icd10_code, icd10_description, confidence, processing_time,
                pdf_path,
                json.dumps(layer1_findings) if layer1_findings else None,
                json.dumps(layer2_assessment) if layer2_assessment else None,
                json.dumps(drug_warnings) if drug_warnings else None,
            ),
        )
        con.execute(
            "INSERT INTO audit_log (case_id, event) VALUES (?,?)",
            (case_id, "case_saved"),
        )


def get_case_history(limit: int = 20, offset: int = 0) -> List[Dict]:
    with _conn() as con:
        rows = con.execute(
            "SELECT * FROM cases ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
    return [dict(r) for r in rows]


def get_case(case_id: str) -> Optional[Dict]:
    with _conn() as con:
        row = con.execute(
            "SELECT * FROM cases WHERE case_id = ?", (case_id,)
        ).fetchone()
    return dict(row) if row else None


def get_stats() -> Dict:
    with _conn() as con:
        total    = con.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
        avg_conf = con.execute("SELECT AVG(confidence) FROM cases").fetchone()[0]
        avg_time = con.execute("SELECT AVG(processing_time) FROM cases").fetchone()[0]
        top_diag = con.execute(
            "SELECT primary_diagnosis, COUNT(*) as n FROM cases "
            "GROUP BY primary_diagnosis ORDER BY n DESC LIMIT 5"
        ).fetchall()
    return {
        "total_cases": total,
        "avg_confidence": round(avg_conf or 0, 3),
        "avg_processing_time_s": round(avg_time or 0, 1),
        "top_diagnoses": [{"diagnosis": r[0], "count": r[1]} for r in top_diag],
    }


def save_feedback(case_id: str, rating: int, comment: str = "") -> None:
    with _conn() as con:
        con.execute(
            "INSERT INTO feedback (case_id, rating, comment) VALUES (?,?,?)",
            (case_id, max(1, min(5, rating)), comment),
        )
        con.execute(
            "INSERT INTO audit_log (case_id, event, detail) VALUES (?,?,?)",
            (case_id, "feedback_submitted", f"rating={rating}"),
        )


def get_feedback(case_id: str) -> List[Dict]:
    with _conn() as con:
        rows = con.execute(
            "SELECT rating, comment, created_at FROM feedback WHERE case_id = ? ORDER BY created_at",
            (case_id,),
        ).fetchall()
    return [dict(r) for r in rows]
