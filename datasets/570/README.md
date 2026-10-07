---
program_id: "570"
title: "Charlotte Harbor Seagrass Monitoring"
generated_at: "2026-10-02"
reviewed: false
---

# Case study: 570 -- Charlotte Harbor Seagrass Monitoring

**Organization:** Florida Department of Environmental Protection (DEP), Office of Resilience and Coastal Protection (RCP), Charlotte Harbor Aquatic Preserves

**Managed area(s):** Cape Haze AP, Gasparilla Sound-Charlotte Harbor AP, Lemon Bay AP, Matlacha Pass AP, Pine Island Sound AP

**Source:** https://data.florida-seacar.org/programs/details/570

> Florida Department of Environmental Protection (DEP), Office of Resilience and Coastal Protection (RCP), Charlotte Harbor Aquatic Preserves. (2025). Charlotte Harbor Seagrass Monitoring. Updated 03/23/2026. Distributed by: SEACAR Data Discovery Interface, Office of Resilience and Coastal Protection, Florida Department of Environmental Protection. https://data.florida-seacar.org/programs/details/570

## Raw Data

> ⚠️ **Not yet reviewed by a data manager.** Drafted by Claude (claude-sonnet-5), 2026-08-25, from raw_data_profile.json; flip `reviewed: true` in the front matter once checked.

# Raw data summary: program 570 (Charlotte Harbor Seagrass Monitoring)

61,969 rows covering 63 stations across five managed areas (Cape Haze, Gasparilla
Sound-Charlotte Harbor, Lemon Bay, Matlacha Pass, Pine Island Sound), sampled
1998-06-15 through 2025-11-25 -- a long-running, fairly stable fixed-transect
program rather than a one-off survey.

Every row is one of exactly two parameters: **Presence/Absence** (30,981 rows) and
**Braun Blanquet Score** (30,988 rows), almost perfectly paired per quadrat/species
reading as expected. 18 distinct SpeciesIDs appear: 15 are real taxa (mostly
seagrasses and macroalgae -- *Halodule wrightii*, *Thalassia testudinum*,
*Caulerpa* spp., etc.) and 3 are SEACAR's own aggregate/placeholder codes ("Total
seagrass", "No grass in quadrat", "Drift algae"), all correctly recognized as
non-taxon by `Ref_Species` -- see `raw_data_profile.json: non_taxon_species`.

No SpeciesIDs are missing from `Ref_Species` (`unresolved_species` is empty) and
every ParameterID in the data has a `measurement_vocab.yaml` entry
(`unmapped_parameters` is empty), so nothing here is silently falling through a
default path. QAQC flags are almost entirely `7Q` / `1Q/7Q` (SEACAR's standard
"calculated, no defined threshold" combination); one lone row carries `7Q/15Q`
instead -- not investigated, but worth a glance if anyone is auditing QAQC flag
handling specifically. The source parse also drops 18 exact-duplicate rows on
every run (same program/location/date/quad/species/parameter/value reported
twice), which looks like a benign export artifact rather than a real duplicate
observation.

### Raw data profile

- **61,969** raw rows, **63** stations, **18** distinct SpeciesIDs
- sample dates: 1998-06-15 to 2025-11-25
- QAQC flags: `7Q` (30,987), `1Q/7Q` (30,981), `7Q/15Q` (1)

- non-taxon placeholder codes present: 3681 (No grass in quadrat), 15414 (Drift algae), 15472 (Total seagrass)

## Transformation

This section is identical across every dataset -- the transform logic is shared
code (`src/seacar_to_dwc/transform/`), not configured per program. What varies
per dataset is *which* of these rules actually fire on its data; see
"Applied to this dataset" below for that.

**Target standard.** This Event+Occurrence+EMoF layout, and `scientificNameID` as a WoRMS
LSID, follow the GOOS Seagrass Essential Ocean Variable specification: Duffy et al. (2026),
["Measuring and Reporting on Seagrass as an Essential Ocean Variable for Science and
Management"](https://doi.org/10.1093/biosci/biaf199), *BioScience* 76(4):359-374, and its data
dictionary (`report/references/duffy-et-al.pdf`, `duffy-supplement.pdf`). That spec's standard
`measurementType` vocabulary reports seagrass cover as `percentCover` (a defined percentage),
not a raw Braun-Blanquet class -- this pipeline still reports the raw
`"Percent Cover (Braun-Blanquet cover-abundance score)"` value today; converting to `percentCover`
via the documented class-midpoint mapping is a tracked follow-up (see the top-level README).

**Grain.** One Event = one quadrat read at one station on one date
(`ProgramID, ProgramLocationID, SampleDate, QuadIdentifier`).

**Event core** (`transform/event.py`):

- `eventDate`/`year`/`month` from `SampleDate`
- `decimalLatitude`/`decimalLongitude` from `OriginalLatitude`/`OriginalLongitude`
- `sampleSizeValue`/`sampleSizeUnit` from `QuadSize_m2`
- `waterBody` from `ManagedAreaName` (leading `"NN - "` area-ID prefix stripped)
- `samplingProtocol` assembled from `ReportingLevel`/`SurveyMethod`/`HabitatClassification`
- `geodeticDatum` is hardcoded `WGS84`, `countryCode` `US`, `stateProvince` `Florida`,
  `institutionCode` `SEACAR` -- these are true for every SEACAR program, not derived per-row

**Occurrence extension** (`transform/occurrence.py`): one row per (event, SpeciesID)
*if and only if* that SpeciesID is a real taxon -- `Ref_Species.ScientificName` is
non-null (see `taxonomy.py`); non-taxon placeholder codes (SEACAR aggregate/absence
codes like "Total seagrass", "No grass in quadrat") never become an Occurrence.

- `scientificName`/`taxonRank`/`kingdom`/.../`genus` come straight from `Ref_Species`
- `scientificNameID` is a WoRMS LSID resolved live via `AphiaRecordsByMatchNames`
  (genus-rank IDs are queried by genus alone -- see `taxonomy.worms_query_name`),
  cached to `data/03_taxonomy_cache/worms_lsids.json`
- `basisOfRecord` is always `HumanObservation`
- `occurrenceStatus` is read off that Occurrence's Presence/Absence reading
  (`ResultValue` 1 -> present, 0 -> absent)

**MeasurementOrFact extension** (`transform/emof.py`): every remaining source row
becomes one eMoF record, *except* Presence/Absence readings (role `occurrence_status`
in `measurement_vocab.yaml`), which are dropped entirely.

- for a real taxon that fact is `occurrenceStatus` above
- for a non-taxon SpeciesID there's no Occurrence to attach a status to, so it's
  simply not included (occurrenceStatus is what it's for, whether or not a row
  happens to have one)
- a fact attaches to `occurrenceID` when its SpeciesID is a real taxon (e.g. Braun
  Blanquet Score for *Halodule wrightii*)
- a fact attaches to `eventID` alone when its SpeciesID isn't a real taxon (e.g.
  Braun Blanquet Score reported against "Total seagrass" -- the quadrat's total
  cover, not any one species)
