"""Build eml.xml from the scraped program page metadata (discover.py).

IPT reads eml.xml when you create a resource from an existing Darwin Core
Archive, prefilling title/creator/contact/abstract/coverage from it -- this
is what makes the archive genuinely "ready to upload" rather than needing
metadata re-entered by hand in the IPT UI.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

from lxml import etree

from .discover import ProgramMetadata

EML_NS = "eml://ecoinformatics.org/eml-2.1.1"
DC_NS = "http://purl.org/dc/terms/"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
NSMAP = {"eml": EML_NS, "dc": DC_NS, "xsi": XSI_NS}


def _para(parent, text: str):
    if text:
        etree.SubElement(parent, "para").text = text


def build_eml(meta: ProgramMetadata, bbox: dict, date_range: dict, record_counts: dict) -> bytes:
    package_id = f"urn:seacar:dataset:{meta.program_id}:{datetime.now(timezone.utc):%Y%m%dT%H%M%S}"

    root = etree.Element(
        f"{{{EML_NS}}}eml",
        nsmap=NSMAP,
        attrib={
            f"{{{XSI_NS}}}schemaLocation": f"{EML_NS} http://rs.gbif.org/schema/eml-gbif-profile/1.2/eml.xsd",
            "packageId": package_id,
            "system": "http://data.florida-seacar.org",
            "scope": "system",
        },
    )
    dataset = etree.SubElement(root, "dataset")

    etree.SubElement(dataset, "title").text = meta.title

    creator = etree.SubElement(dataset, "creator")
    etree.SubElement(creator, "organizationName").text = meta.organization

    metadata_provider = etree.SubElement(dataset, "metadataProvider")
    etree.SubElement(metadata_provider, "organizationName").text = "Florida SEACAR Data Discovery Interface"
    etree.SubElement(metadata_provider, "onlineUrl").text = meta.source_url

    for contact in meta.contacts:
        party = etree.SubElement(dataset, "associatedParty")
        individual = etree.SubElement(party, "individualName")
        name_parts = contact.name.rsplit(" ", 1)
        if len(name_parts) == 2:
            etree.SubElement(individual, "givenName").text = name_parts[0]
            etree.SubElement(individual, "surName").text = name_parts[1]
        else:
            etree.SubElement(individual, "surName").text = contact.name
        if contact.role:
            etree.SubElement(party, "positionName").text = contact.role
        if contact.email:
            etree.SubElement(party, "electronicMailAddress").text = contact.email
        if contact.phone:
            etree.SubElement(party, "phone").text = contact.phone
        etree.SubElement(party, "role").text = "pointOfContact"

    etree.SubElement(dataset, "pubDate").text = date.today().isoformat()
    etree.SubElement(dataset, "language").text = "en"

    if meta.summary:
        abstract = etree.SubElement(dataset, "abstract")
        _para(abstract, meta.summary)

    keyword_set = etree.SubElement(dataset, "keywordSet")
    for kw in [meta.fields.get("Habitats"), "Darwin Core", "SEACAR", "occurrence"]:
        if kw:
            etree.SubElement(keyword_set, "keyword").text = kw

    if meta.managed_areas:
        for area in meta.managed_areas:
            kw_set = etree.SubElement(dataset, "keywordSet")
            etree.SubElement(kw_set, "keyword").text = area
            etree.SubElement(kw_set, "keywordThesaurus").text = "Florida managed areas"

    rights = etree.SubElement(dataset, "intellectualRights")
    rights_text = meta.fields.get("Rights") or (
        "Neither the State of Florida nor the Florida Department of Environmental Protection makes any "
        "warranty, expressed or implied, and assumes no legal liability for the accuracy, completeness, "
        "or usefulness of this data."
    )
    _para(rights, rights_text)

    coverage = etree.SubElement(dataset, "coverage")
    if bbox:
        geo = etree.SubElement(coverage, "geographicCoverage")
        etree.SubElement(geo, "geographicDescription").text = ", ".join(meta.managed_areas) or meta.title
        bc = etree.SubElement(geo, "boundingCoordinates")
        etree.SubElement(bc, "westBoundingCoordinate").text = str(bbox["west"])
        etree.SubElement(bc, "eastBoundingCoordinate").text = str(bbox["east"])
        etree.SubElement(bc, "northBoundingCoordinate").text = str(bbox["north"])
        etree.SubElement(bc, "southBoundingCoordinate").text = str(bbox["south"])
    if date_range:
        temporal = etree.SubElement(coverage, "temporalCoverage")
        rod = etree.SubElement(temporal, "rangeOfDates")
        begin = etree.SubElement(rod, "beginDate")
        etree.SubElement(begin, "calendarDate").text = str(date_range["start"])
        end = etree.SubElement(rod, "endDate")
        etree.SubElement(end, "calendarDate").text = str(date_range["end"])

    contact_el = etree.SubElement(dataset, "contact")
    if meta.contacts:
        c = meta.contacts[0]
        name_parts = c.name.rsplit(" ", 1)
        individual = etree.SubElement(contact_el, "individualName")
        if len(name_parts) == 2:
            etree.SubElement(individual, "givenName").text = name_parts[0]
            etree.SubElement(individual, "surName").text = name_parts[1]
        else:
            etree.SubElement(individual, "surName").text = c.name
        if c.email:
            etree.SubElement(contact_el, "electronicMailAddress").text = c.email
    else:
        etree.SubElement(contact_el, "organizationName").text = meta.organization

    if meta.methods:
        methods = etree.SubElement(dataset, "methods")
        step = etree.SubElement(methods, "methodStep")
        description = etree.SubElement(step, "description")
        _para(description, meta.methods)

    additional = etree.SubElement(root, "additionalMetadata")
    md = etree.SubElement(additional, "metadata")
    gbif = etree.SubElement(md, "gbif")
    if meta.citation:
        etree.SubElement(gbif, "citation").text = meta.citation
    for label, value in record_counts.items():
        comment = etree.Comment(f" {label}: {value} ")
        additional.append(comment)

    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", pretty_print=True)
