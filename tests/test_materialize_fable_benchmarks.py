from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "materialize_fable_benchmarks.py"


def load_script_module():
    spec = importlib.util.spec_from_file_location("materialize_fable_benchmarks", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fake_workbook_manifest(sha256: str, size: int) -> dict[str, object]:
    return {
        "benchmark_set": "fable-calculator",
        "source": {"type": "dropbox_folder", "url": "https://example.test/dropbox"},
        "local_directory": "tmp/private-workbooks",
        "workbooks": [
            {
                "filename": "canonical.xlsx",
                "local_path": "tmp/private-workbooks/canonical.xlsx",
                "role": "test",
                "sha256": sha256,
                "bytes": size,
            }
        ],
    }


def test_materialize_from_directory_copies_by_checksum_to_canonical_path(tmp_path: Path) -> None:
    script = load_script_module()
    source_dir = tmp_path / "downloaded"
    repo_root = tmp_path / "repo"
    source_dir.mkdir()
    payload = b"not really an xlsx, but checksum matching is what matters"
    source_file = source_dir / "wrong-name-from-download.xlsx"
    source_file.write_bytes(payload)
    manifest = fake_workbook_manifest(script.sha256_file(source_file), len(payload))

    materialized = script.materialize_from_directory(source_dir, manifest, repo_root)

    destination = repo_root / "tmp" / "private-workbooks" / "canonical.xlsx"
    assert materialized == [destination]
    assert destination.read_bytes() == payload


def test_materialize_from_directory_refuses_wrong_existing_destination(tmp_path: Path) -> None:
    script = load_script_module()
    source_dir = tmp_path / "downloaded"
    repo_root = tmp_path / "repo"
    source_dir.mkdir()
    payload = b"correct workbook payload"
    source_file = source_dir / "downloaded.xlsx"
    source_file.write_bytes(payload)
    manifest = fake_workbook_manifest(script.sha256_file(source_file), len(payload))
    destination = repo_root / "tmp" / "private-workbooks" / "canonical.xlsx"
    destination.parent.mkdir(parents=True)
    destination.write_bytes(b"wrong payload")

    with pytest.raises(script.MaterializationError, match="wrong checksum"):
        script.materialize_from_directory(source_dir, manifest, repo_root)
