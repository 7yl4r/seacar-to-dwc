"""Deterministic, code-computed facts about a raw SEACAR export -- no AI, no
network, just counts and cross-references against Ref_Species /
measurement_vocab.yaml.

This is the grounding data for datasets/<id>/summary.md and
transform_notes.md (see docs_scaffold.py): a human or an AI drafting those
free-text write-ups should read this JSON rather than eyeball the raw file
by hand, and report/template.qmd renders it directly as its own "raw data
profile" section so the two stay checkable against each other.
"""
from __future__ import annotations

import pandas as pd


def _species_lookup_table(df: pd.DataFrame) -> pd.Series:
    """SpeciesID -> the raw file's own CommonIdentifier label for it, for
    describing flagged SpeciesIDs without a second Ref_Species lookup."""
    return (
        df[["SpeciesID", "CommonIdentifier"]]
        .dropna(subset=["SpeciesID"])
        .drop_duplicates(subset="SpeciesID")
        .assign(SpeciesID=lambda d: d["SpeciesID"].astype(int))
        .set_index("SpeciesID")["CommonIdentifier"]
    )


def raw_data_profile(df: pd.DataFrame, species_ref: pd.DataFrame) -> dict:
    species_ids = sorted({int(s) for s in df["SpeciesID"].dropna().unique()})
    ref_ids = {int(i) for i in species_ref.index if pd.notna(i)}
    names = _species_lookup_table(df)

    def _describe(ids: list[int]) -> list[dict]:
        return [{"species_id": sid, "common_identifier": names.get(sid)} for sid in ids]

    # in Ref_Species but with no ScientificName -- SEACAR's own aggregate/placeholder
    # codes (see taxonomy.py), routed to event-level facts rather than an Occurrence
    non_taxon_ids = [sid for sid in species_ids if sid in ref_ids and not bool(species_ref.loc[sid, "is_taxon"])]
    # NOT in Ref_Species at all -- taxonomy.lookup() treats these the same as a
    # non-taxon code today (silently dropped from Occurrence), but this could
    # equally mean the reference workbook is stale for this SpeciesID
    unresolved_ids = [sid for sid in species_ids if sid not in ref_ids]

    param_counts = df["ParameterID"].value_counts()
    qaqc_counts = df["SEACAR_QAQCFlagCode"].fillna("(none)").value_counts()

    return {
        "row_count": int(len(df)),
        "n_program_locations": int(df["ProgramLocationID"].nunique()),
        "n_species_ids": len(species_ids),
        "sample_date_range": {
            "start": str(df["SampleDate"].min().date()),
            "end": str(df["SampleDate"].max().date()),
        },
        "non_taxon_species": _describe(non_taxon_ids),
        "unresolved_species": _describe(unresolved_ids),
        "parameter_counts": {str(k): int(v) for k, v in param_counts.items()},
        "qaqc_flag_counts": {str(k): int(v) for k, v in qaqc_counts.items()},
    }


def unmapped_parameter_ids(df: pd.DataFrame, vocab: dict) -> list[dict]:
    """ParameterIDs present in this dataset with no entry in
    measurement_vocab.yaml -- emof.py falls back to the raw
    ParameterName/Units for these rather than a deliberate mapping."""
    known = set(vocab["parameters"].keys())
    rows = (
        df[["ParameterID", "ParameterName", "ParameterUnits"]]
        .drop_duplicates(subset="ParameterID")
    )
    return [
        {
            "parameter_id": row.ParameterID,
            "parameter_name": row.ParameterName,
            "parameter_units": row.ParameterUnits if pd.notna(row.ParameterUnits) else None,
        }
        for row in rows.itertuples(index=False)
        if row.ParameterID not in known
    ]
