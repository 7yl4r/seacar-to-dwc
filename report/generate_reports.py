#!/usr/bin/env python3
"""Pre-render step (see _quarto.yml): emits reports/<program_id>.qmd for every
dataset the pipeline has processed, by filling in template.qmd's placeholders.

Mirrors the batch-generation pattern in https://github.com/7yl4r/quartobatch
(a template + a generate script that stamps out one .qmd per item, plus a
listing.qmd that lists them) -- reimplemented in Python, matching the rest of
this pipeline, instead of quartobatch's R/whisker version.
"""
from __future__ import annotations

import json
import shutil
from datetime import date
from pathlib import Path

REPORT_DIR = Path(__file__).resolve().parent
REPO_ROOT = REPORT_DIR.parent
DATA_ROOT = REPO_ROOT / "data"
TEMPLATE_PATH = REPORT_DIR / "template.qmd"
REPORTS_DIR = REPORT_DIR / "reports"
DOWNLOADS_DIR = REPORTS_DIR / "downloads"


def _processed_program_ids() -> list[str]:
    processed_root = DATA_ROOT / "04_processed"
    if not processed_root.exists():
        return []
    return sorted(
        p.name for p in processed_root.iterdir()
        if (p / "report_meta.json").exists()
    )


def generate() -> None:
    if REPORTS_DIR.exists():
        shutil.rmtree(REPORTS_DIR)
    REPORTS_DIR.mkdir(parents=True)

    template_text = TEMPLATE_PATH.read_text()
    today = date.today().isoformat()
    program_ids = _processed_program_ids()

    for program_id in program_ids:
        processed_dir = DATA_ROOT / "04_processed" / program_id
        meta = json.loads((processed_dir / "report_meta.json").read_text())

        zip_src = DATA_ROOT / "05_archive" / program_id / meta["archive_filename"]
        if not zip_src.exists():
            print(f"skipping {program_id}: no archive at {zip_src}")
            continue
        zip_dst_dir = DOWNLOADS_DIR / program_id
        zip_dst_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(zip_src, zip_dst_dir / zip_src.name)

        description = meta.get("habitat") or meta["title"]
        rendered = (
            template_text
            .replace("__PROGRAM_ID__", program_id)
            .replace("__TITLE__", meta["title"].replace('"', '\\"'))
            .replace("__DESCRIPTION__", description.replace('"', '\\"'))
            .replace("__DATE__", today)
        )
        (REPORTS_DIR / f"{program_id}.qmd").write_text(rendered)
        print(f"generated reports/{program_id}.qmd")

    if not program_ids:
        print("no processed datasets found under data/04_processed -- run the pipeline first")


if __name__ == "__main__":
    generate()
