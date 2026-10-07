---
instructions: |-
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
  reviewed: false until a data manager signs off, same as summary.md.
generated_by: "Claude (claude-sonnet-5), 2026-08-25, from raw_data_profile.json"
reviewed: false
reviewed_by: null
reviewed_at: null
---

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
