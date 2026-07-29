from __future__ import annotations

import importlib.util
import inspect
import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
VALIDATORS = (
    "validate_agent_evals.py",
    "validate_ai_assets.py",
    "validate_capability_claims.py",
    "validate_catalog.py",
    "validate_constraints.py",
    "validate_dependencies.py",
    "validate_governance.py",
    "validate_ignore_markers.py",
    "validate_packaging_model.py",
    "validate_readme_links.py",
    "validate_readme_visuals.py",
    "validate_secrets.py",
)


def load_script(name: str) -> Any:
    path = ROOT / "scripts" / name
    module_name = f"release_validator_{name.replace('.', '_')}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def invoke_validate(module: Any) -> Any:
    function = module.validate
    kwargs: dict[str, Any] = {}
    for name, parameter in inspect.signature(function).parameters.items():
        if parameter.default is not inspect.Parameter.empty:
            continue
        if name == "root":
            kwargs[name] = ROOT
        elif name == "strict":
            kwargs[name] = True
        else:
            raise RuntimeError(f"unsupported required validator parameter: {name}")
    return function(**kwargs)


class ReleaseValidatorIntegrationTests(unittest.TestCase):
    def test_all_permanent_pure_validators_pass_current_repository(self) -> None:
        for name in VALIDATORS:
            with self.subTest(validator=name):
                module = load_script(name)
                result = invoke_validate(module)
                if isinstance(result, tuple):
                    self.assertFalse(result[0], f"{name}: {result}")
                elif isinstance(result, dict):
                    self.assertTrue(result.get("ok", not result.get("failures")), f"{name}: {result}")
                else:
                    self.assertFalse(result, f"{name}: {result}")

    def test_strict_repository_audit_main_json(self) -> None:
        module = load_script("validate_repo.py")
        with (
            patch.object(sys, "argv", ["validate_repo.py", "--strict", "--json"]),
            redirect_stdout(io.StringIO()) as stdout,
        ):
            self.assertEqual(module.main(), 0)
        payload = json.loads(stdout.getvalue())
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["failures"], [])

    def test_validator_main_json_surfaces(self) -> None:
        for name in (
            "validate_agent_evals.py",
            "validate_capability_claims.py",
            "validate_constraints.py",
            "validate_dependencies.py",
            "validate_governance.py",
            "validate_ignore_markers.py",
            "validate_packaging_model.py",
            "validate_secrets.py",
        ):
            with self.subTest(validator=name):
                module = load_script(name)
                with (
                    patch.object(sys, "argv", [name, "--json"]),
                    redirect_stdout(io.StringIO()) as stdout,
                ):
                    self.assertEqual(module.main(), 0)
                payload = json.loads(stdout.getvalue())
                self.assertTrue(payload["ok"])


if __name__ == "__main__":
    unittest.main()
