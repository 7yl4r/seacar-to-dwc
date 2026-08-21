"""Taxonomy lookup, sourced from the Ref_Species sheet SEACAR ships in every
program's SEACAR_Metadata.xlsx.

SEACAR staff already reconcile every SpeciesID against the World Register of
Marine Species (WoRMS) or the Florida Plant Atlas and record the accepted
higher classification (see the sheet's own preamble). Using that beats a live
WoRMS API lookup: it's authoritative for what SEACAR means by each
CommonIdentifier, offline, and matches every dataset exactly (no rate limits,
no ambiguous-match guessing).

Not every SpeciesID is a real taxon. A handful are aggregate/placeholder
codes SEACAR uses within a quadrat read -- e.g. "Total seagrass" (sum across
species), "No grass in quadrat" (nothing found), "Drift algae" (unidentified
drift material). These have no ScientificName in Ref_Species; `is_taxon`
flags them so transform/occurrence.py can route their rows to event-level
measurements instead of fabricating an Occurrence with no scientific name.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

_HEADER_ROW = 7  # rows above the header are sheet title/preamble text, see tests/test_taxonomy.py

_RENAME = {
    "SpeciesID": "SpeciesID",
    "ScientificName": "scientificName",
    "GenusName": "genus",
    "CommonName": "vernacularName",
    "Family": "family",
    "Order": "order",
    "Class": "class_",
    "Phylum": "phylum",
    "Kingdom": "kingdom",
    "Source": "taxonSource",
}


def load_species_reference(metadata_xlsx: Path) -> pd.DataFrame:
    df = pd.read_excel(metadata_xlsx, sheet_name="Ref_Species", skiprows=_HEADER_ROW)
    df = df.rename(columns=_RENAME)[list(_RENAME.values())]
    df["SpeciesID"] = df["SpeciesID"].astype("Int64")
    df = df.drop_duplicates(subset="SpeciesID", keep="first").set_index("SpeciesID")

    df["is_taxon"] = df["scientificName"].notna()
    # genus-only identifications ("Halophila sp.", "Caulerpa spp.") carry a
    # scientificName equal to the CommonIdentifier but no species epithet
    df["taxonRank"] = pd.NA
    df.loc[df["is_taxon"], "taxonRank"] = "species"
    df.loc[df["is_taxon"] & df["scientificName"].str.endswith((" sp.", " spp."), na=False), "taxonRank"] = "genus"

    return df


def lookup(species_ref: pd.DataFrame, species_id) -> dict:
    """Return the taxonomy row for `species_id` as a dict, or an empty/non-taxon dict if absent."""
    try:
        row = species_ref.loc[int(species_id)]
    except (KeyError, ValueError):
        return {"is_taxon": False}
    return row.to_dict()


def worms_query_name(taxon: dict) -> str | None:
    """The name to hand WoRMS for this taxon: genus alone for genus-rank IDs
    ("Caulerpa spp." isn't a WoRMS-matchable string; "Caulerpa" is), the full
    scientificName otherwise."""
    if not taxon.get("is_taxon"):
        return None
    if taxon.get("taxonRank") == "genus":
        return taxon.get("genus")
    return taxon.get("scientificName")
