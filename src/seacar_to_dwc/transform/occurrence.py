"""Build the Occurrence extension (one row per taxon detected/checked-for within an Event).

Not every SEACAR SpeciesID is a real taxon (see taxonomy.py) -- rows for
non-taxon codes like "Total seagrass" or "No grass in quadrat" are excluded
here and instead become event-level facts in transform/emof.py.

occurrenceStatus is read off the row's Presence/Absence reading (the
parameter flagged `role: occurrence_status` in measurement_vocab.yaml) rather
than being emitted as its own MeasurementOrFact, since dwc:occurrenceStatus
is the correct home for that fact and duplicating it in the eMoF extension
would just restate it in a second vocabulary.
"""
from __future__ import annotations

import logging

import pandas as pd

from ..keys import event_id, occurrence_id
from ..taxonomy import lookup

logger = logging.getLogger(__name__)

GROUP_COLS = ["ProgramID", "ProgramLocationID", "SampleDate", "QuadIdentifier", "SpeciesID"]

OCCURRENCE_COLUMNS = [
    "occurrenceID", "eventID", "basisOfRecord", "occurrenceStatus",
    "scientificName", "taxonRank", "kingdom", "phylum", "class", "order", "family", "genus",
    "vernacularName", "taxonID", "occurrenceRemarks",
]


def _status_parameter_id(vocab: dict) -> str:
    for parameter_id, cfg in vocab["parameters"].items():
        if cfg["role"] == "occurrence_status":
            return parameter_id
    raise ValueError("measurement_vocab.yaml has no parameter with role: occurrence_status")


def build_occurrences(df: pd.DataFrame, species_ref: pd.DataFrame, vocab: dict) -> pd.DataFrame:
    status_parameter_id = _status_parameter_id(vocab)
    status_cfg = vocab["parameters"][status_parameter_id]

    rows = []
    for key, group in df.groupby(GROUP_COLS, sort=False):
        program_id, program_location_id, sample_date, quad_identifier, species_id = key

        taxon = lookup(species_ref, species_id)
        if not taxon.get("is_taxon"):
            continue  # aggregate/placeholder code, not a real occurrence -- see transform/emof.py

        date_str = str(sample_date.date())
        eid = event_id(program_id, program_location_id, date_str, quad_identifier)
        occ_id = occurrence_id(program_id, program_location_id, date_str, quad_identifier, species_id)

        status_rows = group[group["ParameterID"] == status_parameter_id]
        if len(status_rows):
            raw_value = status_rows.iloc[0]["ResultValue"]
            occurrence_status = "present" if float(raw_value) == float(status_cfg["present_value"]) else "absent"
        else:
            occurrence_status = None
            logger.warning("occurrence %s has no Presence/Absence reading to derive occurrenceStatus from", occ_id)

        first = group.iloc[0]
        remarks = None
        if pd.notna(first.Drift_Attached):
            remarks = f"{first.Drift_Attached} algae"

        rows.append({
            "occurrenceID": occ_id,
            "eventID": eid,
            "basisOfRecord": "HumanObservation",
            "occurrenceStatus": occurrence_status,
            "scientificName": taxon["scientificName"],
            "taxonRank": taxon["taxonRank"],
            "kingdom": taxon["kingdom"],
            "phylum": taxon["phylum"],
            "class": taxon["class_"],
            "order": taxon["order"],
            "family": taxon["family"],
            "genus": taxon["genus"],
            "vernacularName": taxon["vernacularName"],
            "taxonID": f"urn:seacar:species:{int(species_id)}",
            "occurrenceRemarks": remarks,
        })

    return pd.DataFrame(rows, columns=OCCURRENCE_COLUMNS)
