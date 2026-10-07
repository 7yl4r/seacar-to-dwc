---
program_id: "570"
habitat: "SAV"
description: "Charlotte Harbor Seagrass Monitoring (pilot dataset)"
instructions: |-
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
  against the real data, then flip it to true with reviewed_by/reviewed_at.
generated_by: "Claude (claude-sonnet-5), 2026-08-25, from raw_data_profile.json"
reviewed: false
reviewed_by: null
reviewed_at: null
---

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
