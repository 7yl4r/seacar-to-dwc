"""Scaffolds datasets/<program_id>/'s three review write-ups: summary.md,
transform_notes.md, archive_summary.md -- for the three points in the
pipeline a human should sanity-check (raw data, the transform's choices,
and the final archive).

Each file is self-contained: its own front matter carries both the
`instructions` for what to write (steer these per dataset -- e.g. a program
with a known data-entry quirk can call that out explicitly) and the
`generated_by`/`reviewed`/`reviewed_by`/`reviewed_at` sign-off fields (see
reviewable_docs.py, which report/template.qmd and case_study.py both use to
surface `reviewed: false` -- or an undrafted file's missing `generated_by`
-- as a visible warning). Nobody has to go find a separate instructions
file to know what a write-up is supposed to say.

summary.md additionally carries the dataset's identity (`program_id`,
`habitat`, `description`) -- what used to live in a separate dataset.yaml.
It's the one file that has to exist before the pipeline can run for a given
id (`--all` discovers datasets by globbing datasets/*/summary.md and
reading `program_id` out of its front matter), so folding identity into it
means there's exactly one file to create to onboard a new dataset by hand.

This module only ever creates a file if it's missing -- it never overwrites
an existing summary.md/transform_notes.md/archive_summary.md, whether or
not it's been drafted yet, since a human may have customized its
instructions, identity fields, or already started writing.
"""
from __future__ import annotations

import json
from pathlib import Path

DEFAULT_SUMMARY_INSTRUCTIONS = """\
Fill in this file's body (below the front matter) with a short, plain-language
summary of this dataset's *raw* export, for a data manager who knows the field
program but hasn't seen this particular file. Ground it in
data/04_processed/<program_id>/raw_data_profile.json, which the pipeline
generates automatically (row/location/species counts, date range, QAQC flag
counts, and -- importantly -- any unresolved_species SpeciesIDs found in the
data but missing from Ref_Species, which is worth calling out explicitly
since the pipeline silently drops those rows).

Cover, briefly:
- what this dataset is and its rough size/shape
- the sampling date range and number of stations
- anything about the species/parameter mix worth flagging
- any data-quality oddities in the profile (unresolved SpeciesIDs, unusual
  QAQC flag rates, a duplicate-row count worth knowing about)

Keep it under ~200 words. Once drafted, set generated_by above (model/person
+ date); leave reviewed: false until a data manager has actually checked it
against the real data, then flip it to true with reviewed_by/reviewed_at."""

DEFAULT_TRANSFORM_INSTRUCTIONS = """\
Fill in this file's body with anything about *this dataset's* run through the
transform that a data manager should double check -- not the general
Event/Occurrence/eMoF mapping rules (those are standardized across every
dataset and documented once in report/mapping_reference.md), but choices
specific to this program's data.

Cover, briefly, using data/04_processed/<program_id>/raw_data_profile.json
and config/measurement_vocab.yaml:
- any ParameterID present in this dataset's parameter_counts that has no
  entry in measurement_vocab.yaml (falls back to the raw ParameterName/Units
  as-is -- worth a deliberate mapping instead)
- any non-taxon SpeciesID codes this dataset actually uses (aggregate rows
  like "Total seagrass" that become event-level facts, not Occurrences) and
  whether that's the right call for this program
- any unresolved_species (SpeciesIDs missing from Ref_Species entirely --
  silently dropped today; may indicate the reference workbook is stale)

Keep it under ~200 words. Once drafted, set generated_by above and leave
reviewed: false until a data manager signs off, same as summary.md."""

DEFAULT_ARCHIVE_SUMMARY_INSTRUCTIONS = """\
Fill in this file's body with a short write-up of the *output* Darwin Core
Archive itself, for a reviewer deciding whether it's ready to upload into
IPT. Ground it in data/04_processed/<program_id>/report_meta.json's
record_counts and data/05_archive/<program_id>/seacar-<program_id>-dwca.zip.

Cover, briefly:
- final event/occurrence/measurement counts, and whether that ratio looks
  sane given the raw data profile (e.g. wildly fewer occurrences than
  expected would suggest a taxonomy join problem)
- anything worth flagging about the archive as a deliverable: does the EML
  citation/contact info look right, does the date/bbox coverage match
  expectations, anything unusual noticed while spot-checking the CSVs in
  data/04_processed/<program_id>/

Keep it under ~150 words. Once drafted, set generated_by above and leave
reviewed: false until a data manager signs off, same as summary.md."""

_DEFAULTS = {
    "summary.md": DEFAULT_SUMMARY_INSTRUCTIONS,
    "transform_notes.md": DEFAULT_TRANSFORM_INSTRUCTIONS,
    "archive_summary.md": DEFAULT_ARCHIVE_SUMMARY_INSTRUCTIONS,
}


def _yaml_scalar(value) -> str:
    return "null" if value is None else json.dumps(value)  # JSON strings are valid YAML scalars


def _scaffold_text(instructions: str, identity: dict | None = None) -> str:
    lines = ["---"]
    for key, value in (identity or {}).items():
        lines.append(f"{key}: {_yaml_scalar(value)}")
    indented = "\n".join(f"  {line}" if line else "" for line in instructions.splitlines())
    lines += [
        "instructions: |-",
        indented,
        "generated_by: null",
        "reviewed: false",
        "reviewed_by: null",
        "reviewed_at: null",
        "---\n",
    ]
    return "\n".join(lines)


def ensure_dataset_docs(program_id: str, datasets_root: Path) -> Path:
    """Create datasets/<program_id>/ and its three write-ups (each with its
    own instructions in front matter, undrafted body) if they don't already
    exist. summary.md also gets its identity fields (program_id pre-filled;
    habitat/description left for a human to fill in). Returns that
    directory."""
    dataset_dir = datasets_root / str(program_id)
    dataset_dir.mkdir(parents=True, exist_ok=True)
    for filename, instructions in _DEFAULTS.items():
        path = dataset_dir / filename
        if path.exists():
            continue
        identity = {"program_id": str(program_id), "habitat": None, "description": None} if filename == "summary.md" else None
        path.write_text(_scaffold_text(instructions, identity))
    return dataset_dir
