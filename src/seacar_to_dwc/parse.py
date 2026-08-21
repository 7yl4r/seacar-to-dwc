"""Parse a SEACAR pipe-delimited export into a typed, deduplicated DataFrame.

Column definitions are documented in the "Col_SAV" sheet of the
SEACAR_Metadata.xlsx bundled with every export; see taxonomy.py for how the
Ref_Species sheet of that same workbook is used.
"""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

# Columns the rest of the pipeline (keys.py, transform/*) depends on. SEACAR's
# SAV habitat export always carries these; other habitats (Coral, Nekton, ...)
# have a different column set per Ref_Parameters and would need this list
# adjusted before reusing parse.py for them.
REQUIRED_COLUMNS = [
    "RowID", "ProgramID", "ProgramName", "Habitat",
    "IndicatorID", "IndicatorName", "ParameterID", "ParameterName", "ParameterUnits", "ResultValue",
    "SampleDate", "Include",
    "LocationID", "ProgramLocationID", "OriginalLatitude", "OriginalLongitude",
    "AreaID", "ManagedAreaName",
    "SpeciesID", "CommonIdentifier", "SpeciesName", "GenusName",
    "Drift_Attached", "SurveyMethod", "HabitatClassification", "ReportingLevel",
    "QuadSize_m2", "Depth_M", "QuadIdentifier", "SiteIdentifier",
    "SEACAR_QAQCFlagCode", "SEACAR_QAQC_Description",
]

# Row identity for exact-duplicate detection: two rows sharing all of these
# are the same reading reported twice (seen in program 570 -- a handful of
# rows repeated under a different RowID/ExportVersion), not two real facts.
DEDUPE_KEY = [
    "ProgramID", "LocationID", "SampleDate", "QuadIdentifier", "SpeciesID",
    "ParameterID", "ResultValue",
]

_NUMERIC_COLUMNS = ["ResultValue", "OriginalLatitude", "OriginalLongitude", "QuadSize_m2", "PlotSize_m2", "Depth_M"]


def parse(txt_path: Path, include_only: bool = True) -> pd.DataFrame:
    df = pd.read_csv(txt_path, sep="|", encoding="utf-8-sig", dtype=str, low_memory=False)

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"{txt_path}: missing expected columns {missing}")

    for col in _NUMERIC_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["SampleDate"] = pd.to_datetime(df["SampleDate"], errors="raise")

    before = len(df)
    df = df.drop_duplicates(subset=DEDUPE_KEY, keep="first")
    dropped = before - len(df)
    if dropped:
        logger.warning("%s: dropped %d exact-duplicate rows", txt_path, dropped)

    if include_only:
        before = len(df)
        df = df[df["Include"] == "1"]
        excluded = before - len(df)
        if excluded:
            logger.warning("%s: excluded %d rows with Include != 1", txt_path, excluded)

    return df.reset_index(drop=True)
