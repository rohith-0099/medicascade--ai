"""
Notes Analyzer — Specialist 2 (alias)
Model: UFNLP/gatortron-medium

This module re-exports NotesAnalyzer and notes_analyzer from symptom_analyzer,
which provides the full GatorTron-based clinical NLP implementation.
Kept for backward-compatibility with any imports of specialists.notes_analyzer.
"""

from specialists.symptom_analyzer import NotesAnalyzer, notes_analyzer

__all__ = ["NotesAnalyzer", "notes_analyzer"]
