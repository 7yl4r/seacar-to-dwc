# seacar-to-dwc

Converts FL SEACAR program exports (e.g. https://data.florida-seacar.org/programs/details/570)
into a Darwin Core Archive: **Event core + Occurrence extension + MeasurementOrFact extension**,
ready to upload into IPT.

## Quick start

Onboarding one dataset looks like this (see "Pipeline structure" and "Documentation structure"
below for the full picture and why it's shaped this way):

1. **Place your dataset.** Copy the template: `cp -r datasets/_template datasets/<program_id>`
   (e.g. `datasets/570`). For a SEACAR program there's nothing else to place -- the pipeline
   fetches the export automatically from the id alone.
2. **Create `summary.md` from the template.** In `datasets/<program_id>/summary.md`'s front
   matter, set `program_id` to your actual id (required -- it's how the pipeline knows what to
   run) and `habitat`/`description` if you know them (optional, descriptive only). Leave the
   rest of the file alone for now.
3. **Run your preferred AI assistant** (Claude Code or similar) with a prompt like:

   > Run the seacar-to-dwc pipeline for program `<program_id>`
   > (`python -m seacar_to_dwc.pipeline <program_id>`), then draft the body of
   > `datasets/<program_id>/summary.md` and `transform_notes.md`, following each file's own
   > `instructions` front-matter field and the `raw_data_profile.json` the run just produced.

   This fetches and transforms the data deterministically, and drafts both write-ups
   (`generated_by` set, `reviewed: false`).
4. **Review `transform_notes.md`** (and `summary.md`) against what you actually know about the
   dataset. Open `datasets/<program_id>/README.md` to see everything together -- including
   anything the pipeline itself flagged (`unresolved_species`, `unmapped_parameters`). Edit the
   write-ups directly, or edit `config/measurement_vocab.yaml`/`transform/*.py` if something
   needs an actual code fix.
5. **Run your preferred AI assistant again** with a prompt like:

   > I've edited `datasets/<program_id>/transform_notes.md` (and/or `measurement_vocab.yaml`).
   > Apply any changes it implies, re-run `python -m seacar_to_dwc.pipeline <program_id>` to
   > rebuild the archive and `datasets/<program_id>/README.md`, and confirm
   > `transform_notes.md`'s concerns are resolved.

   Repeat 4-5 until it looks right, then flip `reviewed: true` on each write-up. The archive at
   `data/05_archive/<program_id>/seacar-<program_id>-dwca.zip` is then ready for IPT.

## Install

```
pip install -e ".[dev]"
```

## Run

```
python -m seacar_to_dwc.pipeline 570          # one program
python -m seacar_to_dwc.pipeline --all        # every dataset under datasets/*/summary.md
```

Output: `data/05_archive/<program_id>/seacar-<program_id>-dwca.zip`. Each run also writes
`data/04_processed/<program_id>/{report_meta.json,raw_data_profile.json}`, scaffolds
`datasets/<program_id>/{summary,transform_notes,archive_summary}.md` the first time it processes
a program, and (re)generates `datasets/<program_id>/README.md` -- see "Documentation structure"
below.

## Pipeline structure

The goal isn't just "convert program 570" -- it's a repeatable, human-supervised process for
turning any siloed seagrass monitoring dataset into a Darwin Core Archive, where every
AI-drafted step gets reviewed by someone who knows the data before it's trusted. Concretely,
onboarding a dataset (new or re-run) goes through these stages, looping back to step 3 as often
as needed:

1. **Describe the dataset.** Copy `datasets/_template/` to `datasets/<program_id>/` and set
   `program_id` (required) / `habitat` / `description` (optional) in `summary.md`'s front matter
   -- or skip this and let step 2 scaffold it automatically with `program_id` pre-filled.
2. **Run the pipeline.** `python -m seacar_to_dwc.pipeline <program_id>`. This discovers the
   program page, downloads and parses the export, resolves taxonomy/WoRMS, writes the
   Event/Occurrence/eMoF CSVs and the DwC-A zip, writes the deterministic
   `report_meta.json`/`raw_data_profile.json` facts, and -- the first time -- scaffolds
   `datasets/<program_id>/{summary,transform_notes,archive_summary}.md`, each carrying its own
   drafting instructions in its front matter (see "Documentation structure" below).
3. **AI drafts the write-ups.** Using each file's own `instructions` field plus
   `raw_data_profile.json`/`report_meta.json`, fill in the body of `summary.md` (about the raw
   data), `transform_notes.md` (about the transform's choices for this dataset), and
   `archive_summary.md` (about the resulting archive) -- by hand, or by handing an AI assistant
   the file + the profile JSON and asking it to draft the body. Deliberately not something
   `pipeline.py` calls an LLM API for automatically, so the pipeline itself stays deterministic,
   offline, and free to run in CI. Set `generated_by`; leave `reviewed: false`.
4. **Human reviews.** Read `datasets/<program_id>/README.md` (plain markdown, no build step,
   and what GitHub/most file browsers show automatically when you open the folder) or
   `cd report && quarto render` for the same content with charts. Check the raw data profile
   for anything flagged (`unresolved_species`, `unmapped_parameters`), the "applied to this
   dataset" mapping table, and the species/measurement tables and validation charts against what
   you know about the program.
5. **Make changes based on what turns up.** Typically one of: add an unmapped `ParameterID` to
   `config/measurement_vocab.yaml`; note a data-quality flag in `transform_notes.md`, or fix the
   underlying handling in `transform/*.py` if it's a real bug rather than a documented quirk;
   edit a write-up's own `instructions` field if the default missed something specific to this
   program; or just fix wording in a write-up's body directly.
6. **Repeat 3-5**, re-running step 2 whenever a change upstream of the transform
   (`measurement_vocab.yaml`, `transform/*.py`) needs re-applying, until the README and archive
   both look right.
7. **Sign off.** Once a data manager has actually checked a write-up against the real data, flip
   `reviewed: true` (with `reviewed_by`/`reviewed_at`) -- that clears its ⚠️ banner. Once all
   three write-ups for a dataset are `reviewed: true`, its archive is ready to upload into IPT.

Every write-up (`summary.md`, `transform_notes.md`, `archive_summary.md`) starts with the same
front-matter shape, parsed by `seacar_to_dwc.reviewable_docs` (used by both `case_study.py` and
the quarto report, so there's one implementation of "what does reviewed mean" rather than two):

```yaml
---
instructions: |-
  What this write-up should cover, specific to this dataset -- edit this
  directly if the default missed something.
generated_by: null     # "<model/person>, <date>" once drafted
reviewed: false
reviewed_by: null
reviewed_at: null
---
```

## Documentation structure

Each dataset's conversion is documented under `datasets/<program_id>/` -- four files, each with
one obvious job, so the folder is approachable to someone who's never seen this pipeline before:

```
datasets/570/
  summary.md             # editable write-up -- raw data, PLUS this dataset's identity
                          #   (program_id/habitat/description) in its own front matter
  transform_notes.md     # editable write-up -- the transform's choices for this dataset
  archive_summary.md     # editable write-up -- the final archive
  README.md              # generated -- assembles everything above into one file; open this first
```

That's the four things a dataset's conversion should be judged by -- raw data, transformation,
human input, and the final archive -- as plain markdown, comparable across datasets and useful
to hand an AI as a worked example when onboarding the next one. There's no separate
`dataset.yaml` or `*.instructions.md` file to go find: `summary.md`'s front matter carries this
dataset's identity (what used to live in `dataset.yaml` -- `--all` discovers datasets by
globbing `datasets/*/summary.md` and reading `program_id` out of it) and every write-up's own
`instructions` field says what it should cover, right where you're already looking.
`datasets/_template/` is a ready-to-copy starting point for a new one (see "Quick start" above).

`README.md` (built by `case_study.py` at the end of every pipeline run -- never hand-edited, and
named `README.md` on purpose so it's what GitHub/most file browsers show automatically when you
open the folder) has the same section headers for every dataset: **Dataset**, **Raw Data**
(`summary.md` + `raw_data_profile.json` stats), **Transformation** (the standardized mapping
rules from `report/mapping_reference.md` + the vocabulary actually applied to this dataset +
`transform_notes.md`), **Final Darwin Core Archive** (`archive_summary.md` + record counts), and
**Human Review & Sign-off** (a table of each write-up's reviewed status). Its own front matter
rolls up an overall `reviewed` flag (true only once all three write-ups are), so a future script
could scan `datasets/*/README.md` and report review status across every dataset at a glance.

The quarto report (below) reads the same files and renders the same content with added charts --
it's a rendering of this documentation, not a second source of truth for it.

## Report site

```
pip install -e ".[report]"
cd report && quarto render      # or: quarto preview
```

Generates a small quarto website (`report/_site/`) with one page per program already run
through the pipeline above, meant for a reviewer who knows the field program to check the
pipeline's choices at each step: an AI-drafted raw-data summary, the deterministic raw-data
profile it was drafted from, the standardized column-mapping writeup plus this dataset's
transform review notes, validation charts (station map, measurement-value distributions), the
species/measurement tables, the final-archive writeup, and a download link for that program's
DwC-A zip -- plus a `listing.qmd` gallery of all of them. See `report/README.md` for how it's
wired together (adapted from the [quartobatch](https://github.com/7yl4r/quartobatch) batch-report
pattern).

## Test

```
pytest
```

Runs entirely offline against `tests/fixtures/` (a trimmed real excerpt of program 570's
export plus the SEACAR reference workbook). `test_pipeline_integration.py` exercises the
whole transform -> archive path and checks the produced `meta.xml` / zip structure.

## Design

- **Sampling grain**: one Event = one quadrat read at one station on one date
  (`ProgramID, ProgramLocationID, SampleDate, QuadIdentifier`). Verified empirically against
  program 570 (see `keys.py` docstring) -- every event-level column (lat/lon, quadrat size,
  survey method, ...) is constant within that grouping.
- **Natural keys, no hashes** (`keys.py`): `eventID` is built from the grain above,
  `occurrenceID` nests a `SpeciesID` under its `eventID`, `measurementID` nests a `ParameterID`
  under whichever of the two it belongs to. e.g. `urn:seacar:occ:570:MP05:2021-03-15:450:2795`.
- **Not every SpeciesID is a taxon** (`taxonomy.py`): SEACAR uses placeholder codes within a
  quadrat read -- "Total seagrass" (aggregate), "No grass in quadrat", "Drift algae" -- that
  have no `ScientificName` in the `Ref_Species` reference sheet. Their readings become
  event-level MeasurementOrFact rows (`occurrenceID` blank) instead of a fabricated Occurrence.
- **occurrenceStatus, not a duplicate measurement**: a `Presence/Absence` reading never becomes
  a MeasurementOrFact row. For a real taxon it sets `dwc:occurrenceStatus` on its Occurrence
  instead; for a non-taxon SpeciesID (no Occurrence to attach a status to) it is simply dropped
  -- occurrenceStatus is what that reading is for, so it need not appear in the archive at all
  either way. Only `Braun Blanquet Score` becomes a MeasurementOrFact.
- **Taxonomy source**: the `Ref_Species` sheet SEACAR ships inside every export's
  `SEACAR_Metadata.xlsx`, not a live WoRMS API call -- it's what SEACAR itself already
  reconciled against WoRMS/Florida Plant Atlas, is offline, and matches every dataset exactly.
  It gives `scientificName`/`kingdom`/.../`genus` but not the numeric AphiaID, so `worms.py`
  separately resolves `dwc:scientificNameID` as a WoRMS LSID (e.g.
  `urn:lsid:marinespecies.org:taxname:208925`) via `AphiaRecordsByMatchNames`, cached to
  `data/03_taxonomy_cache/worms_lsids.json` so repeat runs don't re-query. Genus-rank IDs
  ("Caulerpa spp.") are queried by genus alone (`taxonomy.worms_query_name`). Best-effort: a
  taxon truly absent from WoRMS (e.g. *Vallisneria americana*, a freshwater species -- confirmed
  via a direct API call returning 204 No Content, not a bug) just gets a blank
  `scientificNameID`, logged as a warning, not a pipeline failure.

## Target architecture (not yet built)

Today everything lives in one `seacar_to_dwc` package because there's one source. The intended
shape once a second source is actually being onboarded (see Follow-ups: SeagrassNet/PANGAEA) is:

- **`core`** (source-agnostic): natural-key builders (`keys.py`), archive assembly (`archive.py`),
  EML building (`eml.py`), WoRMS resolution (`worms.py`), raw-data profiling (`profile.py`), docs
  scaffolding (`docs_scaffold.py`), case-study assembly (`case_study.py`), the report templates,
  and the GOOS EOV target schema/vocabulary (see "Design" above and `report/mapping_reference.md`)
  every source should map into.
- **`sources/<name>/`** (source-specific): discovery/fetch/parse plus the transform functions
  that turn that source's native rows into the shared Event/Occurrence/EMoF DataFrames using
  `core`'s helpers. `sources/seacar/` would hold today's `discover.py`, `fetch.py`, `parse.py`,
  `taxonomy.py`, and `transform/`.

Deliberately not designing the adapter *interface* precisely yet -- SEACAR's long-format
pipe-delimited export and SeagrassNet/PANGAEA's shape are different enough that forcing an
abstraction from a single example would likely guess wrong. Do that once the second source
forces the interface's actual shape.

## Follow-ups (not yet done)

Concrete items surfaced during review, not yet acted on:

- **Report seagrass cover as `percentCover`, not the raw Braun-Blanquet class.** Duffy et al.
  2026 (`report/mapping_reference.md`) specifies `measurementType: percentCover` as the standard
  term; this pipeline should convert each Braun-Blanquet class to its documented percent-range
  midpoint (0.1/0.5/1/2/3/4/5 -> the ranges in `measurement_vocab.yaml`'s `measurementMethod`
  text) and report that as `percentCover`, keeping the raw class + method as provenance
  (`measurementMethod`/`measurementRemarks`) rather than the primary value.
- **Trim `event.py` to the fields actually earning their place.** Reviewer feedback: `locality`
  (currently the station/site name) should move into `eventRemarks`; the managed-area name
  (currently `waterBody`) should become the new `locality`; `waterBody`, `datasetID`, and
  `institutionCode` should be dropped from Event entirely.
- **Confirm `occurrence.txt`'s `taxonID` provenance.** Currently
  `f"urn:seacar:species:{SpeciesID}"` -- an internal urn, not a reference into an existing
  taxonomic authority. Worth confirming that's actually the intended value for `taxonID` (as
  opposed to, e.g., leaving it blank since `scientificNameID` already carries the WoRMS LSID).
- **Confirm absence records are retained end-to-end.** `occurrence.py` already creates an
  Occurrence with `occurrenceStatus: absent` for a real taxon with a "0" Presence/Absence
  reading; double check that holds for every dataset (not just 570) once a second dataset is run.
- **Multi-source core/adapter split** -- see "Target architecture" above. Next concrete source:
  SeagrassNet data via PANGAEA (`https://doi.pangaea.de/10.1594/PANGAEA.994149`).

## Other data on the program page not currently folded into the archive

`discover.py` scrapes `https://data.florida-seacar.org/programs/details/<id>` for everything
used above (title, contacts, citation, methods, managed areas, date range, the standardized
export zip link). The page also links to, per program:

- **Station-location GIS files** (e.g. `2016_Seagrass_Stations.zip`, `2020 seagrass stations.zip`)
  -- precise station geometries/boundaries. Not needed today since every data row already
  carries `OriginalLatitude`/`OriginalLongitude`, but would let a future version add
  `footprintWKT` or verify station coordinates.
- **Protocol documents** (`CHAP Seagrass Monitoring Protocols_2019_current.pdf`,
  `Seagrass Monitoring Protocols_2025.doc`, `DIP_570.pdf`) -- good candidates to cite by URL in
  `eml.xml`'s `<methods>` section (`dataset.methods.methodStep.description` could link out)
  rather than parse, since they're narrative protocol text, not tabular data.
  `meta.fields`/`meta.supplementary_files` in `discover.py` already captures these links if
  a future change wants to fold them in.
- **Raw program-supplied Excel/Access files** (`SEACAR_CHAP Seagrass Data_1999-2025_2025
  submission.xlsx`, the original `.accdb`) and prior seagrass reports (2016-2023 PDFs) --
  superseded by the standardized export for data purposes, kept only as provenance/citation
  material.
