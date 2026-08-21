"""Build the MeasurementOrFact extension.

Every source row becomes one MeasurementOrFact record *except* Presence/Absence
readings (role: occurrence_status in measurement_vocab.yaml): for a real taxon
that becomes dwc:occurrenceStatus on the Occurrence instead (see
transform/occurrence.py), and for a non-taxon SpeciesID ("Total seagrass",
"No grass in quadrat", "Drift algae") it is simply dropped -- occurrenceStatus
is what that reading is for, so it need not appear in eMoF at all.

Two attachment levels for the facts that remain:
  - taxon-level: occurrenceID is set -- the fact is about a specific
    species-in-quadrat (e.g. its Braun Blanquet cover score).
  - event-level: occurrenceID is blank, only eventID is set -- the fact is
    about the quadrat as a whole. This includes readings for non-taxon
    SpeciesIDs, since those have no Occurrence to attach to.
"""
from __future__ import annotations

import logging

import pandas as pd

from ..keys import event_id, measurement_id, occurrence_id
from ..taxonomy import lookup

logger = logging.getLogger(__name__)

EMOF_COLUMNS = [
    "measurementID", "eventID", "occurrenceID",
    "measurementType", "measurementValue", "measurementUnit",
    "measurementMethod", "measurementRemarks",
]

_warned_unknown_parameters: set[str] = set()


def build_emof(df: pd.DataFrame, species_ref: pd.DataFrame, vocab: dict) -> pd.DataFrame:
    params = vocab["parameters"]
    rows = []

    for row in df.itertuples(index=False):
        parameter_id = row.ParameterID
        cfg = params.get(parameter_id)
        if cfg is None:
            if parameter_id not in _warned_unknown_parameters:
                logger.warning(
                    "ParameterID %s (%s) not in measurement_vocab.yaml, using raw ParameterName/Units as-is",
                    parameter_id, row.ParameterName,
                )
                _warned_unknown_parameters.add(parameter_id)
            cfg = {"role": "measurement", "measurementType": row.ParameterName, "measurementUnit": row.ParameterUnits, "measurementMethod": None}

        if cfg["role"] == "occurrence_status":
            continue  # dwc:occurrenceStatus is what this reading is for, taxon or not

        taxon = lookup(species_ref, row.SpeciesID)
        is_taxon = taxon.get("is_taxon", False)

        date_str = str(row.SampleDate.date())
        eid = event_id(row.ProgramID, row.ProgramLocationID, date_str, row.QuadIdentifier)
        occ_id = occurrence_id(row.ProgramID, row.ProgramLocationID, date_str, row.QuadIdentifier, row.SpeciesID) if is_taxon else None
        parent_id = occ_id or eid

        remarks_parts = []
        if pd.notna(row.SEACAR_QAQC_Description):
            remarks_parts.append(row.SEACAR_QAQC_Description)
        if not is_taxon and pd.notna(row.CommonIdentifier):
            remarks_parts.append(f"recorded against SEACAR code: {row.CommonIdentifier}")

        rows.append({
            "measurementID": measurement_id(parent_id, parameter_id),
            "eventID": eid,
            "occurrenceID": occ_id,
            "measurementType": cfg.get("measurementType") or row.ParameterName,
            "measurementValue": row.ResultValue,
            "measurementUnit": cfg.get("measurementUnit") or (row.ParameterUnits if pd.notna(row.ParameterUnits) else None),
            "measurementMethod": cfg.get("measurementMethod"),
            "measurementRemarks": "; ".join(remarks_parts) or None,
        })

    return pd.DataFrame(rows, columns=EMOF_COLUMNS)
