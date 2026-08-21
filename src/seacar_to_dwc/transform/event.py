"""Build the Darwin Core Event core.

One Event = one quadrat read at one station on one date. See keys.py for the
grain verification this relies on: every event-level column below (lat/lon,
QuadSize_m2, SurveyMethod, ...) is constant within
(ProgramID, ProgramLocationID, SampleDate, QuadIdentifier).
"""
from __future__ import annotations

import re

import pandas as pd

from ..keys import event_id

GROUP_COLS = ["ProgramID", "ProgramLocationID", "SampleDate", "QuadIdentifier"]

EVENT_COLUMNS = [
    "eventID", "eventDate", "year", "month",
    "samplingProtocol", "sampleSizeValue", "sampleSizeUnit",
    "habitat", "decimalLatitude", "decimalLongitude", "geodeticDatum",
    "countryCode", "stateProvince", "waterBody", "locality",
    "verbatimDepth", "datasetID", "institutionCode", "eventRemarks",
]

_AREA_PREFIX = re.compile(r"^\d+\s*-\s*")


def _water_body(managed_area_name) -> str | None:
    if pd.isna(managed_area_name):
        return None
    return _AREA_PREFIX.sub("", managed_area_name).strip()


def build_events(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for key, group in df.groupby(GROUP_COLS, sort=False):
        program_id, program_location_id, sample_date, quad_identifier = key
        first = group.iloc[0]

        eid = event_id(program_id, program_location_id, str(sample_date.date()), quad_identifier)

        remarks_parts = [f"Quadrat {quad_identifier}"]
        if pd.notna(first.SiteIdentifier) and first.SiteIdentifier != program_location_id:
            remarks_parts.append(f"transect {first.SiteIdentifier}")

        rows.append({
            "eventID": eid,
            "eventDate": str(sample_date.date()),
            "year": sample_date.year,
            "month": sample_date.month,
            "samplingProtocol": (
                f"{first.ReportingLevel} sample via Braun-Blanquet cover-abundance method; "
                f"{first.SurveyMethod} station design; {first.HabitatClassification} habitat"
            ),
            "sampleSizeValue": first.QuadSize_m2,
            "sampleSizeUnit": "square metres" if pd.notna(first.QuadSize_m2) else None,
            "habitat": first.Habitat,
            "decimalLatitude": first.OriginalLatitude,
            "decimalLongitude": first.OriginalLongitude,
            "geodeticDatum": "WGS84",
            "countryCode": "US",
            "stateProvince": "Florida",
            "waterBody": _water_body(first.ManagedAreaName),
            "locality": program_location_id,
            "verbatimDepth": first.Depth_M,
            "datasetID": str(program_id),
            "institutionCode": "SEACAR",
            "eventRemarks": "; ".join(remarks_parts),
        })

    return pd.DataFrame(rows, columns=EVENT_COLUMNS)
