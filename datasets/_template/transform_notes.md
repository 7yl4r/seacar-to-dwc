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
generated_by: null
reviewed: false
reviewed_by: null
reviewed_at: null
---
