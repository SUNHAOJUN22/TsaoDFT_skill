from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_validator():
    path = ROOT / "scripts" / "validate_secrets.py"
    spec = importlib.util.spec_from_file_location("tsao_validate_secrets", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validator = load_validator()


class SecretScannerTests(unittest.TestCase):
    def test_current_repository_has_no_high_confidence_secret(self):
        self.assertEqual(validator.validate(ROOT), [])

    def test_private_key_and_token_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            private_header = "-----BEGIN " + "PRIVATE KEY-----\n"
            synthetic_token = "github_" + "pat_" + "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_ABCDEFGHIJKLMNOPQRSTUVWXYZ\n"
            (root / "example.md").write_text(private_header + synthetic_token, encoding="utf-8")
            failures = validator.validate(root)
            self.assertTrue(any("private-key" in item for item in failures), failures)
            self.assertTrue(any("github-token" in item for item in failures), failures)

    def test_secret_bearing_filename_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / ".env").write_text("PLACEHOLDER=true\n", encoding="utf-8")
            failures = validator.validate(root)
            self.assertTrue(any("secret-bearing filename" in item for item in failures), failures)

    def test_arbitrary_large_text_still_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "large.svg").write_text("x" * (validator.MAX_TEXT_BYTES + 1), encoding="utf-8")
            self.assertTrue(any("too large" in item for item in validator.validate(root)))

    def test_hash_verified_art_still_scans_non_png_content(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(ROOT / "docs/assets/readme-vnext", root / "docs/assets/readme-vnext")
            manifest_path = root / "docs/assets/readme-vnext/artwork-provenance.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["implementation_references"] = []
            item = manifest["localized_assets"][0]
            art = root / item["path"]
            synthetic_key = "-----BEGIN " + "PRIVATE KEY-----"
            changed = art.read_text(encoding="utf-8").replace("</desc>", synthetic_key + "</desc>").encode("utf-8")
            art.write_bytes(changed)
            item.update(bytes=len(changed), sha256=hashlib.sha256(changed).hexdigest())
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            failures = validator.validate(root)
            self.assertTrue(any("private-key" in item for item in failures), failures)

    def test_tampered_governed_art_does_not_bypass_size_limit(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            art = root / "docs/assets/readme-vnext/hero.en.svg"
            art.parent.mkdir(parents=True)
            art.write_text("x" * (validator.MAX_TEXT_BYTES + 1), encoding="utf-8")
            self.assertTrue(any("too large" in item for item in validator.validate(root)))


if __name__ == "__main__":
    unittest.main()
