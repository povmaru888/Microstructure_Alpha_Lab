"""Artifact hashing and safe serialization helpers."""

import csv
import hashlib
import json
import os
import platform
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from microalpha.config import SourceConfig


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    """Return a streaming SHA-256 digest, failing clearly for missing files."""
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"required input file does not exist: {source}")
    digest = hashlib.sha256()
    with source.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def csv_row_count(path: str | Path) -> int:
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"required input file does not exist: {source}")
    with source.open(newline="", encoding="utf-8") as stream:
        return sum(1 for row in csv.reader(stream) if row)


def build_data_manifest(
    source: SourceConfig,
    *,
    source_page: str,
    license_note: str,
    expected_hashes: dict[str, str] | None = None,
    downloaded_at_utc: str | None = None,
) -> dict[str, Any]:
    """Build provenance from actual files; optionally verify expected hashes."""
    files: dict[str, dict[str, Any]] = {}
    paths = {"message": source.message_path, "orderbook": source.orderbook_path}
    for role, path in paths.items():
        digest = sha256_file(path)
        if expected_hashes and role in expected_hashes and digest != expected_hashes[role]:
            raise ValueError(f"SHA-256 mismatch for {role}: expected {expected_hashes[role]}")
        files[role] = {
            "local_path": str(path),
            "original_filename": path.name,
            "sha256": digest,
            "rows": csv_row_count(path),
        }
    return {
        "schema_version": "1.0",
        "dataset_id": source.dataset_id,
        "provider": source.provider.upper(),
        "symbol": source.symbol,
        "trade_date": source.trade_date.isoformat(),
        "levels": source.levels,
        "downloaded_at_utc": downloaded_at_utc,
        "manifest_created_at_utc": datetime.now(UTC).isoformat(),
        "source_page": source_page,
        "license_note": license_note,
        "files": files,
    }


def atomic_write_json(path: str | Path, payload: Any) -> None:
    """Atomically replace a JSON artifact in the destination directory."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.", dir=destination.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(destination)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def atomic_write_parquet(path: str | Path, frame: pd.DataFrame) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    handle, name = tempfile.mkstemp(prefix=f".{destination.name}.", dir=destination.parent)
    os.close(handle)
    temporary = Path(name)
    try:
        frame.to_parquet(temporary, index=False)
        temporary.replace(destination)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def atomic_dump_joblib(path: str | Path, value: Any) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    handle, name = tempfile.mkstemp(prefix=f".{destination.name}.", dir=destination.parent)
    os.close(handle)
    temporary = Path(name)
    try:
        joblib.dump(value, temporary)
        temporary.replace(destination)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def repository_state(root: str | Path) -> dict[str, Any]:
    try:
        sha = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
        ).stdout.strip()
        dirty = bool(
            subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        )
        return {"git_sha": sha, "git_dirty": dirty}
    except (OSError, subprocess.SubprocessError):
        return {"git_sha": None, "git_dirty": None}


def artifact_hashes(directory: str | Path) -> dict[str, str]:
    root = Path(directory)
    return {
        str(path.relative_to(root)): sha256_file(path)
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.name != "run_manifest.json"
    }


def reproducibility_manifest(
    *,
    run_id: str,
    root: str | Path,
    run_dir: str | Path,
    lockfile: str | Path,
    source_hashes: dict,
    seed: int,
    parameters: dict,
) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "run_id": run_id,
        "created_at_utc": datetime.now(UTC).isoformat(),
        **repository_state(root),
        "python_version": platform.python_version(),
        "dependency_lock_sha256": sha256_file(lockfile),
        "source_sha256": source_hashes,
        "seed": seed,
        "parameters": parameters,
        "artifact_sha256": artifact_hashes(run_dir),
    }


def refresh_run_manifest(run_dir: str | Path) -> dict[str, Any] | None:
    directory = Path(run_dir)
    path = directory / "run_manifest.json"
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["artifact_sha256"] = artifact_hashes(directory)
    payload["artifacts"] = sorted(payload["artifact_sha256"])
    atomic_write_json(path, payload)
    return payload
