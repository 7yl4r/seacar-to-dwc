"""End-to-end test using the local fixture -- no network access.

Covers discover.py's ProgramMetadata -> eml.py -> archive.py wiring, and
checks the produced Darwin Core Archive has the shape IPT expects
(meta.xml declaring one core + two extensions, all four data/metadata files
present in the zip, and coreid linkage holding together).
"""
import csv
import io
import zipfile

from lxml import etree

from seacar_to_dwc import archive, taxonomy
from seacar_to_dwc.discover import Contact, ProgramMetadata
from seacar_to_dwc.eml import build_eml
from seacar_to_dwc.transform.emof import build_emof
from seacar_to_dwc.transform.event import build_events
from seacar_to_dwc.transform.occurrence import build_occurrences


def _fake_meta() -> ProgramMetadata:
    return ProgramMetadata(
        program_id="570",
        title="Charlotte Harbor Seagrass Monitoring",
        organization="Florida DEP",
        managed_areas=["Gasparilla Sound-Charlotte Harbor AP"],
        contacts=[Contact(name="Melynda Brown", role="Manager", email="m@example.gov", phone="941-000-0000")],
        fields={"Summary": "Seagrass monitoring", "SEACAR Citation": "FDEP (2025). Test citation."},
        dataset_zip_url="https://data.florida-seacar.org/static/datadownload/SAV - 570.zip",
        metadata_xlsx_url="https://data.florida-seacar.org/static/metadataexport/SEACAR_Metadata.xlsx",
        source_url="https://data.florida-seacar.org/programs/details/570",
    )


def test_full_local_pipeline_produces_a_valid_archive(sample_df, sample_xlsx_path, vocab, tmp_path):
    species_ref = taxonomy.load_species_reference(sample_xlsx_path)

    event_df = build_events(sample_df)
    occurrence_df = build_occurrences(sample_df, species_ref, vocab)
    emof_df = build_emof(sample_df, species_ref, vocab)

    eml_bytes = build_eml(
        _fake_meta(),
        bbox={"south": 26.5, "north": 26.9, "west": -82.2, "east": -82.0},
        date_range={"start": "1998-07-24", "end": "2015-09-23"},
        record_counts={"events": len(event_df), "occurrences": len(occurrence_df), "measurementOrFacts": len(emof_df)},
    )
    etree.fromstring(eml_bytes)  # raises if malformed

    zip_path = archive.assemble_archive(
        tmp_path / "out", event_df, occurrence_df, emof_df, eml_bytes, archive_name="test-dwca",
    )

    with zipfile.ZipFile(zip_path) as zf:
        names = set(zf.namelist())
        assert names == {"event.txt", "occurrence.txt", "extendedmeasurementorfact.txt", "meta.xml", "eml.xml"}

        meta_tree = etree.fromstring(zf.read("meta.xml"))
        ns = {"m": archive.META_XMLNS}
        assert meta_tree.get("metadata") == "eml.xml"
        core = meta_tree.find("m:core", ns)
        assert core.get("rowType") == archive.EVENT_ROW_TYPE
        extensions = meta_tree.findall("m:extension", ns)
        assert {e.get("rowType") for e in extensions} == {archive.OCCURRENCE_ROW_TYPE, archive.EMOF_ROW_TYPE}

        # coreid must point at the eventID column's actual position in each
        # extension file, not just assume column 0 (regression: it used to be
        # hardcoded to 0, which happened to be occurrenceID/measurementID instead)
        for ext, fields in [
            (meta_tree.findall("m:extension", ns)[0], archive.OCCURRENCE_FIELDS),
            (meta_tree.findall("m:extension", ns)[1], archive.EMOF_FIELDS),
        ]:
            expected_index = next(i for i, (name, _) in enumerate(fields) if name == "eventID")
            coreid = ext.find("m:coreid", ns)
            assert coreid.get("index") == str(expected_index)

        event_rows = list(csv.DictReader(io.StringIO(zf.read("event.txt").decode("utf-8")), delimiter="\t"))
        occ_rows = list(csv.DictReader(io.StringIO(zf.read("occurrence.txt").decode("utf-8")), delimiter="\t"))
        mof_rows = list(csv.DictReader(io.StringIO(zf.read("extendedmeasurementorfact.txt").decode("utf-8")), delimiter="\t"))

        assert len(event_rows) == 2
        assert len(occ_rows) == 3
        assert len(mof_rows) == 7

        event_ids = {r["eventID"] for r in event_rows}
        # every occurrence and every measurement must key back to a real event (coreid linkage)
        assert {r["eventID"] for r in occ_rows} <= event_ids
        assert {r["eventID"] for r in mof_rows} <= event_ids

        occurrence_ids = {r["occurrenceID"] for r in occ_rows}
        taxon_level_facts = [r for r in mof_rows if r["occurrenceID"]]
        assert taxon_level_facts, "expected at least one occurrence-level measurement"
        assert {r["occurrenceID"] for r in taxon_level_facts} <= occurrence_ids
