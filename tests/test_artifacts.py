from pathlib import Path

from microalpha.artifacts import atomic_write_json, reproducibility_manifest, sha256_file


def test_complete_manifest_hashes_real_artifacts(tmp_path: Path) -> None:
    run = tmp_path / "run"
    run.mkdir()
    atomic_write_json(run / "metrics.json", {"value": 1})
    lock = tmp_path / "requirements.lock"
    lock.write_text("package==1\n", encoding="utf-8")
    manifest = reproducibility_manifest(
        run_id="r1",
        root=tmp_path,
        run_dir=run,
        lockfile=lock,
        source_hashes={"message": "a" * 64},
        seed=42,
        parameters={"horizon": 10},
    )
    assert manifest["dependency_lock_sha256"] == sha256_file(lock)
    assert manifest["artifact_sha256"]["metrics.json"] == sha256_file(run / "metrics.json")
    assert "git_sha" in manifest and "git_dirty" in manifest
    assert manifest["git_sha"] is None
    assert manifest["python_version"]
