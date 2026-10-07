---
instructions: |-
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
  reviewed: false until a data manager signs off, same as summary.md.
generated_by: "Claude (claude-sonnet-5), 2026-09-25, from report_meta.json"
reviewed: false
reviewed_by: null
reviewed_at: null
---

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
