"""Splitting must preserve input data and previous outputs on failure."""

from __future__ import annotations

import csv
import importlib.util
import os
from pathlib import Path
from typing import Any

import pytest

SOURCE = Path(__file__).resolve().parents[1] / "skills/tsao-dft-ml-active-learning/scripts/group_split.py"
SPEC = importlib.util.spec_from_file_location("group_split_publication", SOURCE)
assert SPEC and SPEC.loader
splitter: Any = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(splitter)
PAYLOAD = b"sample_id,parent_id,energy\na,g1,-1\nb,g2,-2\nc,g3,-3\n"


@pytest.mark.parametrize("alias", ["direct", "hardlink", "symlink"])
def test_input_output_alias_fails_before_any_truncation(tmp_path: Path, alias: str) -> None:
    dataset = tmp_path / "train.csv" if alias == "direct" else tmp_path / "source.csv"
    dataset.write_bytes(PAYLOAD)
    output = tmp_path / "train.csv"
    if alias == "hardlink":
        output.hardlink_to(dataset)
    elif alias == "symlink":
        try:
            output.symlink_to(dataset)
        except OSError as exc:
            pytest.skip(f"symlink creation unavailable: {exc}")
    with pytest.raises(ValueError, match=r"input|alias|symlink"):
        splitter.split_dataset(dataset, "parent_id", tmp_path)
    assert dataset.read_bytes() == PAYLOAD
    assert output.read_bytes() == PAYLOAD
    assert not (tmp_path / "valid.csv").exists()
    assert not (tmp_path / "test.csv").exists()


def existing_outputs(root: Path) -> dict[str, bytes]:
    saved = {f"{name}.csv": f"old {name}\n".encode() for name in splitter.SPLITS}
    saved["notes.txt"] = b"unrelated data\n"
    for name, content in saved.items():
        (root / name).write_bytes(content)
    return saved


def assert_preserved(root: Path, saved: dict[str, bytes]) -> None:
    assert {path.name: path.read_bytes() for path in root.iterdir()} == saved


def test_staging_write_failure_preserves_previous_outputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dataset = tmp_path / "source.csv"
    dataset.write_bytes(PAYLOAD)
    outputs = tmp_path / "splits"
    outputs.mkdir()
    saved = existing_outputs(outputs)
    original = csv.DictWriter.writerow

    def fail_on_second_row(self, row):
        if row.get("sample_id") == "b":
            raise OSError("injected disk write failure")
        return original(self, row)

    monkeypatch.setattr(csv.DictWriter, "writerow", fail_on_second_row)
    with pytest.raises(OSError, match="injected"):
        splitter.split_dataset(dataset, "parent_id", outputs)
    assert dataset.read_bytes() == PAYLOAD
    assert_preserved(outputs, saved)


def test_output_alias_collision_is_rejected(tmp_path: Path) -> None:
    dataset = tmp_path / "source.csv"
    dataset.write_bytes(PAYLOAD)
    outputs = tmp_path / "splits"
    outputs.mkdir()
    (outputs / "train.csv").write_bytes(b"old shared output\n")
    (outputs / "valid.csv").hardlink_to(outputs / "train.csv")
    with pytest.raises(ValueError, match=r"alias|collision"):
        splitter.split_dataset(dataset, "parent_id", outputs)
    assert (outputs / "train.csv").read_bytes() == b"old shared output\n"
    assert (outputs / "valid.csv").read_bytes() == b"old shared output\n"
    assert not (outputs / "test.csv").exists()


@pytest.mark.parametrize("previous_outputs", [True, False])
def test_publication_failure_restores_entire_previous_set(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, previous_outputs: bool
) -> None:
    dataset = tmp_path / "source.csv"
    dataset.write_bytes(PAYLOAD)
    outputs = tmp_path / "splits"
    outputs.mkdir()
    saved = existing_outputs(outputs) if previous_outputs else {}
    replace = os.replace
    injected = False

    def fail_once(source, target):
        nonlocal injected
        if Path(target) == outputs / "valid.csv" and not injected:
            injected = True
            raise OSError("injected publication failure")
        return replace(source, target)

    monkeypatch.setattr(os, "replace", fail_once)
    with pytest.raises(OSError, match="injected"):
        splitter.split_dataset(dataset, "parent_id", outputs)
    assert dataset.read_bytes() == PAYLOAD
    assert_preserved(outputs, saved)


