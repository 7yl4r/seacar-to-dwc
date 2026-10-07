"""Assembles datasets/<program_id>/README.md -- the one portable file for a
dataset's whole conversion: raw data, transformation, human review, and the
final archive, in that order, with the same section headers for every
dataset so they stay comparable to each other and usable as a worked
example when onboarding the next one. Named README.md (not case_study.md)
on purpose -- GitHub and most file browsers render it automatically when
you open datasets/<id>/, so there's nothing to hunt for.

Generated fresh at the end of every pipeline run (pipeline.py); never
hand-edited -- the content a human actually edits lives in summary.md,
transform_notes.md, and archive_summary.md, which this just weaves together
with the deterministic facts (report_meta.json, raw_data_profile.json).
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .reviewable_docs import read_reviewable_doc, review_badge

_WRITEUPS = ["summary", "transform_notes", "archive_summary"]


def _markdown_table(rows: list[dict]) -> str:
    if not rows:
        return "_(none)_"
    headers = list(rows[0].keys())
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row[h]) if row[h] is not None else "" for h in headers) + " |")
    return "\n".join(lines)


def _applied_vocab_table(raw_profile: dict, vocab: dict) -> str:
    entries = sorted(raw_profile["parameter_counts"].items(), key=lambda kv: kv[1], reverse=True)
    rows = []
    for parameter_id, count in entries:
        cfg = vocab.get(parameter_id)
        rows.append({
            "ParameterID": parameter_id,
            "rows": f"{count:,}",
            "role": cfg["role"] if cfg else "UNMAPPED (raw ParameterName/Units used as-is)",
            "measurementType / status parameter": (cfg.get("measurementType") or cfg.get("parameter_name")) if cfg else "",
        })
    return _markdown_table(rows)


def _sign_off_table(dataset_dir: Path) -> str:
    rows = []
    for name in _WRITEUPS:
        front_matter, _ = read_reviewable_doc(dataset_dir / f"{name}.md")
        rows.append({
            "Write-up": f"{name}.md",
            "Reviewed": "yes" if front_matter.get("reviewed") else "no",
            "By": front_matter.get("reviewed_by") or "",
            "When": front_matter.get("reviewed_at") or "",
        })
    return _markdown_table(rows)


def _overall_reviewed(dataset_dir: Path) -> bool:
    return all(read_reviewable_doc(dataset_dir / f"{name}.md")[0].get("reviewed") for name in _WRITEUPS)


def assemble_case_study(
    program_id: str,
    dataset_dir: Path,
    report_meta: dict,
    raw_profile: dict,
    vocab: dict,
    mapping_reference_text: str,
) -> str:
    summary_fm, summary_body = read_reviewable_doc(dataset_dir / "summary.md")
    transform_fm, transform_body = read_reviewable_doc(dataset_dir / "transform_notes.md")
    archive_fm, archive_body = read_reviewable_doc(dataset_dir / "archive_summary.md")

    counts = report_meta["record_counts"]
    lines = [
        "---",
        f'program_id: "{program_id}"',
        f'title: "{report_meta["title"]}"',
        f'generated_at: "{datetime.now(timezone.utc):%Y-%m-%d}"',
        f"reviewed: {str(_overall_reviewed(dataset_dir)).lower()}",
        "---",
        "",
        f"# Case study: {program_id} -- {report_meta['title']}",
        "",
        f"**Organization:** {report_meta['organization']}",
        "",
    ]
    if report_meta["managed_areas"]:
        lines += [f"**Managed area(s):** {', '.join(report_meta['managed_areas'])}", ""]
    lines += [f"**Source:** {report_meta['source_url']}", ""]
    if report_meta["citation"]:
        lines += [f"> {report_meta['citation']}", ""]

    lines += ["## Raw Data", "", review_badge(summary_fm), ""]
    lines += [summary_body or "_(nothing drafted yet)_", ""]
    lines += ["### Raw data profile", ""]
    lines += [
        f"- **{raw_profile['row_count']:,}** raw rows, **{raw_profile['n_program_locations']}** stations, "
        f"**{raw_profile['n_species_ids']}** distinct SpeciesIDs",
        f"- sample dates: {raw_profile['sample_date_range']['start']} to {raw_profile['sample_date_range']['end']}",
        "- QAQC flags: " + ", ".join(f"`{k}` ({v:,})" for k, v in raw_profile["qaqc_flag_counts"].items()),
        "",
    ]
    if raw_profile["unresolved_species"]:
        ids = ", ".join(f"{s['species_id']} ({s['common_identifier']})" for s in raw_profile["unresolved_species"])
        lines += [f"> ⚠️ **{len(raw_profile['unresolved_species'])} SpeciesID(s) missing from Ref_Species entirely**, "
                   f"silently excluded from Occurrence: {ids}", ""]
    if raw_profile["non_taxon_species"]:
        ids = ", ".join(f"{s['species_id']} ({s['common_identifier']})" for s in raw_profile["non_taxon_species"])
        lines += [f"- non-taxon placeholder codes present: {ids}", ""]

    lines += ["## Transformation", "", mapping_reference_text.strip(), "", "### Applied to this dataset", ""]
    lines += [_applied_vocab_table(raw_profile, vocab), ""]
    lines += [review_badge(transform_fm), ""]
    lines += [transform_body or "_(nothing drafted yet)_", ""]

    lines += ["## Final Darwin Core Archive", "", review_badge(archive_fm), ""]
    lines += [archive_body or "_(nothing drafted yet)_", ""]
    lines += [
        f"- **{counts['events']:,}** events, **{counts['occurrences']:,}** occurrences, "
        f"**{counts['measurementOrFacts']:,}** measurements",
        f"- archive file: `{report_meta['archive_filename']}`",
        "",
    ]

    lines += ["## Human Review & Sign-off", "", _sign_off_table(dataset_dir), ""]

    return "\n".join(lines)
