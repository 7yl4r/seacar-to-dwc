"""End-to-end orchestration: discover -> fetch -> parse -> transform -> archive.

    python -m seacar_to_dwc.pipeline 570
    python -m seacar_to_dwc.pipeline --all          # every entry in config/datasets.yaml
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path

import yaml

from . import archive, discover, fetch, parse, taxonomy, worms
from .eml import build_eml
from .transform.emof import build_emof
from .transform.event import build_events
from .transform.occurrence import build_occurrences

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_ROOT = REPO_ROOT / "data"
DEFAULT_CONFIG_ROOT = REPO_ROOT / "config"


def _record_counts(event_df, occurrence_df, emof_df) -> dict:
    return {
        "events": len(event_df),
        "occurrences": len(occurrence_df),
        "measurementOrFacts": len(emof_df),
    }


def _bbox(event_df) -> dict | None:
    lat = event_df["decimalLatitude"].dropna()
    lon = event_df["decimalLongitude"].dropna()
    if lat.empty or lon.empty:
        return None
    return {"south": lat.min(), "north": lat.max(), "west": lon.min(), "east": lon.max()}


def _date_range(event_df) -> dict | None:
    dates = event_df["eventDate"].dropna()
    if dates.empty:
        return None
    return {"start": dates.min(), "end": dates.max()}


def run_pipeline(program_id: int | str, data_root: Path = DEFAULT_DATA_ROOT, config_root: Path = DEFAULT_CONFIG_ROOT) -> Path:
    program_id = str(program_id)
    logger.info("=== program %s: discover ===", program_id)
    meta = discover.discover(program_id)
    if not meta.dataset_zip_url:
        raise RuntimeError(f"program {program_id}: no standardized-export zip link found on {meta.source_url}")

    logger.info("=== program %s: fetch ===", program_id)
    raw = fetch.fetch(program_id, meta.dataset_zip_url, raw_dir=data_root / "01_raw")

    logger.info("=== program %s: parse ===", program_id)
    df = parse.parse(raw.txt_path)

    interim_dir = data_root / "02_interim"
    interim_dir.mkdir(parents=True, exist_ok=True)
    df.to_parquet(interim_dir / f"{program_id}.parquet", index=False)

    logger.info("=== program %s: taxonomy ===", program_id)
    species_ref = taxonomy.load_species_reference(raw.xlsx_path)

    with open(config_root / "measurement_vocab.yaml") as f:
        vocab = yaml.safe_load(f)

    logger.info("=== program %s: WoRMS scientificNameID lookup ===", program_id)
    query_names = {
        taxonomy.worms_query_name(taxonomy.lookup(species_ref, sid))
        for sid in df["SpeciesID"].unique()
    }
    query_names.discard(None)
    lsids = worms.resolve_lsids(query_names, cache_path=data_root / "03_taxonomy_cache" / "worms_lsids.json")

    logger.info("=== program %s: transform ===", program_id)
    event_df = build_events(df)
    occurrence_df = build_occurrences(df, species_ref, vocab, lsids=lsids)
    emof_df = build_emof(df, species_ref, vocab)

    processed_dir = data_root / "04_processed" / program_id
    processed_dir.mkdir(parents=True, exist_ok=True)
    event_df.to_csv(processed_dir / "event.csv", index=False)
    occurrence_df.to_csv(processed_dir / "occurrence.csv", index=False)
    emof_df.to_csv(processed_dir / "emof.csv", index=False)

    logger.info("=== program %s: eml ===", program_id)
    eml_bytes = build_eml(
        meta,
        bbox=_bbox(event_df),
        date_range=_date_range(event_df),
        record_counts=_record_counts(event_df, occurrence_df, emof_df),
    )

    logger.info("=== program %s: archive ===", program_id)
    archive_dir = data_root / "05_archive" / program_id
    zip_path = archive.assemble_archive(
        archive_dir, event_df, occurrence_df, emof_df, eml_bytes,
        archive_name=f"seacar-{program_id}-dwca",
    )
    logger.info("program %s: archive ready at %s", program_id, zip_path)
    return zip_path


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("program_id", nargs="?", help="SEACAR program ID, e.g. 570")
    ap.add_argument("--all", action="store_true", help="run every dataset listed in config/datasets.yaml")
    ap.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    ap.add_argument("--config-root", type=Path, default=DEFAULT_CONFIG_ROOT)
    args = ap.parse_args()

    if args.all:
        with open(args.config_root / "datasets.yaml") as f:
            datasets = yaml.safe_load(f)["datasets"]
        for entry in datasets:
            run_pipeline(entry["program_id"], args.data_root, args.config_root)
    elif args.program_id:
        run_pipeline(args.program_id, args.data_root, args.config_root)
    else:
        ap.error("pass a program_id or --all")


if __name__ == "__main__":
    main()
