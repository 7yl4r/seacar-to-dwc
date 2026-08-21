"""Download a program's standardized-export zip and extract it into 01_raw."""
from __future__ import annotations

import logging
import zipfile
from dataclasses import dataclass
from pathlib import Path

import requests

logger = logging.getLogger(__name__)


@dataclass
class RawDataset:
    program_id: str
    dir: Path       # data/01_raw/<program_id>/
    txt_path: Path  # the pipe-delimited export
    xlsx_path: Path  # SEACAR_Metadata.xlsx


def fetch(program_id: str, zip_url: str, raw_dir: Path, session: requests.Session | None = None, timeout: int = 60) -> RawDataset:
    """Download `zip_url` and extract it under raw_dir/<program_id>/.

    Idempotent: if the target directory already has a .txt and .xlsx, skips
    the network call entirely (SEACAR exports are re-downloaded deliberately,
    not on every pipeline run -- delete the directory to force a re-fetch).
    """
    session = session or requests.Session()
    program_dir = raw_dir / str(program_id)
    program_dir.mkdir(parents=True, exist_ok=True)

    existing_txt = list(program_dir.glob("*.txt"))
    existing_xlsx = list(program_dir.glob("*.xlsx"))
    if existing_txt and existing_xlsx:
        logger.info("raw data for program %s already present, skipping download", program_id)
        return RawDataset(program_id=str(program_id), dir=program_dir, txt_path=existing_txt[0], xlsx_path=existing_xlsx[0])

    zip_path = program_dir / f"{program_id}.zip"
    logger.info("downloading %s", zip_url)
    resp = session.get(zip_url, timeout=timeout)
    resp.raise_for_status()
    zip_path.write_bytes(resp.content)

    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(program_dir)
    zip_path.unlink()

    txt_files = list(program_dir.glob("*.txt"))
    xlsx_files = list(program_dir.glob("*.xlsx"))
    if not txt_files:
        raise FileNotFoundError(f"no .txt file found in extracted archive for program {program_id}")
    if not xlsx_files:
        raise FileNotFoundError(f"no .xlsx metadata file found in extracted archive for program {program_id}")

    return RawDataset(program_id=str(program_id), dir=program_dir, txt_path=txt_files[0], xlsx_path=xlsx_files[0])
