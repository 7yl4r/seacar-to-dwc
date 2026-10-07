"""Read/render a human-editable, AI-drafted write-up (summary.md,
transform_notes.md, archive_summary.md -- see docs_scaffold.py).

Each of these files starts with a standard top-of-file YAML front matter
block (`instructions`/`generated_by`/`reviewed`/`reviewed_by`/`reviewed_at`)
followed by free-text markdown -- the instructions for what to write live
*in the file itself*, not in a separate sibling file, so a newcomer opening
datasets/<id>/ only ever sees the files they actually need to read or edit.
This module is the one place that convention is parsed, shared by
report/template.qmd (via quarto's jupyter engine, which imports this
installed package) and case_study.py, so there's exactly one implementation
rather than two copies drifting apart.
"""
from __future__ import annotations

from pathlib import Path

import yaml


def read_reviewable_doc(path: Path) -> tuple[dict, str]:
    """Split a write-up into (front matter, body). Returns ({}, "") if the
    file doesn't exist yet."""
    if not path.exists():
        return {}, ""
    text = path.read_text()
    parts = text.split("---\n", 2) if text.startswith("---\n") else [text]
    if len(parts) != 3:
        return {}, text  # malformed front matter -- show the raw file rather than crash
    _, fm_text, body = parts
    return yaml.safe_load(fm_text) or {}, body.strip()


def review_badge(front_matter: dict) -> str:
    if not front_matter.get("generated_by"):
        return (
            "> ⚠️ **Not yet drafted.** See this file's `instructions` front-matter "
            "field for what to cover, grounded in the profile data below."
        )
    if front_matter.get("reviewed"):
        return f"> ✅ Reviewed by {front_matter.get('reviewed_by')} on {front_matter.get('reviewed_at')}."
    return (
        f"> ⚠️ **Not yet reviewed by a data manager.** Drafted by "
        f"{front_matter.get('generated_by')}; flip `reviewed: true` "
        "in the front matter once checked."
    )
