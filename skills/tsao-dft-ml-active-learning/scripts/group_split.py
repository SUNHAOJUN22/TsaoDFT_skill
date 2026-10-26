#!/usr/bin/env python3
"""Create deterministic group-disjoint CSV splits with bounded row memory."""

from __future__ import annotations

import argparse
import contextlib
import csv
import hashlib
import json
import math
import os
import shutil
import tempfile
from pathlib import Path

SPLITS = ("train", "valid", "test")


def file_identity(path: Path) -> tuple[int, int, int, int, int] | None:
    try:
        info = path.stat()
    except FileNotFoundError:
        return None
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns


def output_paths(dataset: Path, out_dir: Path) -> dict[str, Path]:
    """Reject destructive aliases before opening any output for writing."""
    targets = {name: out_dir / f"{name}.csv" for name in SPLITS}
    checked: list[Path] = []
    for target in targets.values():
        if target.resolve() == dataset.resolve() or (target.exists() and target.samefile(dataset)):
            raise ValueError(f"split output aliases input dataset: {target}")
        if target.is_symlink():
            raise ValueError(f"split output must not be a symlink: {target}")
        if target.exists():
            if not target.is_file():
                raise ValueError(f"split output is not a regular file: {target}")
            if any(previous.exists() and target.samefile(previous) for previous in checked):
                raise ValueError(f"split output alias collision: {target}")
        checked.append(target)
    return targets


def bucket(group: str) -> float:
    return int(hashlib.sha256(group.encode()).hexdigest()[:12], 16) / float(16**12)


def split_name(group: str, train: float, valid: float) -> str:
    value = bucket(group)
    return "train" if value < train else "valid" if value < train + valid else "test"


def validate_fractions(train: float, valid: float) -> None:
    if not math.isfinite(train) or not math.isfinite(valid):
        raise ValueError("split fractions must be finite")
    if train <= 0 or train >= 1:
        raise ValueError("train fraction must be between 0 and 1")
    if valid < 0 or valid >= 1:
        raise ValueError("valid fraction must be between 0 and 1")
    if train + valid >= 1:
        raise ValueError("train + valid must be less than 1")


def scan_groups(path: Path, group_column: str) -> tuple[list[str], set[str], int]:
    groups: set[str] = set()
    row_count = 0
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("dataset is missing a CSV header")
        fieldnames = list(reader.fieldnames)
        if group_column not in fieldnames:
            raise ValueError(f"missing group column {group_column}")
        for line_number, row in enumerate(reader, start=2):
            if None in row:
                raise ValueError(f"row {line_number} has more fields than the CSV header")
            group = row.get(group_column)
            if group is None or not group:
                raise ValueError(f"row {line_number} has an empty group value")
            groups.add(group)
            row_count += 1
    if row_count == 0:
        raise ValueError("dataset is empty")
    return fieldnames, groups, row_count


def write_splits(
    dataset: Path,
    out_dir: Path,
    fieldnames: list[str],
    assignment: dict[str, str],
    group_column: str,
    *,
    expected_row_count: int | None = None,
) -> dict[str, int]:
    targets = output_paths(dataset, out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    lock = out_dir / ".group-split.lock"
    # Cooperative writers fail closed instead of replacing each other's files.
    lock.touch(exist_ok=False)
    try:
        return stage_splits(dataset, out_dir, targets, fieldnames, assignment, group_column, expected_row_count)
    finally:
        lock.unlink()


def stage_splits(
    dataset: Path,
    out_dir: Path,
    targets: dict[str, Path],
    fieldnames: list[str],
    assignment: dict[str, str],
    group_column: str,
    expected_row_count: int | None,
) -> dict[str, int]:
    stage = Path(tempfile.mkdtemp(prefix=".group-split-", dir=out_dir))
    retain_stage = False
    try:
        source_identity = file_identity(dataset)
        previous = {name: file_identity(path) for name, path in targets.items()}
        with contextlib.ExitStack() as stack:
            handles = {
                name: stack.enter_context((stage / f"{name}.csv").open("w", newline="", encoding="utf-8"))
                for name in SPLITS
            }
            writers = {name: csv.DictWriter(handles[name], fieldnames=fieldnames) for name in SPLITS}
            for writer in writers.values():
                writer.writeheader()
            row_counts = {name: 0 for name in SPLITS}
            with dataset.open(encoding="utf-8", newline="") as source:
                reader = csv.DictReader(source)
                if reader.fieldnames != fieldnames:
                    raise ValueError("dataset header changed between split passes")
                for row in reader:
                    group = row.get(group_column)
                    if None in row or group not in assignment:
                        raise ValueError("dataset rows changed between split passes")
                    name = assignment[group]
                    writers[name].writerow(row)
                    row_counts[name] += 1
        if source_identity != file_identity(dataset):
            raise ValueError("dataset changed while staging splits")
        if expected_row_count is not None and sum(row_counts.values()) != expected_row_count:
            raise ValueError("dataset row count changed between split passes")
        output_paths(dataset, out_dir)
        for name, target in targets.items():
            if file_identity(target) != previous[name]:
                raise ValueError(f"split output changed while staging: {target}")
            if previous[name] is not None:
                # os.replace publishes the staged inode, so preserve metadata
                # from an existing output rather than widening its permissions
                # to the process umask defaults (commonly 0644).
                shutil.copystat(target, stage / f"{name}.csv", follow_symlinks=False)
                shutil.copy2(target, stage / f"{name}.backup")
        published: dict[str, tuple[int, int, int, int, int] | None] = {}
        try:
            for name, target in targets.items():
                if file_identity(target) != previous[name]:
                    raise ValueError(f"split output changed before publication: {target}")
                os.replace(stage / f"{name}.csv", target)
                published[name] = file_identity(target)
        except BaseException:
            try:
                for name, installed_identity in reversed(list(published.items())):
                    target = targets[name]
                    if file_identity(target) != installed_identity:
                        raise OSError(f"published output changed before rollback: {target}")
                    if previous[name] is None:
                        target.unlink()
                    else:
                        os.replace(stage / f"{name}.backup", target)
            except OSError as rollback_error:
                retain_stage = True
                raise OSError(
                    f"split rollback incomplete; recovery files retained at {stage}: {rollback_error}"
                ) from rollback_error
            raise
        return row_counts
    finally:
        if not retain_stage:
            shutil.rmtree(stage)


def split_dataset(
    dataset: Path,
    group_column: str,
    out_dir: Path,
    train: float = 0.7,
    valid: float = 0.15,
) -> dict[str, object]:
    validate_fractions(train, valid)
    fieldnames, groups, row_count = scan_groups(dataset, group_column)
    assignment = {group: split_name(group, train, valid) for group in sorted(groups)}
    row_counts = write_splits(dataset, out_dir, fieldnames, assignment, group_column, expected_row_count=row_count)
    group_counts = {name: sum(value == name for value in assignment.values()) for name in SPLITS}
    return {"row_count": row_count, "row_counts": row_counts, "group_counts": group_counts}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--group", required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--train", type=float, default=0.7)
    parser.add_argument("--valid", type=float, default=0.15)
    args = parser.parse_args()
    try:
        result = split_dataset(args.dataset, args.group, args.out_dir, args.train, args.valid)
    except (OSError, UnicodeError, csv.Error, ValueError) as exc:
        print(json.dumps({"ok": False, "errors": [str(exc)]}, indent=2))
        return 1
    print(result["group_counts"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
