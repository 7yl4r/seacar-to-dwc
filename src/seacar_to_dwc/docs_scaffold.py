"""Scaffolds the per-dataset review docs under config/datasets/<program_id>/.

Two kinds of file live there, for each of the two points in the pipeline a
human should sanity-check (raw data, and the transform's choices):

  <step>.instructions.md   Human-editable prompt: what a reviewer (or an AI
                            drafting on their behalf) should look for and say
                            about *this* dataset. Customize per dataset --
                            e.g. a program with a known data-entry quirk can
                            have its instructions call that out explicitly.
  <step>.md                The actual write-up: front matter tracks who
                            drafted it and whether a data manager has signed
                            off (see report/template.qmd, which surfaces
                            `reviewed: false` as a visible warning).

This module only ever creates the `.instructions.md` files, and only if
they're missing -- never `<step>.md` (that has to be actually written, by a
human or by an AI reading the instructions + data/04_processed/<id>/
raw_data_profile.json) and never overwrites an existing `.instructions.md`
(a human may have customized it).
"""
from __future__ import annotations

from pathlib import Path

DEFAULT_SUMMARY_INSTRUCTIONS = """\
# Instructions: raw data summary

Draft `summary.md` (in this same folder) as a short, plain-language summary
of this dataset's *raw* export for a data manager who knows the field
program but hasn't seen this particular file. Ground it in
`data/04_processed/<program_id>/raw_data_profile.json`, which the pipeline
generates automatically (row/location/species counts, date range, QAQC flag
counts, and -- importantly -- any `unresolved_species` SpeciesIDs found in
the data but missing from Ref_Species, which is worth calling out
explicitly since the pipeline silently drops those rows).

Cover, briefly:
- what this dataset is and its rough size/shape
- the sampling date range and number of stations
- anything about the species/parameter mix worth flagging
- any data-quality oddities in the profile (unresolved SpeciesIDs, unusual
  QAQC flag rates, a duplicate-row count worth knowing about)

Keep it under ~200 words. Start `summary.md` with this front matter (standard
top-of-file YAML, delimited by `---` lines), then the write-up below it:

    ---
    generated_by: "<model/person>, <date>"
    reviewed: false
    reviewed_by: null
    reviewed_at: null
    ---

and flip `reviewed` to `true` (with your name and date) once you've checked
it against the real data.
"""

DEFAULT_TRANSFORM_INSTRUCTIONS = """\
# Instructions: transformation review notes

Draft `transform_notes.md` (in this same folder) to flag anything about
*this dataset's* run through the transform that a data manager should
double check -- not the general Event/Occurrence/eMoF mapping rules (those
are standardized across every dataset and documented once in
report/mapping_reference.md), but choices specific to this program's data.

Cover, briefly, using `data/04_processed/<program_id>/raw_data_profile.json`
and `config/measurement_vocab.yaml`:
- any ParameterID present in this dataset's `parameter_counts` that has no
  entry in measurement_vocab.yaml (falls back to the raw ParameterName/Units
  as-is -- worth a deliberate mapping instead)
- any non-taxon SpeciesID codes this dataset actually uses (aggregate rows
  like "Total seagrass" that become event-level facts, not Occurrences) and
  whether that's the right call for this program
- any `unresolved_species` (SpeciesIDs missing from Ref_Species entirely --
  silently dropped today; may indicate the reference workbook is stale)

Keep it under ~200 words. Start `transform_notes.md` with the same
top-of-file front matter convention as summary.md (`generated_by` /
`reviewed` / `reviewed_by` / `reviewed_at`).
"""

_INSTRUCTION_FILES = {
    "summary.instructions.md": DEFAULT_SUMMARY_INSTRUCTIONS,
    "transform_notes.instructions.md": DEFAULT_TRANSFORM_INSTRUCTIONS,
}


def ensure_dataset_docs(program_id: str, config_root: Path) -> Path:
    """Create config/datasets/<program_id>/ and its default *.instructions.md
    files if they don't already exist. Returns that directory. Never touches
    summary.md/transform_notes.md or an already-present instructions file."""
    dataset_dir = config_root / "datasets" / str(program_id)
    dataset_dir.mkdir(parents=True, exist_ok=True)
    for filename, default_text in _INSTRUCTION_FILES.items():
        path = dataset_dir / filename
        if not path.exists():
            path.write_text(default_text)
    return dataset_dir
