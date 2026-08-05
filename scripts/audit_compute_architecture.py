#!/usr/bin/env python3
"""Audit repository language roles and evidence-bounded acceleration candidates."""

from __future__ import annotations

import argparse
import ast
import json
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

SCHEMA_VERSION = "1.0"
EXCLUDED_PARTS = {
    ".git",
    ".audit-snapshot",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
}
LANGUAGES = {
    ".py": "Python",
    ".ps1": "PowerShell",
    ".sh": "Shell",
    ".bash": "Shell",
    ".c": "C",
    ".h": "C/C++ Header",
    ".cc": "C++",
    ".cpp": "C++",
    ".cxx": "C++",
    ".hpp": "C/C++ Header",
    ".cu": "CUDA C++",
    ".cuh": "CUDA C++ Header",
    ".f": "Fortran",
    ".f90": "Fortran",
    ".f95": "Fortran",
    ".f03": "Fortran",
    ".f08": "Fortran",
    ".rs": "Rust",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".json": "JSON",
    ".toml": "TOML",
    ".md": "Markdown",
    ".csv": "CSV",
    ".svg": "SVG",
}
CODE_LANGUAGES = {
    "Python",
    "PowerShell",
    "Shell",
    "C",
    "C/C++ Header",
    "C++",
    "CUDA C++",
    "CUDA C++ Header",
    "Fortran",
    "Rust",
}
NATIVE_LANGUAGES = {
    "C",
    "C/C++ Header",
    "C++",
    "CUDA C++",
    "CUDA C++ Header",
    "Fortran",
    "Rust",
}
CONTROL_IMPORTS = {
    "argparse",
    "csv",
    "hashlib",
    "importlib",
    "json",
    "os",
    "pathlib",
    "shutil",
    "subprocess",
    "tomllib",
    "xml",
    "yaml",
}
NUMERIC_IMPORTS = {
    "jax",
    "math",
    "matplotlib",
    "numpy",
    "scipy",
    "torch",
}
GPU_IMPORTS = {
    "cudf",
    "cupy",
    "cuequivariance",
    "jax",
    "numba",
    "torch",
}
PARALLEL_IMPORTS = {
    "concurrent",
    "dask",
    "joblib",
    "mpi4py",
    "multiprocessing",
    "ray",
    "threading",
}
EXTERNAL_ENGINE_TOKENS = {
    "cp2k",
    "g16",
    "g09",
    "gaussian",
    "pw.x",
    "quantum-espresso",
    "srun",
    "sbatch",
    "vasp",
}


@dataclass(frozen=True)
class PythonSignals:
    imports: frozenset[str]
    calls: frozenset[str]
    loops: int
    nested_loops: int
    comprehensions: int
    subprocess_calls: int
    file_reads: int
    file_writes: int


