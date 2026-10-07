---
program_id: "REPLACE_WITH_YOUR_PROGRAM_ID"  # e.g. 570 -- also rename this folder to match
habitat: null   # e.g. SAV -- optional, descriptive only
description: null   # a short human-readable name for this dataset
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
generated_by: null
reviewed: false
reviewed_by: null
reviewed_at: null
---
