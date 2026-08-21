"""WoRMS (World Register of Marine Species) AphiaID/LSID lookup, cached to disk.

SEACAR's own Ref_Species reference (taxonomy.py) already gives the accepted
scientificName and higher classification, but not the numeric AphiaID --
this resolves dwc:scientificNameID (as an LSID) for that name via WoRMS'
REST API, https://www.marinespecies.org/rest/. Best-effort: a lookup failure
logs a warning and leaves that name's LSID as None rather than failing the
pipeline (occurrence.py falls back to no scientificNameID for that row).
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

API_URL = "https://www.marinespecies.org/rest/AphiaRecordsByMatchNames"


def load_cache(cache_path: Path) -> dict[str, str | None]:
    if cache_path.exists():
        return json.loads(cache_path.read_text())
    return {}


def save_cache(cache_path: Path, cache: dict[str, str | None]) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(cache, indent=2, sort_keys=True))


def resolve_lsids(
    names: set[str], cache_path: Path, session: requests.Session | None = None, timeout: int = 15,
) -> dict[str, str | None]:
    """Return {name: lsid or None}, querying WoRMS only for names not already cached."""
    cache = load_cache(cache_path)
    missing = sorted(n for n in names if n not in cache)
    if not missing:
        return cache

    session = session or requests.Session()
    for name in missing:
        cache[name] = _lookup_one(session, name, timeout)

    save_cache(cache_path, cache)
    return cache


def _lookup_one(session: requests.Session, name: str, timeout: int) -> str | None:
    try:
        resp = session.get(API_URL, params={"scientificnames[]": name, "marine_only": "false"}, timeout=timeout)
        if resp.status_code == 204:  # WoRMS returns 204 No Content when nothing matches
            return None
        resp.raise_for_status()
        data = resp.json()
        matches = data[0] if data else []
        if not matches:
            return None
        accepted = [m for m in matches if m.get("status") == "accepted"]
        chosen = accepted[0] if accepted else matches[0]
        return chosen.get("lsid")
    except Exception as e:
        logger.warning("WoRMS lookup failed for %r: %s", name, e)
        return None
