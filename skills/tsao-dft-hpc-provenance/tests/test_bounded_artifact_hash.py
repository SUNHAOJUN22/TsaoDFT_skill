from __future__ import annotations

import hashlib
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load_parser() -> Any:
    path = ROOT / "scripts" / "engine_parser_contract.py"
    spec = importlib.util.spec_from_file_location("bounded_hash_parser", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BoundedArtifactHashTests(unittest.TestCase):
    parser: Any

    @classmethod
    def setUpClass(cls) -> None:
        cls.parser = load_parser()

    def test_invalid_buffer_is_rejected_before_opening_the_artifact(self) -> None:
        for size in (0, -1, True, False, 1.5, "2", None):
            with (
                self.subTest(chunk_size=size),
                patch.object(Path, "open") as opener,
                self.assertRaisesRegex(ValueError, "positive integer"),
            ):
                self.parser.sha256_file(Path("missing.out"), chunk_size=size)
            opener.assert_not_called()

    def test_digest_is_independent_of_valid_chunk_size(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "artifact.out"
            for data in (b"", b"abc", b"0123456789" * 100_001):
                path.write_bytes(data)
                expected = hashlib.sha256(data).hexdigest()
                for size in (1, 17, 1024 * 1024, 8 * 1024 * 1024, 10**100):
                    with self.subTest(length=len(data), chunk_size=size):
                        self.assertEqual(self.parser.sha256_file(path, size), expected)

    def test_large_requested_buffer_is_bounded_and_stream_is_closed(self) -> None:
        class ReadSpy(io.BytesIO):
            def __init__(self, data: bytes) -> None:
                super().__init__(data)
                self.sizes: list[int | None] = []

            def read(self, size: int | None = -1) -> bytes:
                self.sizes.append(size)
                return super().read(size)

        data = b"artifact" * 200_000
        stream = ReadSpy(data)
        with patch.object(Path, "open", return_value=stream):
            self.assertEqual(
                self.parser.sha256_file(Path("artifact.out"), 8 * 1024 * 1024),
                hashlib.sha256(data).hexdigest(),
            )
        self.assertTrue(stream.closed)
        self.assertGreater(len(stream.sizes), 1)
        self.assertTrue(all(size is not None and 0 < size <= 1024 * 1024 for size in stream.sizes))

    def test_parser_delegates_to_shared_scan_core(self) -> None:
        expected = hashlib.sha256(b"delegated artifact").hexdigest()
        with patch.object(self.parser._SCAN, "sha256_file", return_value=expected) as shared:
            self.assertEqual(self.parser.sha256_file(Path("artifact.out"), 17), expected)
        shared.assert_called_once_with(Path("artifact.out"), chunk_size=17)

    def test_parser_rejects_invalid_shared_digest_values(self) -> None:
        for value in ("delegated", "", "a" * 63, "a" * 65, "g" * 64):
            with (
                self.subTest(value=value),
                patch.object(self.parser._SCAN, "sha256_file", return_value=value) as shared,
                self.assertRaisesRegex(ValueError, "invalid SHA-256"),
            ):
                self.parser.sha256_file(Path("artifact.out"), 17)
            shared.assert_called_once_with(Path("artifact.out"), chunk_size=17)

        for nonstring in (None, 0, b"a" * 64):
            with (
                self.subTest(value=nonstring),
                patch.object(self.parser._SCAN, "sha256_file", return_value=nonstring) as shared,
                self.assertRaisesRegex(TypeError, "SHA-256 string"),
            ):
                self.parser.sha256_file(Path("artifact.out"), 17)
            shared.assert_called_once_with(Path("artifact.out"), chunk_size=17)

    def test_missing_artifact_preserves_file_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(FileNotFoundError):
            self.parser.sha256_file(Path(directory) / "missing.out")
