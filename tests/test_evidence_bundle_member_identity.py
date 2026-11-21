from __future__ import annotations

import json
import os
import runpy
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills/tsao-dft-hpc-provenance/scripts"
TRUST = runpy.run_path(str(SCRIPTS / "trust_boundary.py"))
MUTATIONS = ["extra-directory", "broken-link", "records-link", "root-link", "bundle-link"]


def _publish(parent: Path) -> dict[str, Any]:
    return TRUST["publish_content_addressed_bundle"](parent, [], {}, {}, {}, {})


def _symlink(link: Path, target: Path, *, directory: bool = False) -> None:
    try:
        link.symlink_to(target, target_is_directory=directory)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symbolic links unavailable: {exc}")


def _mutated_bundle(tmp_path: Path, mutation: str) -> tuple[Path, Path | None]:
    bundle = Path(_publish(tmp_path / "published")["out_dir"])
    external: Path | None = None
    if mutation == "extra-directory":
        (bundle / "unlisted").mkdir()
        (bundle / "unlisted/payload.txt").write_bytes(b"unlisted source evidence")
    elif mutation == "broken-link":
        _symlink(bundle / "unlisted", tmp_path / "absent")
    elif mutation in {"records-link", "root-link"}:
        member = bundle / ("records.json" if mutation == "records-link" else "evidence-root.json")
        external = tmp_path / "external.json"
        external.write_bytes(member.read_bytes())
        member.unlink()
        _symlink(member, external)
    elif mutation == "bundle-link":
        actual = tmp_path / "external-bundle"
        bundle.rename(actual)
        _symlink(bundle, actual, directory=True)
        external = actual / "records.json"
    else:
        raise AssertionError(f"unexpected mutation: {mutation}")
    return bundle, external


@pytest.mark.parametrize("mutation", MUTATIONS)
def test_public_cli_rejects_nonregular_or_unlisted_bundle_entries(tmp_path: Path, mutation: str) -> None:
    bundle, external = _mutated_bundle(tmp_path, mutation)
    before = external.read_bytes() if external is not None else None

    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "verify_evidence_bundle.py"), str(bundle)],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert result.returncode == 1, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report["ok"] is False
    assert report["errors"]
    assert "Traceback" not in result.stderr
    if external is not None:
        assert external.read_bytes() == before


@pytest.mark.parametrize("mutation", MUTATIONS)
def test_publisher_refuses_to_reuse_nonregular_or_unlisted_bundle_entries(tmp_path: Path, mutation: str) -> None:
    bundle, external = _mutated_bundle(tmp_path, mutation)
    before = external.read_bytes() if external is not None else None

    with pytest.raises(ValueError, match="content-addressed target already exists"):
        _publish(tmp_path / "published")

    assert bundle.exists()
    if external is not None:
        assert external.read_bytes() == before
    assert not list((tmp_path / "published").glob(".evidence-stage-*"))


def test_extra_fifo_is_rejected_without_opening_it(tmp_path: Path) -> None:
    if not hasattr(os, "mkfifo"):
        pytest.skip("FIFO files unavailable")
    bundle = Path(_publish(tmp_path / "published")["out_dir"])
    os.mkfifo(bundle / "unlisted-pipe")

    report = TRUST["verify_content_addressed_bundle"](bundle)

    assert report["ok"] is False
    assert report["errors"]


def _custom_bundle(parent: Path, files: dict[str, bytes]) -> Path:
    manifest = TRUST["build_root_manifest"](files)
    root_bytes = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode()
    root_sha = TRUST["sha256_bytes"](root_bytes)
    bundle = parent / f"evidence-{root_sha}"
    bundle.mkdir()
    (bundle / "evidence-root.json").write_bytes(root_bytes)
    return bundle


def test_unlisted_external_path_is_not_hashed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    outside = tmp_path / "outside.json"
    outside.write_bytes(b"outside declared bundle")
    bundle = _custom_bundle(tmp_path, {"../outside.json": outside.read_bytes()})
    verify = TRUST["verify_content_addressed_bundle"]
    original_hash = verify.__globals__["sha256_file"]
    observed: list[Path] = []

    def hash_file(path: Path) -> str:
        observed.append(path.resolve())
        return original_hash(path)

    monkeypatch.setitem(verify.__globals__, "sha256_file", hash_file)

    report = verify(bundle)

    assert report["ok"] is False
    assert outside not in observed


def test_member_removed_after_inventory_returns_a_missing_file_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle = Path(_publish(tmp_path)["out_dir"])
    member = bundle / "records.json"
    original_is_file = Path.is_file
    removed = False

    def observed_then_removed(path: Path) -> bool:
        nonlocal removed
        regular = original_is_file(path)
        if path == member and regular and not removed:
            member.unlink()
            removed = True
        return regular

    monkeypatch.setattr(Path, "is_file", observed_then_removed)

    report = TRUST["verify_content_addressed_bundle"](bundle)

    assert removed
    assert report["ok"] is False
    assert "bundle file is missing: records.json" in report["errors"]


@pytest.mark.parametrize("name", ["measurement 01.json", "测量.json"])
def test_regular_flat_unicode_and_space_members_remain_valid(tmp_path: Path, name: str) -> None:
    content = b"retained source bytes"
    bundle = _custom_bundle(tmp_path, {name: content})
    (bundle / name).write_bytes(content)

    report = TRUST["verify_content_addressed_bundle"](bundle)

    assert report["ok"] is True
    assert report["errors"] == []


def test_regular_published_bundle_can_be_verified_and_reused(tmp_path: Path) -> None:
    first = _publish(tmp_path)
    bundle = Path(first["out_dir"])
    before = {path.name: path.read_bytes() for path in bundle.iterdir()}

    second = _publish(tmp_path)

    assert second["ok"] is True
    assert second["reused"] is True
    assert second["root_sha256"] == first["root_sha256"]
    assert TRUST["verify_content_addressed_bundle"](bundle)["ok"] is True
    assert {path.name: path.read_bytes() for path in bundle.iterdir()} == before
