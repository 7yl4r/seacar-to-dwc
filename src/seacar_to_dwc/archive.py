"""Assemble event.txt / occurrence.txt / extendedmeasurementorfact.txt / meta.xml
/ eml.xml into a zipped Darwin Core Archive, ready to hand to IPT.

Star schema: Event core, with Occurrence and MeasurementOrFact as extensions
that both key off eventID via <coreid>. The eMoF file additionally carries an
occurrenceID column (mapped to dwc:occurrenceID even though it isn't part of
GBIF's formal eMoF term list) for facts that belong to one specific taxon
occurrence rather than the whole event -- the same pattern OBIS/GBIF
"sample-based data" guidance uses for this exact Event+Occurrence+eMoF star.
"""
from __future__ import annotations

import zipfile
from pathlib import Path

import pandas as pd
from lxml import etree

DWC = "http://rs.tdwg.org/dwc/terms/"
GBIF = "http://rs.gbif.org/terms/1.0/"
META_XMLNS = "http://rs.tdwg.org/dwc/text/"

EVENT_ROW_TYPE = f"{DWC}Event"
OCCURRENCE_ROW_TYPE = f"{DWC}Occurrence"
EMOF_ROW_TYPE = f"{GBIF}MeasurementOrFact"

# (column name, term URI) for every column in the file, id/coreid column included
# (both the file-position <id>/<coreid> pointer AND a <field> term mapping are
# emitted for it -- the dual mapping real GBIF/IPT example archives use).
EVENT_FIELDS = [
    ("eventID", f"{DWC}eventID"),
    ("eventDate", f"{DWC}eventDate"),
    ("year", f"{DWC}year"),
    ("month", f"{DWC}month"),
    ("samplingProtocol", f"{DWC}samplingProtocol"),
    ("sampleSizeValue", f"{DWC}sampleSizeValue"),
    ("sampleSizeUnit", f"{DWC}sampleSizeUnit"),
    ("habitat", f"{DWC}habitat"),
    ("decimalLatitude", f"{DWC}decimalLatitude"),
    ("decimalLongitude", f"{DWC}decimalLongitude"),
    ("geodeticDatum", f"{DWC}geodeticDatum"),
    ("countryCode", f"{DWC}countryCode"),
    ("stateProvince", f"{DWC}stateProvince"),
    ("waterBody", f"{DWC}waterBody"),
    ("locality", f"{DWC}locality"),
    ("verbatimDepth", f"{DWC}verbatimDepth"),
    ("datasetID", f"{DWC}datasetID"),
    ("institutionCode", f"{DWC}institutionCode"),
    ("eventRemarks", f"{DWC}eventRemarks"),
]

OCCURRENCE_FIELDS = [
    ("occurrenceID", f"{DWC}occurrenceID"),
    ("eventID", f"{DWC}eventID"),  # coreid join column
    ("basisOfRecord", f"{DWC}basisOfRecord"),
    ("occurrenceStatus", f"{DWC}occurrenceStatus"),
    ("scientificName", f"{DWC}scientificName"),
    ("taxonRank", f"{DWC}taxonRank"),
    ("kingdom", f"{DWC}kingdom"),
    ("phylum", f"{DWC}phylum"),
    ("class", f"{DWC}class"),
    ("order", f"{DWC}order"),
    ("family", f"{DWC}family"),
    ("genus", f"{DWC}genus"),
    ("vernacularName", f"{DWC}vernacularName"),
    ("taxonID", f"{DWC}taxonID"),
    ("occurrenceRemarks", f"{DWC}occurrenceRemarks"),
]

EMOF_FIELDS = [
    ("measurementID", f"{DWC}measurementID"),
    ("eventID", f"{DWC}eventID"),  # coreid join column
    ("occurrenceID", f"{DWC}occurrenceID"),  # set only for taxon-level facts
    ("measurementType", f"{DWC}measurementType"),
    ("measurementValue", f"{DWC}measurementValue"),
    ("measurementUnit", f"{DWC}measurementUnit"),
    ("measurementMethod", f"{DWC}measurementMethod"),
    ("measurementRemarks", f"{DWC}measurementRemarks"),
]


def _write_table(df: pd.DataFrame, columns: list[tuple[str, str | None]], path: Path) -> None:
    col_names = [c for c, _ in columns]
    df.to_csv(path, sep="\t", columns=col_names, index=False, na_rep="")


def _core_or_extension(
    tag: str, row_type: str, filename: str, fields: list[tuple[str, str]], id_tag: str, id_column: str,
) -> etree._Element:
    el = etree.Element(
        tag,
        encoding="UTF-8",
        fieldsTerminatedBy="\\t",
        linesTerminatedBy="\\n",
        fieldsEnclosedBy="",
        ignoreHeaderLines="1",
        rowType=row_type,
    )
    files = etree.SubElement(el, "files")
    etree.SubElement(files, "location").text = filename

    id_index = next(i for i, (name, _) in enumerate(fields) if name == id_column)
    etree.SubElement(el, id_tag, index=str(id_index))
    for index, (_, term) in enumerate(fields):
        etree.SubElement(el, "field", index=str(index), term=term)
    return el


def build_meta_xml() -> bytes:
    root = etree.Element("archive", nsmap={None: META_XMLNS}, metadata="eml.xml")
    root.append(_core_or_extension("core", EVENT_ROW_TYPE, "event.txt", EVENT_FIELDS, "id", "eventID"))
    root.append(_core_or_extension("extension", OCCURRENCE_ROW_TYPE, "occurrence.txt", OCCURRENCE_FIELDS, "coreid", "eventID"))
    root.append(_core_or_extension("extension", EMOF_ROW_TYPE, "extendedmeasurementorfact.txt", EMOF_FIELDS, "coreid", "eventID"))
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", pretty_print=True)


def assemble_archive(
    output_dir: Path,
    event_df: pd.DataFrame,
    occurrence_df: pd.DataFrame,
    emof_df: pd.DataFrame,
    eml_bytes: bytes,
    archive_name: str,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    _write_table(event_df, EVENT_FIELDS, output_dir / "event.txt")
    _write_table(occurrence_df, OCCURRENCE_FIELDS, output_dir / "occurrence.txt")
    _write_table(emof_df, EMOF_FIELDS, output_dir / "extendedmeasurementorfact.txt")
    (output_dir / "meta.xml").write_bytes(build_meta_xml())
    (output_dir / "eml.xml").write_bytes(eml_bytes)

    zip_path = output_dir / f"{archive_name}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in ["event.txt", "occurrence.txt", "extendedmeasurementorfact.txt", "meta.xml", "eml.xml"]:
            zf.write(output_dir / name, arcname=name)

    return zip_path