class _SignalVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.imports: set[str] = set()
        self.calls: set[str] = set()
        self.loops = 0
        self.nested_loops = 0
        self.comprehensions = 0
        self.subprocess_calls = 0
        self.file_reads = 0
        self.file_writes = 0
        self._loop_depth = 0

    @staticmethod
    def _call_name(node: ast.AST) -> str:
        parts: list[str] = []
        current = node
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        return ".".join(reversed(parts))

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports.add(alias.name.split(".", 1)[0])

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            self.imports.add(node.module.split(".", 1)[0])

    def _visit_loop(self, node: ast.For | ast.AsyncFor | ast.While) -> None:
        self.loops += 1
        if self._loop_depth:
            self.nested_loops += 1
        self._loop_depth += 1
        self.generic_visit(node)
        self._loop_depth -= 1

    def visit_For(self, node: ast.For) -> None:
        self._visit_loop(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self._visit_loop(node)

    def visit_While(self, node: ast.While) -> None:
        self._visit_loop(node)

    def visit_ListComp(self, node: ast.ListComp) -> None:
        self.comprehensions += 1
        self.generic_visit(node)

    def visit_SetComp(self, node: ast.SetComp) -> None:
        self.comprehensions += 1
        self.generic_visit(node)

    def visit_DictComp(self, node: ast.DictComp) -> None:
        self.comprehensions += 1
        self.generic_visit(node)

    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> None:
        self.comprehensions += 1
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        name = self._call_name(node.func)
        if name:
            self.calls.add(name)
        if name.startswith(("subprocess.", "os.system")):
            self.subprocess_calls += 1
        if name.endswith(("read_text", "read_bytes", "read", "readlines")):
            self.file_reads += 1
        if name.endswith(("write_text", "write_bytes", "write", "writelines")):
            self.file_writes += 1
        self.generic_visit(node)


def _tracked_paths(root: Path) -> list[Path]:
    try:
        process = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=root,
            check=False,
            capture_output=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        process = None
    if process is not None and process.returncode == 0:
        relative_paths = process.stdout.decode("utf-8", errors="strict").split("\0")
        candidates = [root / item for item in relative_paths if item]
    else:
        candidates = [path for path in root.rglob("*") if path.is_file()]
    return sorted(
        (
            path
            for path in candidates
            if path.is_file() and not EXCLUDED_PARTS.intersection(path.relative_to(root).parts)
        ),
        key=lambda item: item.as_posix(),
    )


def _read_utf8(path: Path) -> str | None:
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if b"\0" in data:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def _python_signals(text: str) -> tuple[PythonSignals | None, str | None]:
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return None, f"line {exc.lineno or 0}: {exc.msg}"
    visitor = _SignalVisitor()
    visitor.visit(tree)
    return (
        PythonSignals(
            imports=frozenset(visitor.imports),
            calls=frozenset(visitor.calls),
            loops=visitor.loops,
            nested_loops=visitor.nested_loops,
            comprehensions=visitor.comprehensions,
            subprocess_calls=visitor.subprocess_calls,
            file_reads=visitor.file_reads,
            file_writes=visitor.file_writes,
        ),
        None,
    )


def _contains_any(text: str, tokens: Iterable[str]) -> bool:
    lowered = text.lower()
    return any(token.lower() in lowered for token in tokens)


def _candidate(path: str, signals: PythonSignals, role: str) -> dict[str, Any] | None:
    reasons: list[str] = []
    score = 0
    if signals.nested_loops:
        reasons.append(f"{signals.nested_loops} nested loop(s)")
        score += 4 * signals.nested_loops
    elif signals.loops >= 3:
        reasons.append(f"{signals.loops} explicit loop(s)")
        score += signals.loops
    if signals.file_reads >= 3:
        reasons.append(f"{signals.file_reads} file-read call(s)")
        score += min(signals.file_reads, 6)
    if signals.subprocess_calls >= 2:
        reasons.append(f"{signals.subprocess_calls} external-process call(s)")
        score += signals.subprocess_calls
    if signals.imports & NUMERIC_IMPORTS and signals.loops:
        reasons.append("numeric imports combined with Python loops")
        score += 4
    if role == "numeric-candidate":
        score += 2
    if score < 4:
        return None
    action = "profile-before-native-migration"
    if signals.subprocess_calls >= 2 and not signals.nested_loops:
        action = "parallelize-independent-processes-with-bounded-workers"
    elif signals.file_reads >= 3 and not (signals.imports & NUMERIC_IMPORTS):
        action = "batch-or-stream-io-before-changing-language"
    return {"path": path, "score": score, "reasons": reasons, "recommended_action": action}


def build_report(root: Path) -> dict[str, Any]:
    root = root.resolve()
    if not root.is_dir():
        return {"ok": False, "schema_version": SCHEMA_VERSION, "errors": [f"not a directory: {root}"]}

    language_files: Counter[str] = Counter()
    language_lines: Counter[str] = Counter()
    python_roles: Counter[str] = Counter()
    parse_failures: list[dict[str, str]] = []
    candidates: list[dict[str, Any]] = []
    external_boundary_files: list[str] = []
    parallel_files: list[str] = []
    gpu_interface_files: list[str] = []
    text_files = 0

    for path in _tracked_paths(root):
        text = _read_utf8(path)
        if text is None:
            continue
        text_files += 1
        language = LANGUAGES.get(path.suffix.lower(), "Other text")
        line_count = len(text.splitlines())
        language_files[language] += 1
        language_lines[language] += line_count
        relative = path.relative_to(root).as_posix()
        if language != "Python":
            if language in CODE_LANGUAGES and _contains_any(text, EXTERNAL_ENGINE_TOKENS):
                external_boundary_files.append(relative)
            continue

        signals, error = _python_signals(text)
        if error is not None or signals is None:
            parse_failures.append({"path": relative, "error": error or "unknown parse error"})
            continue
        control = bool(signals.imports & CONTROL_IMPORTS) or signals.subprocess_calls > 0
        numeric = bool(signals.imports & NUMERIC_IMPORTS)
        gpu = bool(signals.imports & GPU_IMPORTS) or _contains_any(text, {"__dlpack__", "array_api", "cuda"})
        parallel = bool(signals.imports & PARALLEL_IMPORTS) or _contains_any(
            text,
            {"ProcessPoolExecutor", "ThreadPoolExecutor", "mpirun", "srun", "job array"},
        )
        if control and numeric:
            role = "mixed-control-and-numeric"
        elif control:
            role = "control-plane"
        elif numeric or (signals.nested_loops and signals.loops >= 2):
            role = "numeric-candidate"
        else:
            role = "general"
        python_roles[role] += 1
        if signals.subprocess_calls or _contains_any(text, EXTERNAL_ENGINE_TOKENS):
            external_boundary_files.append(relative)
        if parallel:
            parallel_files.append(relative)
        if gpu:
            gpu_interface_files.append(relative)
        item = _candidate(relative, signals, role)
        if item is not None:
            candidates.append(item)

    source_files = sum(language_files[name] for name in CODE_LANGUAGES)
    source_lines = sum(language_lines[name] for name in CODE_LANGUAGES)
    python_files = language_files["Python"]
    python_lines = language_lines["Python"]
    native_files = sum(language_files[name] for name in NATIVE_LANGUAGES)
    native_lines = sum(language_lines[name] for name in NATIVE_LANGUAGES)
    python_percent = round(100.0 * python_lines / source_lines, 2) if source_lines else 0.0
    native_percent = round(100.0 * native_lines / source_lines, 2) if source_lines else 0.0
    candidates.sort(key=lambda item: (-int(item["score"]), str(item["path"])))

    conclusion = (
        "Python is predominantly the orchestration, validation, parsing and evidence control plane; "
        "external DFT engines remain the compute plane."
    )
    if python_roles["numeric-candidate"] + python_roles["mixed-control-and-numeric"] > python_roles["control-plane"]:
        conclusion = (
            "Python contains a material numerical surface in addition to orchestration; profile the ranked candidates "
            "before selecting native or accelerator implementations."
        )

    return {
        "ok": not parse_failures,
        "schema_version": SCHEMA_VERSION,
        "scope": "tracked UTF-8 repository files; generated, cache and binary paths excluded",
        "summary": {
            "text_files": text_files,
            "source_files": source_files,
            "source_lines": source_lines,
            "python_files": python_files,
            "python_lines": python_lines,
            "python_source_line_percent": python_percent,
            "native_files": native_files,
            "native_lines": native_lines,
            "native_source_line_percent": native_percent,
        },
        "languages": [
            {"language": name, "files": language_files[name], "lines": language_lines[name]}
            for name in sorted(language_files, key=lambda item: (-language_lines[item], item))
        ],
        "architecture": {
            "python_roles": dict(sorted(python_roles.items())),
            "external_engine_boundary_files": sorted(set(external_boundary_files)),
            "parallel_or_distributed_files": sorted(set(parallel_files)),
            "gpu_or_array_interface_files": sorted(set(gpu_interface_files)),
            "conclusion": conclusion,
        },
        "ranked_static_candidates": candidates[:40],
        "parse_failures": parse_failures,
        "recommended_sequence": [
            "Keep Python for orchestration, schemas, provenance, CLI and external-engine adapters.",
            "Use engine-native GPU builds before attempting to inject CUDA-X libraries into packaged DFT engines.",
            "Parallelize independent jobs, parsers and campaign materialization with bounded process pools and scheduler arrays.",
            "Adopt Array API plus DLPack at Python tensor boundaries to avoid backend lock-in and unnecessary copies.",
            "Move only measured local kernels to a narrow C ABI/C++20 core; expose Python bindings with pybind11 or the CPython limited ABI.",
            "Use CUDA/HIP/SYCL/Kokkos kernels only after numerical equivalence, transfer-cost and device-memory gates pass.",
            "Deploy edge devices primarily for validated surrogate inference, monitoring and remote-DFT orchestration.",
        ],
        "non_claims": [
            "Static ranking is not runtime profiling and does not establish a bottleneck.",
            "Library mentions do not prove installation, execution, correctness or speedup.",
            "C++ or GPU migration is not recommended without representative benchmark evidence.",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    if not report.get("ok"):
        failures = report.get("errors") or report.get("parse_failures") or []
        return "# Compute Architecture Audit\n\nAudit failed.\n\n```json\n" + json.dumps(failures, indent=2) + "\n```\n"
    summary = report["summary"]
    lines = [
        "# Executable Compute Architecture Audit",
        "",
        f"Schema: `{report['schema_version']}`",
        "",
        "## Repository composition",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Audited UTF-8 text files | {summary['text_files']} |",
        f"| Source files | {summary['source_files']} |",
        f"| Source lines | {summary['source_lines']} |",
        f"| Python files | {summary['python_files']} |",
        f"| Python source-line share | {summary['python_source_line_percent']}% |",
        f"| Native-language files | {summary['native_files']} |",
        f"| Native source-line share | {summary['native_source_line_percent']}% |",
        "",
        "## Architecture conclusion",
        "",
        str(report["architecture"]["conclusion"]),
        "",
        "## Language inventory",
        "",
        "| Language | Files | Lines |",
        "|---|---:|---:|",
    ]
    for item in report["languages"]:
        lines.append(f"| {item['language']} | {item['files']} | {item['lines']} |")
    lines.extend(["", "## Highest static candidates", "", "These entries require runtime profiling before migration.", ""])
    candidates = report["ranked_static_candidates"][:20]
    if candidates:
        lines.extend(["| Path | Score | Evidence | Action |", "|---|---:|---|---|"])
        for item in candidates:
            evidence = "; ".join(item["reasons"]).replace("|", "\\|")
            lines.append(
                f"| `{item['path']}` | {item['score']} | {evidence} | `{item['recommended_action']}` |"
            )
    else:
        lines.append("No static candidate crossed the conservative threshold.")
    lines.extend(["", "## Required implementation sequence", ""])
    for index, item in enumerate(report["recommended_sequence"], start=1):
        lines.append(f"{index}. {item}")
    lines.extend(["", "## Non-claims", ""])
    for item in report["non_claims"]:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def _write(path: Path | None, text: str) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json", action="store_true", dest="json_output")
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--markdown-out", type=Path)
    args = parser.parse_args()

    report = build_report(args.root)
    rendered_json = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    _write(args.json_out, rendered_json)
    if args.markdown_out is not None:
        _write(args.markdown_out, render_markdown(report))
    if args.json_output:
        print(rendered_json, end="")
    else:
        summary = report.get("summary", {})
        print(
            "Compute architecture audit: "
            f"{'PASS' if report.get('ok') else 'FAIL'}; "
            f"Python={summary.get('python_source_line_percent', 'n/a')}%; "
            f"native={summary.get('native_source_line_percent', 'n/a')}%; "
            f"candidates={len(report.get('ranked_static_candidates', []))}"
        )
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
