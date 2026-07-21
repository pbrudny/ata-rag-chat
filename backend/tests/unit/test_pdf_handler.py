import sys
import types
from pathlib import Path

import pytest

from app.crawler.pdf_handler import extract_pdf_text

FAKE_ANALYSIS_MARKDOWN = """\
# PDF Analysis

## Summary
This document is about admissions requirements.

## Key Facts
- Deadline: September 30

## Full Extracted Text

Wymagane dokumenty do rekrutacji:
1. Dowod osobisty
2. Swiadectwo maturalne

## Agent Notes

Some internal note that should not be included.
"""


@pytest.fixture()
def fake_pdf_to_md(tmp_path, monkeypatch):
    md_path = tmp_path / "output.md"
    md_path.write_text(FAKE_ANALYSIS_MARKDOWN, encoding="utf-8")

    fake_module = types.ModuleType("pdf_to_md")
    fake_module.analyze_pdf = lambda pdf_path, output_path=None: md_path
    monkeypatch.setitem(sys.modules, "pdf_to_md", fake_module)
    return md_path


def test_extracts_only_full_text_section(fake_pdf_to_md):
    result = extract_pdf_text(Path("dummy.pdf"))
    assert "Wymagane dokumenty" in result
    assert "Dowod osobisty" in result


def test_excludes_summary_and_key_facts(fake_pdf_to_md):
    result = extract_pdf_text(Path("dummy.pdf"))
    assert "Summary" not in result
    assert "admissions requirements" not in result
    assert "Deadline" not in result


def test_excludes_trailing_sections(fake_pdf_to_md):
    result = extract_pdf_text(Path("dummy.pdf"))
    assert "Agent Notes" not in result
    assert "internal note" not in result


def test_raises_clear_error_when_pdf_to_md_not_installed(monkeypatch):
    monkeypatch.setitem(sys.modules, "pdf_to_md", None)
    with pytest.raises(RuntimeError, match="pdf_to_md is not installed"):
        extract_pdf_text(Path("dummy.pdf"))
