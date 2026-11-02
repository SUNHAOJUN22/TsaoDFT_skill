"""A manifest hash never authorizes active SVG or arbitrary embedded bytes."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def validator():
    path = ROOT / "scripts/validate_readme_visuals.py"
    spec = importlib.util.spec_from_file_location("localized_art_validator", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_frozen_artwork_is_safe_and_hash_bound():
    assert validator().validate_localized_art(ROOT) == []


@pytest.mark.parametrize(
    "addition",
    [
        "<script>alert(1)</script>",
        "<foreignObject><div>active HTML</div></foreignObject>",
        '<rect onload="alert(1)"/>',
        '<use href="https://example.invalid/remote.svg#glyph"/>',
        '<rect fill="url(https://example.invalid/paint.svg)"/>',
        '<image href="data:image/svg+xml;base64,PHN2Zz4="/>',
    ],
)
def test_rehashed_manifest_cannot_authorize_active_or_extra_content(tmp_path, addition):
    module = validator()
    shutil.copytree(ROOT / "docs/assets/readme-vnext", tmp_path / "docs/assets/readme-vnext")
    manifest_path = tmp_path / module.ART_MANIFEST
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["implementation_references"] = []
    entry = manifest["localized_assets"][0]
    path = tmp_path / entry["path"]
    changed = path.read_text(encoding="utf-8").replace("</svg>", addition + "</svg>").encode("utf-8")
    path.write_bytes(changed)
    entry.update(bytes=len(changed), sha256=hashlib.sha256(changed).hexdigest())
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    assert module.validate_localized_art(tmp_path)


def test_unannounced_asset_change_is_detected(tmp_path):
    module = validator()
    shutil.copytree(ROOT / "docs/assets/readme-vnext", tmp_path / "docs/assets/readme-vnext")
    path = tmp_path / module.LOCALIZED_HEROES["en"]
    path.write_bytes(path.read_bytes() + b"\n")
    assert any("hash/size mismatch" in error for error in module.validate_localized_art(tmp_path))
