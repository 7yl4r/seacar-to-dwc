# seacar-to-dwc

Converts FL SEACAR program exports (e.g. https://data.florida-seacar.org/programs/details/570)
into a Darwin Core Archive: **Event core + Occurrence extension + MeasurementOrFact extension**,
ready to upload into IPT.

## Install

```
pip install -e ".[dev]"
```

## Run

```
python -m seacar_to_dwc.pipeline 570          # one program
python -m seacar_to_dwc.pipeline --all        # every program in config/datasets.yaml
```

Output: `data/05_archive/<program_id>/seacar-<program_id>-dwca.zip`.

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
