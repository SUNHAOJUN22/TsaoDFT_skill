from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

import pytest


def load_parser():
    path = Path(__file__).resolve().parents[1] / "scripts/engine_parser_contract.py"
    spec = importlib.util.spec_from_file_location("parser_hash_regression", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_hash_interface_returns_checked_sha256(tmp_path: Path) -> None:
    parser = load_parser()
    path = tmp_path / "output.log"
    path.write_bytes(b"reference output")
    assert parser.sha256_file(path) == hashlib.sha256(path.read_bytes()).hexdigest()
    for invalid in (None, b"a" * 64, "short", "G" * 64):
        with (
            patch.object(parser._SCAN, "sha256_file", return_value=invalid),
            pytest.raises((TypeError, ValueError)),
        ):
            parser.sha256_file(path)