def test_normal_replacement_retains_all_records_and_unrelated_files(tmp_path: Path) -> None:
    dataset = tmp_path / "source.csv"
    dataset.write_bytes(PAYLOAD)
    outputs = tmp_path / "splits"
    outputs.mkdir()
    existing_outputs(outputs)
    report = splitter.split_dataset(dataset, "parent_id", outputs)
    rows: list[dict[str, str]] = []
    for name in splitter.SPLITS:
        with (outputs / f"{name}.csv").open(encoding="utf-8", newline="") as stream:
            rows.extend(csv.DictReader(stream))
    assert sorted(row["sample_id"] for row in rows) == ["a", "b", "c"]
    assert sum(report["row_counts"].values()) == report["row_count"] == 3
    assert dataset.read_bytes() == PAYLOAD
    assert (outputs / "notes.txt").read_bytes() == b"unrelated data\n"


@pytest.mark.skipif(os.name != "posix", reason="POSIX permission-bit contract; Windows ACLs need separate validation")
@pytest.mark.parametrize("mode", [0o600, 0o640])
def test_successful_replacement_preserves_existing_output_permissions(tmp_path: Path, mode: int) -> None:
    dataset = tmp_path / "source.csv"
    dataset.write_bytes(PAYLOAD)
    outputs = tmp_path / "splits"
    outputs.mkdir()
    existing_outputs(outputs)
    for name in splitter.SPLITS:
        (outputs / f"{name}.csv").chmod(mode)

    splitter.split_dataset(dataset, "parent_id", outputs)

    assert {((outputs / f"{name}.csv").stat().st_mode & 0o777) for name in splitter.SPLITS} == {mode}


def test_active_writer_lock_preserves_previous_outputs(tmp_path: Path) -> None:
    dataset = tmp_path / "source.csv"
    dataset.write_bytes(PAYLOAD)
    outputs = tmp_path / "splits"
    outputs.mkdir()
    saved = existing_outputs(outputs)
    saved[".group-split.lock"] = b"existing writer\n"
    (outputs / ".group-split.lock").write_bytes(saved[".group-split.lock"])
    with pytest.raises(FileExistsError):
        splitter.split_dataset(dataset, "parent_id", outputs)
    assert_preserved(outputs, saved)


def test_failed_rollback_retains_old_data_for_recovery(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dataset = tmp_path / "source.csv"
    dataset.write_bytes(PAYLOAD)
    outputs = tmp_path / "splits"
    outputs.mkdir()
    saved = existing_outputs(outputs)
    replace = os.replace

    def fail_publication_and_rollback(source, target):
        if Path(target) == outputs / "valid.csv" or Path(source).suffix == ".backup":
            raise OSError("injected persistent IO failure")
        return replace(source, target)

    monkeypatch.setattr(os, "replace", fail_publication_and_rollback)
    with pytest.raises(OSError, match="recovery files retained"):
        splitter.split_dataset(dataset, "parent_id", outputs)
    stages = [path for path in outputs.iterdir() if path.is_dir()]
    assert len(stages) == 1
    for name in splitter.SPLITS:
        assert (stages[0] / f"{name}.backup").read_bytes() == saved[f"{name}.csv"]
    assert dataset.read_bytes() == PAYLOAD
    assert (outputs / "notes.txt").read_bytes() == saved["notes.txt"]


def test_input_change_between_passes_does_not_publish_partial_splits(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dataset = tmp_path / "source.csv"
    dataset.write_bytes(PAYLOAD)
    outputs = tmp_path / "splits"
    outputs.mkdir()
    saved = existing_outputs(outputs)
    scan = splitter.scan_groups

    def scan_then_change(path, group):
        result = scan(path, group)
        path.write_bytes(PAYLOAD.splitlines(keepends=True)[0])
        return result

    monkeypatch.setattr(splitter, "scan_groups", scan_then_change)
    with pytest.raises(ValueError, match="row count changed"):
        splitter.split_dataset(dataset, "parent_id", outputs)
    assert_preserved(outputs, saved)
