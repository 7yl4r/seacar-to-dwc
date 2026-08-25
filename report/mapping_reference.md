This section is identical across every dataset -- the transform logic is shared
code (`src/seacar_to_dwc/transform/`), not configured per program. What varies
per dataset is *which* of these rules actually fire on its data; see
"Applied to this dataset" below for that.

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