- `measurementType`/`measurementUnit`/`measurementMethod` come from
  `config/measurement_vocab.yaml`, keyed by ParameterID
- a ParameterID with no entry there falls back to the raw `ParameterName`/
  `ParameterUnits` as-is (flagged below if this dataset has any)

### Applied to this dataset

| ParameterID | rows | role | measurementType / status parameter |
| --- | --- | --- | --- |
| 21 | 30,988 | measurement | Percent Cover (Braun-Blanquet cover-abundance score) |
| 69 | 30,981 | occurrence_status | Presence/Absence |

> ⚠️ **Not yet reviewed by a data manager.** Drafted by Claude (claude-sonnet-5), 2026-08-25, from raw_data_profile.json; flip `reviewed: true` in the front matter once checked.

# Transformation review notes: program 570 (Charlotte Harbor Seagrass Monitoring)

Nothing in this dataset hits a fallback path: both ParameterIDs (69 Presence/Absence,
21 Braun Blanquet Score) are explicitly mapped in `measurement_vocab.yaml`, and every
SpeciesID either resolves to a real taxon or is one of SEACAR's own recognized
non-taxon codes (`Ref_Species` has no gaps for this program). So the general
mapping rules in `report/mapping_reference.md` apply here without exception --
these notes just confirm that and flag one thing worth a second look.

**Non-taxon readings are dropped entirely, including Braun Blanquet Score.** The
3 non-taxon SpeciesIDs ("Total seagrass", "No grass in quadrat", "Drift algae")
carry both Presence/Absence *and* Braun Blanquet Score readings in the raw data.
Presence/Absence is dropped by design for every SpeciesID (`occurrenceStatus` is
what it's for). But Braun Blanquet Score for a non-taxon code becomes an
event-level MeasurementOrFact (`occurrenceID` blank) -- i.e. "Total seagrass"
percent-cover readings *are* retained in the archive, just not tied to any one
species. Worth confirming that's the intended behavior for a program manager who
cares about total-cover trends specifically, since it's easy to miss in the
Occurrence-focused species table.

**Genus-rank WoRMS resolution**: any *Caulerpa* spp. / *Halophila* sp. style
identifications are queried against WoRMS by genus alone (see
`taxonomy.worms_query_name`), so `scientificNameID` on those Occurrences points to
the genus-level AphiaID, not a species. That's expected, not a bug, but flagging
it here since it's the kind of thing a downstream data user might otherwise
mistake for imprecise resolution.

## Final Darwin Core Archive

> ⚠️ **Not yet reviewed by a data manager.** Drafted by Claude (claude-sonnet-5), 2026-09-25, from report_meta.json; flip `reviewed: true` in the front matter once checked.

# Final archive summary: program 570 (Charlotte Harbor Seagrass Monitoring)

`seacar-570-dwca.zip`: **13,601** events, **13,725** occurrences, **30,988** measurements.
The occurrence:event ratio (~1.01) makes sense for this program -- most quadrats record only
one or two of the 15 real taxa present station-to-station, so slightly more occurrences than
events is expected, not a taxonomy-join undercount. The measurement count matches
`raw_data_profile.json`'s Braun Blanquet Score row count (30,988) exactly, confirming every
retained reading made it into the archive and nothing was silently dropped beyond the
by-design Presence/Absence exclusion.

EML citation, contact info (two Charlotte Harbor Aquatic Preserves staff), and the five managed
areas all look right against the source page. Coverage (1998-06-15 to 2025-11-25; bounding box
matches the five listed managed areas along Florida's southwest coast) is consistent with a
long-running fixed-transect program, not truncated or shifted. No spot-check surprises in
`event.csv`/`occurrence.csv`/`emof.csv`.

- **13,601** events, **13,725** occurrences, **30,988** measurements
- archive file: `seacar-570-dwca.zip`

## Human Review & Sign-off

| Write-up | Reviewed | By | When |
| --- | --- | --- | --- |
| summary.md | no |  |  |
| transform_notes.md | no |  |  |
| archive_summary.md | no |  |  |
