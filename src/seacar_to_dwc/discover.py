"""Scrape a SEACAR program details page for its metadata and download links.

Example page: https://data.florida-seacar.org/programs/details/570

The page is server-rendered HTML (ASP.NET), not a JS app, so plain requests +
lxml is enough -- no headless browser needed. Layout verified against program
570 on 2026-08-21; re-check the xpaths in `discover()` if SEACAR changes their
template and this starts returning empty fields.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import urljoin

import requests
from lxml import html

BASE_URL = "https://data.florida-seacar.org"
PROGRAM_URL_TMPL = f"{BASE_URL}/programs/details/{{program_id}}"


@dataclass
class Contact:
    name: str
    role: str | None
    email: str | None
    phone: str | None


@dataclass
class DownloadLink:
    label: str
    url: str


@dataclass
class ProgramMetadata:
    program_id: str
    title: str
    organization: str
    managed_areas: list[str]
    contacts: list[Contact]
    fields: dict[str, str]  # every dt/dd pair on the page, keyed by label as-shown
    dataset_zip_url: str | None  # the "standardized data" export -- what parse.py consumes
    metadata_xlsx_url: str | None  # SEACAR_Metadata.xlsx (also bundled inside dataset_zip_url)
    supplementary_files: list[DownloadLink] = field(default_factory=list)
    source_url: str = ""

    @property
    def summary(self) -> str | None:
        return self.fields.get("Summary")

    @property
    def citation(self) -> str | None:
        return self.fields.get("SEACAR Citation")

    @property
    def methods(self) -> str | None:
        return self.fields.get("Method")

    @property
    def date_start(self) -> str | None:
        return self.fields.get("Start")

    @property
    def date_end(self) -> str | None:
        return self.fields.get("End")


def _text(el) -> str:
    return " ".join(el.text_content().split())


def discover(program_id: int | str, session: requests.Session | None = None, timeout: int = 30) -> ProgramMetadata:
    session = session or requests.Session()
    url = PROGRAM_URL_TMPL.format(program_id=program_id)
    resp = session.get(url, timeout=timeout)
    resp.raise_for_status()
    tree = html.fromstring(resp.content)

    h1 = tree.xpath('//h1[contains(@class,"page-title")]')
    title = " ".join("".join(h1[0].xpath("text()")).split()) if h1 else ""

    subtitle = tree.xpath('//h5[contains(@class,"page-subtitle")]')
    organization = _text(subtitle[0]) if subtitle else ""

    fields: dict[str, str] = {}
    for dt in tree.xpath("//dl//dt"):
        label = _text(dt)
        dd = dt.getnext()
        fields[label] = _text(dd) if dd is not None else ""

    managed_areas: list[str] = []
    for heading in tree.xpath('//h2[contains(.,"Managed Areas")]'):
        panel_body = heading.xpath(
            './ancestor::div[contains(concat(" ", normalize-space(@class), " "), " panel ")][1]'
            '//div[contains(@class,"panel-body")]'
        )
        if panel_body:
            text = _text(panel_body[0])
            managed_areas = [a.strip() for a in text.split(",") if a.strip()]
        break

    contacts: list[Contact] = []
    for card in tree.xpath('//div[contains(@class,"card-block")]'):
        name_el = card.xpath('.//h5[contains(@class,"card-title")]')
        if not name_el:
            continue
        name = _text(name_el[0])
        role_el = card.xpath('.//p[contains(@class,"card-text") and contains(@class,"grey-500")]')
        role = _text(role_el[0]) if role_el else None
        email_el = card.xpath('.//a[starts-with(@href,"mailto:")]/@href')
        email = email_el[0].replace("mailto:", "").strip() if email_el else None
        phone_el = card.xpath('.//a[starts-with(@href,"tel:")]/@href')
        phone = phone_el[0].replace("tel:", "").strip() if phone_el else None
        contacts.append(Contact(name=name, role=role, email=email, phone=phone))

    dataset_zip_url = None
    metadata_xlsx_url = None
    supplementary: list[DownloadLink] = []
    for a in tree.xpath('//a[contains(@class,"file-download")]'):
        dsp_url = a.get("data-dsp-url")
        if not dsp_url:
            continue
        label = _text(a) or dsp_url.rsplit("/", 1)[-1]
        full_url = urljoin(BASE_URL, dsp_url)
        if "/static/datadownload/" in dsp_url:
            dataset_zip_url = full_url
        else:
            supplementary.append(DownloadLink(label=label, url=full_url))

    xlsx_hrefs = tree.xpath('//a[contains(@href,"/static/metadataexport/")]/@href')
    if xlsx_hrefs:
        metadata_xlsx_url = urljoin(BASE_URL, xlsx_hrefs[0])

    return ProgramMetadata(
        program_id=str(program_id),
        title=title,
        organization=organization,
        managed_areas=managed_areas,
        contacts=contacts,
        fields=fields,
        dataset_zip_url=dataset_zip_url,
        metadata_xlsx_url=metadata_xlsx_url,
        supplementary_files=supplementary,
        source_url=url,
    )
