#!/usr/bin/env python3
"Complete the reviewed baseline trust and transaction migration idempotently."

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
HPC = ROOT / "skills/tsao-dft-hpc-provenance"


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines(keepends=True)


def write_lines(path: Path, lines: list[str]) -> None:
    path.write_text("".join(lines), encoding="utf-8")


def ensure_local_import(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if "SCRIPT_DIR = Path(__file__).resolve().parent" in text:
        return
    if "import sys\n" not in text:
        anchor = "import json\n" if "import json\n" in text else "import argparse\n"
        if anchor not in text:
            raise RuntimeError(f"sys import anchor missing in {path}")
        text = text.replace(anchor, anchor + "import sys\n", 1)
    import_index = text.index("from shell_contract import")
    line_end = text.index("\n", import_index)
    import_line = text[import_index:line_end]
    if "# noqa: E402" not in import_line:
        text = text[:line_end] + "  # noqa: E402 -- standalone Skill import contract" + text[line_end:]
    import_index = text.index("from shell_contract import")
    block = (
        "SCRIPT_DIR = Path(__file__).resolve().parent\n"
        "if str(SCRIPT_DIR) not in sys.path:\n"
        "    sys.path.insert(0, str(SCRIPT_DIR))\n\n"
    )
    text = text[:import_index] + block + text[import_index:]
    path.write_text(text, encoding="utf-8")


def repair_inventory_and_typing() -> None:
    inventory = HPC / "scripts/inspect_execution_environment.py"
    lines = read_lines(inventory)
    main_index = next(i for i, line in enumerate(lines) if line.startswith("def main()"))
    if not any(line.strip() == "report = (" for line in lines[main_index:]):
        start = next(i for i in range(main_index, len(lines)) if lines[i].strip() == "if errors:")
        end = next(i for i in range(start, len(lines)) if lines[i].strip() == "rendered = (")
        candidate = "".join(lines[start:end])
        if '"inventory": report' not in candidate or "else:" not in candidate:
            raise RuntimeError("inventory conditional block failed structural validation")
        lines[start:end] = [
            "    report = (\n",
            '        {"ok": False, "errors": errors, "inventory": report}\n',
            "        if errors\n",
            '        else {"ok": True, "inventory": report}\n',
            "    )\n",
        ]
        write_lines(inventory, lines)

    parser_path = HPC / "scripts/engine_parser_contract.py"
    lines = read_lines(parser_path)
    if not any("vector: list[float]" in line for line in lines):
        index = next(i for i, line in enumerate(lines) if line.strip() == "vector = []")
        indent = lines[index][: len(lines[index]) - len(lines[index].lstrip())]
        lines[index] = indent + "vector: list[float] = []\n"
        write_lines(parser_path, lines)

    shell = HPC / "scripts/shell_contract.py"
    lines = read_lines(shell)
    if not any('signature_value = attestation.get("signature")' in line for line in lines):
        index = next(
            i
            for i, line in enumerate(lines)
            if line.strip() == 'signature = base64.b64decode(attestation.get("signature"), validate=True)'
        )
        indent = lines[index][: len(lines[index]) - len(lines[index].lstrip())]
        observed = [lines[index + offset].strip() for offset in range(5)]
        expected = [
            'signature = base64.b64decode(attestation.get("signature"), validate=True)',
            "key = serialization.load_pem_public_key(public_key_pem)",
            "if not isinstance(key, Ed25519PublicKey):",
            'raise ValueError("review key must be Ed25519")',
            'key.verify(signature, canonical_json(unsigned).encode("utf-8"))',
        ]
        if observed != expected:
            raise RuntimeError(f"shell signature target changed: {observed}")
        lines[index : index + 5] = [
            indent + 'signature_value = attestation.get("signature")\n',
            indent + "if not isinstance(signature_value, str):\n",
            indent + '    raise ValueError("attestation signature must be base64 text")\n',
            indent + "signature = base64.b64decode(signature_value, validate=True)\n",
            indent + "public_key = serialization.load_pem_public_key(public_key_pem)\n",
            indent + "if not isinstance(public_key, Ed25519PublicKey):\n",
            indent + '    raise ValueError("review key must be Ed25519")\n',
            indent + 'public_key.verify(signature, canonical_json(unsigned).encode("utf-8"))\n',
        ]
        write_lines(shell, lines)

    class_attributes = {
        HPC / "tests/test_engine_parser_contract.py": (
            "class EngineParserContractTests(unittest.TestCase):",
            ["    core: Any\n", "    schema: dict[str, Any]\n", "\n"],
            "    core: Any",
        ),
        HPC / "tests/test_benchmark_bridge.py": (
            "class BenchmarkBridgeTests(unittest.TestCase):",
            ["    bridge: Any\n", "    parser: Any\n", "\n"],
            "    bridge: Any",
        ),
        HPC / "tests/test_shell_trust_boundary.py": (
            "class ShellTrustBoundaryTests(unittest.TestCase):",
            ["    validator: Any\n", "    generator: Any\n", "    base: dict[str, Any]\n", "\n"],
            "    validator: Any",
        ),
        HPC / "tests/test_evidence_trust_boundary.py": (
            "class EvidenceTrustBoundaryTests(unittest.TestCase):",
            [
                "    trust: Any\n",
                "    shell: Any\n",
                "    performance: Any\n",
                "    result_schema: dict[str, Any]\n",
                "    policy_schema: dict[str, Any]\n",
                "    policy: dict[str, Any]\n",
                "\n",
            ],
            "    trust: Any",
        ),
    }
    for path, (class_line, attributes, marker) in class_attributes.items():
        lines = read_lines(path)
        if any(line.rstrip("\n") == marker for line in lines):
            continue
        index = next(i for i, line in enumerate(lines) if line.strip() == class_line)
        lines[index + 1 : index + 1] = attributes
        write_lines(path, lines)


def repair_installer_transaction() -> None:
    path = ROOT / "scripts/install.py"
    text = path.read_text(encoding="utf-8")
    if "from collections.abc import Iterator" not in text:
        text = text.replace(
            "from __future__ import annotations\n\n",
            "from __future__ import annotations\n\nfrom collections.abc import Iterator\n",
            1,
        )
    if "from contextlib import contextmanager, nullcontext, suppress" not in text:
        text = text.replace(
            "import argparse\n",
            "import argparse\nfrom contextlib import contextmanager, nullcontext, suppress\n",
            1,
        )
    if 'INSTALL_LOCK = ".tsao-install.lock"' not in text:
        text = text.replace("MARKER_SCHEMA = 1\n", 'MARKER_SCHEMA = 1\nINSTALL_LOCK = ".tsao-install.lock"\n', 1)
    if "def install_lock(" not in text:
        function = '''@contextmanager
def install_lock(target: Path) -> Iterator[None]:
    target.mkdir(parents=True, exist_ok=True)
    lock = target / INSTALL_LOCK
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise InstallSafetyError(f"another TsaoDFT install operation holds {lock}") from exc
    try:
        os.write(descriptor, f"pid={os.getpid()}\\n".encode("utf-8"))
        yield
    finally:
        os.close(descriptor)
        with suppress(FileNotFoundError):
            lock.unlink()


'''
        anchor = "def default_target(agent: str, scope: str) -> Path:\n"
        if anchor not in text:
            raise RuntimeError("installer lock insertion anchor missing")
        text = text.replace(anchor, function + anchor, 1)
    if "rollback: Path | None = None" not in text:
        text = text.replace(
            "    staged: Path | None = None\n    backup: Path | None = None\n",
            "    staged: Path | None = None\n    backup: Path | None = None\n    rollback: Path | None = None\n",
            1,
        )
    old_remove = '''            else:
                remove_owned_destination(destination)
'''
    new_remove = '''            else:
                rollback = Path(tempfile.mkdtemp(prefix=f".{destination.name}.rollback-", dir=destination.parent))
                rollback.rmdir()
                os.replace(destination, rollback)
'''
    if old_remove in text:
        text = text.replace(old_remove, new_remove, 1)
    if "if rollback is not None and rollback.exists()" not in text:
        old_marker = '''        write_marker(
            target,
            skill,
            {
                "schema_version": MARKER_SCHEMA,
                "repository": REPOSITORY,
                "skill": skill,
                "version": (ROOT / "VERSION").read_text(encoding="utf-8").strip(),
                "method": method,
                "source": str(source),
                "destination": str(destination),
                "source_digest": tree_digest(source),
                "installed_digest": installed_digest,
                "backup": str(backup) if backup is not None else None,
            },
        )
'''
        new_marker = old_marker + '''        if rollback is not None and rollback.exists():
            remove_owned_destination(rollback)
'''
        if old_marker not in text:
            raise RuntimeError("installer marker transaction block missing")
        text = text.replace(old_marker, new_marker, 1)
    old_except = '''        if backup is not None and backup.exists() and not destination.exists() and not destination.is_symlink():
            os.replace(backup, destination)
        raise
'''
    if old_except in text:
        text = text.replace(
            old_except,
            '''        original = backup if backup is not None else rollback
        if original is not None and original.exists():
            if destination.exists() or destination.is_symlink():
                remove_owned_destination(destination)
            os.replace(original, destination)
        raise
''',
            1,
        )
    if "lock_context = nullcontext() if args.dry_run else install_lock(target)" not in text:
        old_main = '''        target = safe_target(args.target or default_target(args.agent, args.scope))
        for skill in selected:
            if args.uninstall:
                uninstall_skill(target, skill, force=args.force, dry_run=args.dry_run)
            else:
                install_skill(
                    target,
                    skill,
                    args.method,
                    force=args.force,
                    backup_existing=args.backup_existing,
                    dry_run=args.dry_run,
                )
'''
        new_main = '''        target = safe_target(args.target or default_target(args.agent, args.scope))
        lock_context = nullcontext() if args.dry_run else install_lock(target)
        with lock_context:
            for skill in selected:
                if args.uninstall:
                    uninstall_skill(target, skill, force=args.force, dry_run=args.dry_run)
                else:
                    install_skill(
                        target,
                        skill,
                        args.method,
                        force=args.force,
                        backup_existing=args.backup_existing,
                        dry_run=args.dry_run,
                    )
'''
        if old_main not in text:
            raise RuntimeError("installer main transaction block missing")
        text = text.replace(old_main, new_main, 1)
    path.write_text(text, encoding="utf-8")


def repair_validator_and_imports() -> None:
    validator = HPC / "scripts/validate_hpc_manifest.py"
    ensure_local_import(validator)
    ensure_local_import(HPC / "scripts/benchmark_bridge.py")
    ensure_local_import(HPC / "scripts/trust_boundary.py")

    text = validator.read_text(encoding="utf-8")
    old_resource_loop = '''    for key in ("nodes", "tasks_per_node", "cpus_per_task"):
        integer(resources.get(key), f"resources.{key}", errors, 1)
'''
    new_resource_loop = '''    integer(resources.get("nodes"), "resources.nodes", errors, 1)
    tasks_per_node = integer(resources.get("tasks_per_node"), "resources.tasks_per_node", errors, 1)
    cpus_per_task = integer(resources.get("cpus_per_task"), "resources.cpus_per_task", errors, 1)
    if resources.get("cpus_per_node") is not None:
        cpus_per_node = integer(resources.get("cpus_per_node"), "resources.cpus_per_node", errors, 1)
        if tasks_per_node * cpus_per_task > cpus_per_node:
            errors.append("tasks_per_node * cpus_per_task exceeds cpus_per_node")
'''
    if old_resource_loop in text:
        text = text.replace(old_resource_loop, new_resource_loop, 1)
    elif "tasks_per_node * cpus_per_task exceeds cpus_per_node" not in text:
        raise RuntimeError("validator CPU capacity insertion target missing")

    variables_anchor = '''    if not isinstance(variables, dict):
        errors.append("environment.variables must be a mapping")
        variables = {}
'''
    warning = '''    if "CUDA_VISIBLE_DEVICES" in variables and data.get("scheduler") in {"slurm", "pbs"}:
        warnings.append("hard-coded CUDA_VISIBLE_DEVICES under a scheduler should use scheduler GPU binding")
'''
    if "hard-coded CUDA_VISIBLE_DEVICES" not in text:
        if variables_anchor not in text:
            raise RuntimeError("validator CUDA warning insertion target missing")
        text = text.replace(variables_anchor, variables_anchor + warning, 1)

    if 'errors: list[str] = ["manifest root must be a mapping"]' not in text:
        text = text.replace(
            '        errors, warnings = ["manifest root must be a mapping"], []\n',
            '        errors: list[str] = ["manifest root must be a mapping"]\n'
            "        warnings: list[str] = []\n",
            1,
        )
    validator.write_text(text, encoding="utf-8")


def migrate_example_and_security_contract() -> None:
    example = HPC / "examples/slurm/hpc-manifest.yaml"
    manifest = yaml.safe_load(example.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise RuntimeError("example manifest root must be a mapping")
    manifest["schema_version"] = "1.2"
    manifest["acceleration"] = {
        "enabled": False,
        "profile_id": "CPU-ONLY",
        "backend": "none",
        "mode": "none",
        "gpu_vendor": "none",
        "ranks_per_gpu": 1,
        "allow_gpu_oversubscription": False,
        "cpu_bind": "none",
        "gpu_bind": "none",
        "device_order": "scheduler",
        "precision": "fp64",
        "record_runtime": False,
    }
    manifest["preflight"] = {
        "argv": ["python", "preflight_gaussian_input.py", "demo.gjf"],
        "run_in_job": False,
    }
    manifest["parser"] = {
        "argv": ["python", "parse_gaussian.py", "demo.log", "--json"],
        "run_in_job": False,
    }
    example.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")

    security = ROOT / "tests/test_security_gates.py"
    text = security.read_text(encoding="utf-8")
    if '("scripts/run_coverage.py", "B404")' not in text:
        marker = '    ("skills/tsao-dft-ml-active-learning/scripts/train_ridge_baseline.py", "B311"),\n'
        additions = "".join(
            [
                '    ("scripts/run_coverage.py", "B404"),\n',
                '    ("scripts/run_coverage.py", "B603"),\n',
                '    ("scripts/run_strict_type_checks.py", "B404"),\n',
                '    ("scripts/run_strict_type_checks.py", "B603"),\n',
                '    ("skills/tsao-dft-hpc-provenance/scripts/inspect_execution_environment.py", "B404"),\n',
            ]
        )
        if marker not in text:
            raise RuntimeError("Bandit expected-set insertion target missing")
        security.write_text(text.replace(marker, marker + additions, 1), encoding="utf-8")


def main() -> int:
    repair_inventory_and_typing()
    repair_installer_transaction()
    repair_validator_and_imports()
    migrate_example_and_security_contract()
    print("baseline migration applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
