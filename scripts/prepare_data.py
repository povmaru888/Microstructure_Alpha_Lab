#!/usr/bin/env python3
"""Prepare data artifacts. The manifest stage is independently runnable."""

import argparse
import sys
from pathlib import Path

from pydantic import ValidationError

from microalpha.artifacts import atomic_write_json, atomic_write_parquet, build_data_manifest
from microalpha.config import load_settings
from microalpha.features import compute_features
from microalpha.ingest import ingest_lobster
from microalpha.validate import validate_lobster


def prepare(
    settings,
    output_dir: Path,
    *,
    source_page: str,
    license_note: str,
    downloaded_at_utc: str | None = None,
) -> dict:
    manifest = build_data_manifest(
        settings.source,
        source_page=source_page,
        license_note=license_note,
        downloaded_at_utc=downloaded_at_utc,
    )
    events, books = ingest_lobster(settings.source)
    validated, quality_report = validate_lobster(events, books, settings.source, settings.quality)
    features = compute_features(validated, settings.features)
    output_dir.mkdir(parents=True, exist_ok=True)
    atomic_write_json(output_dir / "data_manifest.json", manifest)
    atomic_write_json(output_dir / "quality_report.json", quality_report)
    atomic_write_parquet(output_dir / "validated.parquet", validated)
    atomic_write_parquet(output_dir / "features.parquet", features)
    metadata = {
        "schema_version": "1.0",
        "feature_version": "1.0",
        "dataset_id": settings.source.dataset_id,
        "source_sha256": {key: value["sha256"] for key, value in manifest["files"].items()},
        "rows": len(features),
        "columns": list(features.columns),
    }
    atomic_write_json(output_dir / "features_metadata.json", metadata)
    return metadata


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/data"))
    parser.add_argument("--source-page", required=True)
    parser.add_argument("--license-note", required=True)
    parser.add_argument("--downloaded-at-utc")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        settings = load_settings(args.config)
        if args.dry_run:
            build_data_manifest(
                settings.source, source_page=args.source_page, license_note=args.license_note
            )
        else:
            prepare(
                settings,
                args.output_dir,
                source_page=args.source_page,
                license_note=args.license_note,
                downloaded_at_utc=args.downloaded_at_utc,
            )
    except (FileNotFoundError, ValueError, ValidationError) as error:
        print(f"configuration/data error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
