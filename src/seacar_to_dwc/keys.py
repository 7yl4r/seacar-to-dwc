"""Natural-key builders shared by every transform stage.

All identifiers are built from fields already present in the SEACAR export
(no surrogate hashes) so they stay stable across re-exports and are legible
on their own, e.g. ``urn:seacar:occ:570:MP05:2021-03-15:450:2795``.

Sampling grain (verified against program 570, see tests/test_keys.py and the
project notes): one Event is one quadrat read at one station on one date --
``(ProgramID, ProgramLocationID, SampleDate, QuadIdentifier)`` is unique and
every event-level column (QuadSize_m2, Depth_M, SurveyMethod, lat/lon, ...)
is constant within it. Occurrences nest under an Event, one per SpeciesID.
"""
from __future__ import annotations

NAMESPACE = "urn:seacar"


def _sample_date(sample_date: str) -> str:
    """SampleDate arrives as 'YYYY-MM-DD HH:MM:SS.fff' (always midnight); keep the date part."""
    return str(sample_date).split(" ")[0]


def event_id(program_id: str, program_location_id: str, sample_date: str, quad_identifier: str) -> str:
    return f"{NAMESPACE}:event:{program_id}:{program_location_id}:{_sample_date(sample_date)}:{quad_identifier}"


def occurrence_id(program_id: str, program_location_id: str, sample_date: str, quad_identifier: str, species_id: str) -> str:
    eid = event_id(program_id, program_location_id, sample_date, quad_identifier)
    return f"{eid.replace(':event:', ':occ:')}:{species_id}"


def measurement_id(parent_id: str, parameter_id: str) -> str:
    """`parent_id` is an eventID (event-level fact) or an occurrenceID (taxon-level fact)."""
    prefix = parent_id.replace(":event:", ":mof:").replace(":occ:", ":mof:")
    return f"{prefix}:{parameter_id}"
