from __future__ import annotations

import base64
import copy
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from unittest.mock import patch

import yaml
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.rsa import generate_private_key

ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str) -> Any:
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(f"release_{name.replace('.', '_')}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ReleaseCoreCoverageTests(unittest.TestCase):
    shell: Any
    trust: Any
    parser: Any
    bridge: Any
    generator: Any
    validator: Any
    policy: dict[str, Any]

    @classmethod
    def setUpClass(cls) -> None:
        cls.shell = load_script("shell_contract.py")
        cls.trust = load_script("trust_boundary.py")
        cls.parser = load_script("engine_parser_contract.py")
        cls.bridge = load_script("benchmark_bridge.py")
        cls.generator = load_script("generate_job_script.py")
        cls.validator = load_script("validate_hpc_manifest.py")
        cls.policy = yaml.safe_load(
            (ROOT / "templates/performance-qualification-policy.yaml").read_text(encoding="utf-8")
        )

    def base_manifest(self) -> dict[str, Any]:
        return yaml.safe_load((ROOT / "templates/hpc-manifest.yaml").read_text(encoding="utf-8"))

    def signed_attestation(self, binding: dict[str, Any], scope: str) -> tuple[dict[str, Any], bytes]:
        private = Ed25519PrivateKey.generate()
        public = private.public_key().public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
        )
        now = datetime.now(timezone.utc)
        attestation: dict[str, Any] = {
            "schema_version": "1.0",
            "attestation_id": "A-1",
            "identity": "reviewer@example.org",
            "decision": "approved",
            "scope": scope,
            "issued_at": (now - timedelta(minutes=1)).isoformat(),
            "expires_at": (now + timedelta(hours=1)).isoformat(),
            "binding": binding,
            "signature_algorithm": "ed25519",
            "key_fingerprint": self.shell.public_key_fingerprint(public),
        }
        attestation["signature"] = base64.b64encode(
            private.sign(self.shell.canonical_json(attestation).encode("utf-8"))
        ).decode()
        return attestation, public

    def test_shell_scalar_path_argv_and_module_contracts(self) -> None:
        errors: list[str] = []
        self.assertEqual(self.shell.safe_scalar("JOB-1", "job", errors, job_name=True), "JOB-1")
        self.shell.safe_scalar("", "empty", errors)
        self.shell.safe_scalar(7, "integer", errors)
        self.shell.safe_scalar("bad\nvalue", "control", errors)
        self.shell.safe_scalar("bad value", "unsafe", errors)
        self.assertGreaterEqual(len(errors), 4)

        errors = []
        self.assertEqual(self.shell.safe_relative_path("run/input.dat", "path", errors), "run/input.dat")
        for value in ("", 2, "/absolute", "../escape", "bad\x00name"):
            self.shell.safe_relative_path(value, "path", errors)
        self.shell.safe_relative_path(".", "path", errors, allow_dot=False)
        self.assertGreaterEqual(len(errors), 5)

        errors = []
        self.assertEqual(self.shell.safe_env_name("OMP_NUM_THREADS", "env", errors), "OMP_NUM_THREADS")
        self.shell.safe_env_name("BAD-NAME", "env", errors)
        self.shell.safe_env_name(None, "env", errors)
        self.assertEqual(len(errors), 2)

        errors = []
        self.assertEqual(self.shell.validate_argv(["python", "a b.py"], "argv", errors), ["python", "a b.py"])
        for argv_value in (None, [], ["python", ""], ["python", 1], ["bad\narg"]):
            self.shell.validate_argv(argv_value, "argv", errors)
        self.assertGreaterEqual(len(errors), 5)
        self.assertEqual(self.shell.render_argv(["python", "a b.py"]), "python 'a b.py'")
        with self.assertRaises(ValueError):
            self.shell.render_argv([])

        errors = []
        self.assertEqual(self.shell.validate_module_or_source("cuda/13", "module", errors), "cuda/13")
        for value in ("", 1, "cuda;touch pwned", "bad\nmodule"):
            self.shell.validate_module_or_source(value, "module", errors)
        self.assertGreaterEqual(len(errors), 4)

    def test_shell_hash_binding_key_and_timestamp_contracts(self) -> None:
        manifest = self.base_manifest()
        payload = self.shell.manifest_binding_payload(manifest)
        self.assertEqual(payload["job_id"], manifest["job_id"])
        self.assertRegex(self.shell.manifest_sha256(manifest), r"^[0-9a-f]{64}$")
        self.assertRegex(self.shell.sha256_object({"b": 2, "a": 1}), r"^[0-9a-f]{64}$")

        private = Ed25519PrivateKey.generate()
        public = private.public_key().public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
        )
        self.assertRegex(self.shell.public_key_fingerprint(public), r"^[0-9a-f]{64}$")
        rsa_public = (
            generate_private_key(public_exponent=65537, key_size=2048)
            .public_key()
            .public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
        )
        with self.assertRaises(ValueError):
            self.shell.public_key_fingerprint(rsa_public)

        errors: list[str] = []
        self.assertIsNone(self.shell.parse_timestamp(None, "time", errors))
        self.assertIsNone(self.shell.parse_timestamp("not-time", "time", errors))
        self.assertIsNone(self.shell.parse_timestamp("2026-01-01T00:00:00", "time", errors))
        parsed = self.shell.parse_timestamp("2026-01-01T00:00:00Z", "time", errors)
        self.assertEqual(parsed, datetime(2026, 1, 1, tzinfo=timezone.utc))
        self.assertGreaterEqual(len(errors), 3)

    def test_signed_attestation_all_negative_edges(self) -> None:
        expected = {"manifest_sha256": "a" * 64}
        valid, public = self.signed_attestation(expected, "execute-reviewed-manifest")
        now = datetime.now(timezone.utc)
        self.assertEqual(self.shell.verify_signed_attestation(valid, public, expected, now=now), [])

        self.assertTrue(self.shell.verify_signed_attestation({}, public, expected, now=now))

        cases: list[dict[str, Any]] = []
        wrong_schema = copy.deepcopy(valid)
        wrong_schema["schema_version"] = "2.0"
        cases.append(wrong_schema)
        wrong_algorithm = copy.deepcopy(valid)
        wrong_algorithm["signature_algorithm"] = "rsa"
        cases.append(wrong_algorithm)
        empty_identity = copy.deepcopy(valid)
        empty_identity["identity"] = ""
        cases.append(empty_identity)
        future = copy.deepcopy(valid)
        future["issued_at"] = (now + timedelta(days=1)).isoformat()
        cases.append(future)
        expired = copy.deepcopy(valid)
        expired["expires_at"] = (now - timedelta(days=1)).isoformat()
        cases.append(expired)
        nonmapping = copy.deepcopy(valid)
        nonmapping["binding"] = []
        cases.append(nonmapping)
        mismatch = copy.deepcopy(valid)
        mismatch["binding"]["manifest_sha256"] = "b" * 64
        cases.append(mismatch)
        fingerprint = copy.deepcopy(valid)
        fingerprint["key_fingerprint"] = "0" * 64
        cases.append(fingerprint)
        signature_type = copy.deepcopy(valid)
        signature_type["signature"] = 4
        cases.append(signature_type)
        signature_encoding = copy.deepcopy(valid)
        signature_encoding["signature"] = "not-base64***"
        cases.append(signature_encoding)
        for case in cases:
            self.assertTrue(self.shell.verify_signed_attestation(case, public, expected, now=now))

        self.assertTrue(self.shell.verify_signed_attestation(valid, b"not-a-key", expected, now=now))
        other = (
            Ed25519PrivateKey.generate()
            .public_key()
            .public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
        )
        self.assertTrue(self.shell.verify_signed_attestation(valid, other, expected, now=now))

    def test_trust_load_schema_policy_and_identity_edges(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            json_path = root / "x.json"
            yaml_path = root / "x.yaml"
            json_path.write_text('{"a": 1}', encoding="utf-8")
            yaml_path.write_text("a: 1\n", encoding="utf-8")
            self.assertEqual(self.trust.load_json(json_path), {"a": 1})
            self.assertEqual(self.trust.load_yaml(yaml_path), {"a": 1})
            json_path.write_text("[]", encoding="utf-8")
            yaml_path.write_text("- x\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                self.trust.load_json(json_path)
            with self.assertRaises(ValueError):
                self.trust.load_yaml(yaml_path)

        schema = {"type": "object", "required": ["a"], "properties": {"a": {"type": "integer"}}}
        self.assertEqual(self.trust.schema_errors({"a": 1}, schema), [])
        self.assertTrue(self.trust.schema_errors({"a": "x"}, schema))

        policy_schema = json.loads(
            (ROOT / "templates/performance-qualification-policy.schema.json").read_text(encoding="utf-8")
        )
        self.assertEqual(self.trust.validate_policy(self.policy, policy_schema), [])
        modified = copy.deepcopy(self.policy)
        modified["unknown"] = True
        modified["acceleration_l3_required_evidence"] = ["engine"]
        errors = self.trust.validate_policy(modified, policy_schema)
        self.assertTrue(any("unsupported" in error for error in errors))
        self.assertTrue(any("executable contract" in error for error in errors))

    def record(
        self,
        plan: str = "PLAN",
        candidate: str = "gpu",
        role: str = "acceleration-candidate",
    ) -> dict[str, Any]:
        return {
            "benchmark_plan_id": plan,
            "candidate_id": candidate,
            "role": role,
            "engine": {"name": "vasp", "version": "6.5", "build_fingerprint_id": "B"},
            "hardware": {
                "hardware_fingerprint_id": "H",
                "cpu_model": "CPU",
                "cpu_arch": "x86_64",
                "nodes": 1,
                "ranks_per_node": 1,
                "threads_per_rank": 8,
                "gpu_vendor": "nvidia",
                "gpu_model": "GPU",
                "gpu_uuids": ["G"],
                "driver_version": "D",
                "gpu_binding": "closest",
            },
            "scientific": {
                "input_sha256": "1" * 64,
                "method_fingerprint_id": "M",
                "model_identity": {"functional": "PBE"},
                "convergence_thresholds": {"e": 1e-6},
                "observable_set": ["forces", "energy"],
            },
        }

    def test_trust_plan_isolation_and_payloads(self) -> None:
        first = self.record()
        self.assertRegex(self.trust.scientific_identity_digest(first), r"^[0-9a-f]{64}$")
        self.assertRegex(self.trust.topology_digest(first), r"^[0-9a-f]{64}$")
        self.assertEqual(self.trust.validate_record_schema({}, {"type": "object"}), [])

        plan, errors = self.trust.isolate_benchmark_plan([])
        self.assertIsNone(plan)
        self.assertTrue(errors)
        plan, errors = self.trust.isolate_benchmark_plan([self.record("A"), self.record("B")])
        self.assertIsNone(plan)
        self.assertTrue(errors)

        changed = self.record()
        changed["hardware"]["driver_version"] = "other"
        plan, errors = self.trust.isolate_benchmark_plan([first, changed])
        self.assertEqual(plan, "PLAN")
        self.assertTrue(errors)

        reference = self.record(candidate="cpu", role="scientific-reference")
        plan, errors = self.trust.isolate_benchmark_plan([reference])
        self.assertTrue(any("must not carry GPU" in error for error in errors))
        reference["hardware"]["gpu_uuids"] = []
        plan, errors = self.trust.isolate_benchmark_plan([reference])
        self.assertEqual((plan, errors), ("PLAN", []))

        summary = {
            "benchmark_plan_id": "PLAN",
            "candidates": {
                "cpu": {"role": "scientific-reference"},
                "gpu": {"role": "acceleration-candidate"},
            },
        }
        payload = self.trust.prequalification_payload([reference], summary, self.policy)
        self.assertEqual(payload["candidate_ids"], ["gpu"])
        root_manifest = self.trust.build_root_manifest({"a": b"one", "b": b"two"})
        self.assertEqual(set(root_manifest["files"]), {"a", "b"})

    def policy_candidate(self) -> dict[str, Any]:
        return {
            "build_identity_consistent": True,
            "hardware_identity_consistent": True,
            "parser_accepted_runs": 3,
            "total_runs": 3,
            "all_artifacts_verified": True,
            "minimum_repeats_pass": True,
            "numerical_equivalence": {"status": "PASS", "reasons": []},
            "cpu_to_candidate_speedup": 2.0,
            "strong_scaling_efficiency": 0.9,
            "resources": {"gpus_total": 4},
            "all_sources_real_engine": True,
        }

    def test_trust_policy_all_status_paths(self) -> None:
        policy = copy.deepcopy(self.policy)
        candidate = self.policy_candidate()
        self.assertEqual(
            self.trust.enforce_policy(candidate, "FAIL", policy, [])[0],
            "REFERENCE_MISSING",
        )
        fields = (
            ("build_identity_consistent", False, "BUILD_IDENTITY_MISSING"),
            ("hardware_identity_consistent", False, "HARDWARE_IDENTITY_MISSING"),
            ("all_artifacts_verified", False, "ARTIFACT_HASH_MISMATCH"),
            ("minimum_repeats_pass", False, "INSUFFICIENT_REPEATS"),
        )
        for field, value, expected in fields:
            case = self.policy_candidate()
            case[field] = value
            self.assertEqual(self.trust.enforce_policy(case, "PASS", policy, [])[0], expected)

        case = self.policy_candidate()
        case["parser_accepted_runs"] = 1
        self.assertEqual(self.trust.enforce_policy(case, "PASS", policy, [])[0], "PARSER_NOT_ACCEPTED")
        case = self.policy_candidate()
        case["total_runs"] = 1
        case["parser_accepted_runs"] = 1
        self.assertEqual(self.trust.enforce_policy(case, "PASS", policy, [])[0], "INSUFFICIENT_REPEATS")
        case = self.policy_candidate()
        case["numerical_equivalence"] = {"status": "FAIL", "reasons": ["bad"]}
        self.assertEqual(self.trust.enforce_policy(case, "PASS", policy, [])[0], "NUMERICAL_MISMATCH")
        case = self.policy_candidate()
        case["cpu_to_candidate_speedup"] = 1.0
        self.assertEqual(self.trust.enforce_policy(case, "PASS", policy, [])[0], "PERFORMANCE_NOT_IMPROVED")
        case = self.policy_candidate()
        case["strong_scaling_efficiency"] = 0.1
        policy["performance"]["minimum_strong_scaling_efficiency"] = 0.5
        self.assertEqual(self.trust.enforce_policy(case, "PASS", policy, [])[0], "PERFORMANCE_POLICY_FAILED")

        policy = copy.deepcopy(self.policy)
        case = self.policy_candidate()
        case["all_sources_real_engine"] = False
        self.assertEqual(self.trust.enforce_policy(case, "PASS", policy, [])[0], "L2_ONLY")
        self.assertEqual(
            self.trust.enforce_policy(self.policy_candidate(), "PASS", policy, ["bad review"])[0],
            "L2_ONLY",
        )
        self.assertEqual(
            self.trust.enforce_policy(self.policy_candidate(), "PASS", policy, [])[0],
            "QUALIFIED_FOR_SCOPED_L3_PERFORMANCE_EVIDENCE",
        )

        policy["require_verified_artifacts"] = False
        policy["require_performance_improvement"] = False
        policy["require_real_engine_source"] = False
        policy["require_independent_review"] = False
        case = self.policy_candidate()
        case["all_artifacts_verified"] = False
        case["cpu_to_candidate_speedup"] = None
        case["all_sources_real_engine"] = False
        self.assertEqual(
            self.trust.enforce_policy(case, "PASS", policy, ["ignored"])[0],
            "QUALIFIED_FOR_SCOPED_L3_PERFORMANCE_EVIDENCE",
        )

    def test_review_scope_and_bundle_error_paths(self) -> None:
        root = "a" * 64
        binding = {
            "policy_id": self.policy["policy_id"],
            "benchmark_plan_id": "PLAN",
            "candidate_ids": ["gpu"],
            "evidence_root_sha256": root,
        }
        review, public = self.signed_attestation(binding, "scoped-performance-evidence")
        self.assertEqual(
            self.trust.verify_review(review, public, root, self.policy["policy_id"], "PLAN", ["gpu"]),
            [],
        )
        wrong = copy.deepcopy(review)
        wrong["decision"] = "rejected"
        wrong["scope"] = "other"
        errors = self.trust.verify_review(wrong, public, root, self.policy["policy_id"], "PLAN", ["gpu"])
        self.assertTrue(any("decision" in error for error in errors))
        self.assertTrue(any("scope" in error for error in errors))

        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary)
            result = self.trust.publish_content_addressed_bundle(parent, [self.record()], {}, self.policy, review, {})
            bundle = Path(result["out_dir"])
            reused = self.trust.publish_content_addressed_bundle(parent, [self.record()], {}, self.policy, review, {})
            self.assertTrue(reused["reused"])

            missing = parent / "evidence-missing"
            missing.mkdir()
            self.assertFalse(self.trust.verify_content_addressed_bundle(missing)["ok"])

            bad_json = parent / "evidence-bad"
            bad_json.mkdir()
            (bad_json / "evidence-root.json").write_text("{", encoding="utf-8")
            self.assertFalse(self.trust.verify_content_addressed_bundle(bad_json)["ok"])

            renamed = parent / "renamed"
            bundle.rename(renamed)
            self.assertFalse(self.trust.verify_content_addressed_bundle(renamed)["ok"])
            renamed.rename(bundle)

            root_path = bundle / "evidence-root.json"
            root_doc = json.loads(root_path.read_text(encoding="utf-8"))
            original = copy.deepcopy(root_doc)
            root_doc["files"] = []
            root_path.write_text(json.dumps(root_doc), encoding="utf-8")
            self.assertFalse(self.trust.verify_content_addressed_bundle(bundle)["ok"])
            root_path.write_text(json.dumps(original, sort_keys=True, indent=2) + "\n", encoding="utf-8")

            extra = bundle / "extra.txt"
            extra.write_text("extra", encoding="utf-8")
            self.assertFalse(self.trust.verify_content_addressed_bundle(bundle)["ok"])
            extra.unlink()

            metadata = original["files"]["records.json"]
            records_path = bundle / "records.json"
            content = records_path.read_bytes()
            records_path.write_bytes(content + b"x")
            self.assertFalse(self.trust.verify_content_addressed_bundle(bundle)["ok"])
            records_path.write_bytes(content)
            metadata["size_bytes"] += 1
            root_path.write_text(json.dumps(original, sort_keys=True, indent=2) + "\n", encoding="utf-8")
            self.assertFalse(self.trust.verify_content_addressed_bundle(bundle)["ok"])

        with (
            tempfile.TemporaryDirectory() as temporary,
            patch.object(self.trust.os, "replace", side_effect=OSError("replace failed")),
            self.assertRaises(OSError),
        ):
            parent = Path(temporary)
            self.trust.publish_content_addressed_bundle(parent, [self.record()], {}, self.policy, review, {})
        self.assertFalse(any(parent.iterdir()))

    def parser_file(self, text: str, name: str = "out.log") -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temporary = tempfile.TemporaryDirectory()
        path = Path(temporary.name) / name
        path.write_text(text, encoding="utf-8")
        return temporary, path

    def test_parser_gaussian_all_routes(self) -> None:
        texts = [
            ("#p pbe/6-31g\nSCF Done: E(RPBE) = -1.0\nNormal termination of Gaussian\n", True, None),
            ("#p pbe/6-31g\nSCF Done: E(RPBE) = -1.0\n", False, "termination"),
            ("#p pbe/6-31g opt\nSCF Done: E(RPBE) = -1.0\nNormal termination of Gaussian\n", False, "geometry"),
            (
                "#p pbe/6-31g opt freq\nSCF Done: E(RPBE) = -1.0\nOptimization completed\n"
                "Frequencies -- -100 -50 20\nNormal termination of Gaussian\n",
                False,
                "scientific-gate",
            ),
            (
                "#p pbe/6-31g opt freq\nSCF Done: E(RPBE) = -1.0\nOptimization completed\n"
                "Frequencies -- -100 20 30\nNormal termination of Gaussian\n",
                True,
                None,
            ),
        ]
        for text, accepted, stage in texts:
            temporary, path = self.parser_file(text)
            with temporary:
                result = self.parser.parse_gaussian(path)
                self.assertEqual(result["parser_accepted"], accepted)
                self.assertEqual(result["failed_stage"], stage)
        temporary, path = self.parser_file(
            "Entering Link 1\n#p pbe/6-31g\nSCF Done: E(RPBE) = -1.0\nNormal termination of Gaussian\n"
            "Entering Link 1\n#p pbe/6-31g\nSCF Done: E(RPBE) = -2.0\nNormal termination of Gaussian\n"
        )
        with temporary:
            result = self.parser.parse_gaussian(path)
            self.assertTrue(result["warnings"])

    def test_parser_vasp_all_routes(self) -> None:
        success = (
            "vasp.6.5\nfree energy TOTEN = -10 eV\nEDIFF is reached\nElapsed time (sec): 4\n"
            "TOTAL-FORCE (eV/Angst)\n 1 2 3 0.1 0.2 0.3\n total drift\n"
            "General timing and accounting informations for this job\n"
        )
        temporary, path = self.parser_file(success, "OUTCAR")
        with temporary:
            result = self.parser.parse_vasp(path)
            self.assertTrue(result["parser_accepted"])
            self.assertEqual(result["forces"]["values"], [0.1, 0.2, 0.3])
            self.assertEqual(result["elapsed_time_s"], 4.0)
        cases = [
            ("EDIFF is reached\n", "termination"),
            ("General timing and accounting informations for this job\n", "electronic"),
            ("ZBRENT: fatal error\nGeneral timing and accounting informations for this job\n", "engine"),
            ("EDDDAV: Call to ZHEGV failed\n", "engine"),
            ("Sub-Space-Matrix is not hermitian\n", "engine"),
        ]
        for text, stage in cases:
            temporary, path = self.parser_file(text, "OUTCAR")
            with temporary:
                self.assertEqual(self.parser.parse_vasp(path)["failed_stage"], stage)

    def test_parser_qe_cp2k_all_routes_and_dispatch(self) -> None:
        qe_success = (
            "Program PWSCF v.7.4\nconvergence has been achieved\nEnd of BFGS Geometry Optimization\n"
            "! total energy = -1.0 Ry\nTotal force = 0.5\nP= 10\nJOB DONE.\n"
        )
        temporary, path = self.parser_file(qe_success)
        with temporary:
            result = self.parser.parse_qe(path)
            self.assertTrue(result["parser_accepted"])
            self.assertTrue(result["geometry_converged"])
            self.assertIsNotNone(result["forces"]["values"])
            self.assertEqual(result["stress"]["values"], [1.0])
        for text, stage in (
            ("convergence has been achieved\n", "termination"),
            ("JOB DONE.\n", "electronic"),
            ("convergence NOT achieved\nJOB DONE.\n", "electronic"),
        ):
            temporary, path = self.parser_file(text)
            with temporary:
                self.assertEqual(self.parser.parse_qe(path)["failed_stage"], stage)

        cp2k_success = (
            "CP2K| version string: CP2K 2026.1\nSCF run converged\nGEOMETRY OPTIMIZATION COMPLETED\n"
            "ENERGY| Total FORCE_EVAL energy (a.u.): -1.0\nMax. gradient = 0.1\nPROGRAM ENDED AT\n"
        )
        temporary, path = self.parser_file(cp2k_success)
        with temporary:
            result = self.parser.parse_cp2k(path)
            self.assertTrue(result["parser_accepted"])
            self.assertTrue(result["geometry_converged"])
            self.assertIsNotNone(result["forces"]["values"])
        for text, stage in (
            ("SCF run converged\n", "termination"),
            ("PROGRAM ENDED AT\n", "electronic"),
            ("SCF run NOT converged\nPROGRAM ENDED AT\n", "electronic"),
        ):
            temporary, path = self.parser_file(text)
            with temporary:
                self.assertEqual(self.parser.parse_cp2k(path)["failed_stage"], stage)

        with self.assertRaises(ValueError):
            self.parser.parse_engine_output("unknown", Path("missing"))
        with tempfile.TemporaryDirectory() as empty_dir:
            empty = Path(empty_dir) / "empty"
            empty.write_text("", encoding="utf-8")
            for engine in ("gaussian", "vasp", "quantum-espresso", "cp2k"):
                self.assertEqual(self.parser.parse_engine_output(engine, empty)["fatal_marker"], "SOURCE_MISSING")

    def test_bridge_loaders_artifact_and_full_record_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            json_path = root / "mapping.json"
            yaml_path = root / "mapping.yaml"
            json_path.write_text('{"a": 1}', encoding="utf-8")
            yaml_path.write_text("a: 1\n", encoding="utf-8")
            self.assertEqual(self.bridge.load_mapping(json_path), {"a": 1})
            self.assertEqual(self.bridge.load_mapping(yaml_path), {"a": 1})
            json_path.write_text("[]", encoding="utf-8")
            with self.assertRaises(ValueError):
                self.bridge.load_mapping(json_path)

            self.assertEqual(self.bridge.parse_key_value(None), {})
            kv = root / "runtime.txt"
            kv.write_text("a=1\nignored\nb = two=three\n", encoding="utf-8")
            self.assertEqual(self.bridge.parse_key_value(kv), {"a": "1", "b": "two=three"})
            self.assertEqual(self.bridge.parse_gpu_inventory(None), [])
            gpu = root / "gpu.csv"
            gpu.write_text("short\nH100, GPU-1, 0000:01, 590, 80G\n", encoding="utf-8")
            rows = self.bridge.parse_gpu_inventory(gpu)
            self.assertEqual(rows[0]["uuid"], "GPU-1")
            gpu.write_text("H100, GPU-1, 0000:01, 590\n", encoding="utf-8")
            self.assertEqual(self.bridge.parse_gpu_inventory(gpu)[0]["memory_total"], "")

            missing: list[str] = []
            source, relative = self.bridge._artifact_path(root, Path("out"), missing)
            self.assertEqual(relative, "out")
            self.assertEqual(source, root / "out")
            outside = root.parent / "outside.out"
            _, relative = self.bridge._artifact_path(root, outside, missing)
            self.assertEqual(relative, "outside.out")
            self.assertTrue(missing)

            (root / "input.in").write_text("input", encoding="utf-8")
            (root / "out").write_text("output", encoding="utf-8")
            parser_result = self.parser.base_result("vasp", root / "out")
            parser_result.update(
                {
                    "engine_version": "6.5",
                    "normal_termination": True,
                    "parser_accepted": True,
                    "scf_iterations": 5,
                    "elapsed_time_s": 2.0,
                    "energy": {"value": -1.0, "unit": "eV"},
                    "forces": {"values": [0.1], "unit": "eV/angstrom"},
                    "stress": {"values": [0.2], "unit": "GPa"},
                }
            )
            manifest = {
                "input": "input.in",
                "executable": "vasp_std",
                "scheduler": "slurm",
                "resources": {"nodes": 2, "tasks_per_node": 4, "cpus_per_task": 8},
                "acceleration": {
                    "benchmark_plan_id": "PLAN",
                    "build_fingerprint_id": "BUILD",
                    "gpu_vendor": "nvidia",
                    "gpu_bind": "closest",
                },
            }
            fingerprint = {
                "method_fingerprint_id": "MF",
                "model_chemistry": {
                    "method": "PBE",
                    "basis_or_pseudopotential": "POT",
                    "dispersion_or_corrections": "D3",
                },
                "numerics": {"ediff": 1e-6},
            }
            record = self.bridge.build_record(
                "vasp",
                parser_result,
                manifest,
                fingerprint,
                root,
                Path("out"),
                "gpu",
                "acceleration-candidate",
                1,
                runtime={
                    "site_id": "SITE",
                    "hardware_fingerprint_id": "HW",
                    "run_id": "RUN",
                    "timestamp": "2026-01-01T00:00:00Z",
                    "exit_status": "7",
                    "compiler": "C",
                    "mpi": "M",
                    "openmp_runtime": "O",
                    "accelerator_runtime": "A",
                    "cpu_model": "CPU",
                    "cpu_arch": "x86_64",
                    "filesystem": "lustre",
                    "scratch_type": "nvme",
                },
                scheduler_metrics={
                    "job_id": "JOB",
                    "wall_time_s": 3,
                    "cpu_time_s": 2,
                    "peak_host_memory_mb": 4,
                    "io_bytes": 5,
                    "energy_joules": 6,
                },
                gpu_inventory=rows,
            )
            self.assertEqual(record["execution"]["exit_status"], 7)
            self.assertEqual(record["scientific"]["observable_set"], ["energy", "forces", "stress"])
            self.assertEqual(record["evidence_source"]["missing_fields"], [])

            parser_result["engine_version"] = None
            parser_result["energy"] = {"value": None}
            parser_result["forces"] = {"values": None}
            parser_result["stress"] = {"values": None}
            record = self.bridge.build_record(
                "vasp",
                parser_result,
                {"input": "../escape", "resources": {}, "acceleration": {}},
                {},
                root,
                outside,
                "gpu",
                "acceleration-candidate",
                1,
            )
            self.assertFalse(record["scientific"]["parser_accepted"])
            self.assertTrue(record["evidence_source"]["missing_fields"])

    def test_generator_all_engines_schedulers_and_runtime_paths(self) -> None:
        base = self.base_manifest()
        self.assertEqual(self.generator.approval_guard({"approval": "approved"}), [])
        self.assertEqual(self.generator.approval_guard({"approval": "not_required"}), [])
        self.assertTrue(self.generator.approval_guard({"approval": "pending"}))

        custom = copy.deepcopy(base)
        custom["launcher"] = {"argv": ["mpirun", "-n", "2"]}
        self.assertIn("mpirun", self.generator.launcher_prefix(custom))
        auto = copy.deepcopy(base)
        auto["launcher"] = "auto"
        auto["scheduler"] = "local"
        with self.assertRaises(ValueError):
            self.generator.launcher_prefix(auto)
        auto["scheduler"] = "slurm"
        auto["resources"]["nodes"] = 2
        auto["resources"]["tasks_per_node"] = 2
        auto["acceleration"].update(
            {
                "enabled": True,
                "ranks_per_gpu": 1,
                "cpu_bind": "cores",
                "gpu_bind": "closest",
            }
        )
        self.assertIn("--gpus-per-task=1", self.generator.launcher_prefix(auto))
        auto["acceleration"]["ranks_per_gpu"] = 2
        self.assertNotIn("--gpus-per-task=1", self.generator.launcher_prefix(auto))

        expected = {
            "gaussian": ["g16"],
            "vasp": ["vasp_std"],
            "quantum-espresso": ["pw.x", "-in", "input"],
            "cp2k": ["cp2k", "-i", "input", "-o", "cp2k.out"],
            "generic": ["tool", "input"],
        }
        for engine, argv in expected.items():
            manifest = {"engine": engine, "executable": argv[0], "input": "input"}
            self.assertEqual(self.generator.engine_argv(manifest), argv)

        gaussian = copy.deepcopy(base)
        self.assertIn("< job.gjf", self.generator.engine_command(gaussian))
        cp2k = copy.deepcopy(base)
        cp2k.update({"engine": "cp2k", "executable": "cp2k", "input": "a.inp", "stdout": "a.out"})
        self.assertNotIn("> a.out", self.generator.engine_command(cp2k))
        vasp = copy.deepcopy(base)
        vasp.update({"engine": "vasp", "executable": "vasp_std"})
        self.assertIn("> job.log", self.generator.engine_command(vasp))

        self.assertEqual(self.generator.runtime_provenance(base), [])
        runtime = copy.deepcopy(base)
        runtime["acceleration"].update({"enabled": True, "record_runtime": False})
        self.assertEqual(self.generator.runtime_provenance(runtime), [])
        runtime["acceleration"].update(
            {
                "record_runtime": True,
                "gpu_vendor": "amd",
                "runtime_record": "runtime.txt",
            }
        )
        self.assertTrue(self.generator.runtime_provenance(runtime))
        runtime["acceleration"]["gpu_vendor"] = "nvidia"
        self.assertTrue(any("nvidia-smi" in line for line in self.generator.runtime_provenance(runtime)))

        slurm = copy.deepcopy(base)
        slurm["resources"].update({"partition": "gpu", "gpus_per_node": 2})
        script = self.generator.build(slurm)
        self.assertIn("#SBATCH --partition=gpu", script)
        self.assertIn("#SBATCH --gpus-per-node=2", script)

        pbs = copy.deepcopy(base)
        pbs["scheduler"] = "pbs"
        pbs["resources"].update({"queue": "work", "gpus_per_node": 1})
        pbs["environment"] = {
            "modules": ["cuda"],
            "source": ["env/setup.sh"],
            "variables": {"OMP_NUM_THREADS": "8"},
        }
        pbs["preflight"]["run_in_job"] = True
        pbs["parser"]["run_in_job"] = True
        script = self.generator.build(pbs)
        self.assertIn("#PBS -q work", script)
        self.assertIn("ngpus=1", script)
        self.assertIn("module load cuda", script)
        self.assertIn("source env/setup.sh", script)

        local = copy.deepcopy(base)
        local["scheduler"] = "local"
        local["acceleration"].update(
            {
                "enabled": True,
                "gpu_vendor": "nvidia",
                "device_order": "pci_bus_id",
            }
        )
        local["environment"]["variables"].pop("CUDA_DEVICE_ORDER", None)
        self.assertIn("export CUDA_DEVICE_ORDER=PCI_BUS_ID", self.generator.build(local))

    def test_validator_acceleration_commands_approval_and_main_edges(self) -> None:
        errors: list[str] = []
        self.assertEqual(self.validator.integer(2, "x", errors, 1), 2)
        for value in (True, "2", 0):
            self.validator.integer(value, "x", errors, 1)
        self.assertGreaterEqual(len(errors), 3)

        warnings: list[str] = []
        errors = []
        self.validator.validate_acceleration({}, {"gpus_per_node": 1}, errors, warnings)
        self.assertTrue(warnings)
        self.validator.validate_acceleration({"acceleration": []}, {}, errors, warnings)
        self.assertTrue(errors)

        manifest = self.base_manifest()
        acceleration = manifest["acceleration"]
        resources = manifest["resources"]
        acceleration.update(
            {
                "enabled": True,
                "backend": "bad",
                "mode": "bad",
                "gpu_vendor": "bad",
                "cpu_bind": "bad",
                "gpu_bind": "bad",
                "device_order": "bad",
                "precision": "bad",
                "ranks_per_gpu": 2,
                "allow_gpu_oversubscription": False,
                "profile_id": "",
                "benchmark_plan_id": "",
            }
        )
        self.validator.validate_acceleration(manifest, resources, errors, warnings)
        self.assertTrue(errors)

        for backend, vendor in (("cuda", "amd"), ("openacc", "amd"), ("metal", "nvidia"), ("hip", "intel")):
            case = self.base_manifest()
            case["resources"].update({"gpus_per_node": 1, "tasks_per_node": 1})
            case["acceleration"].update(
                {
                    "enabled": True,
                    "backend": backend,
                    "mode": "engine-native",
                    "gpu_vendor": vendor,
                    "profile_id": "P",
                    "benchmark_plan_id": "B",
                    "build_fingerprint_id": "F",
                }
            )
            case_errors: list[str] = []
            case_warnings: list[str] = []
            self.validator.validate_acceleration(case, case["resources"], case_errors, case_warnings)
            self.assertTrue(case_errors)

        case = self.base_manifest()
        case["acceleration"].update({"backend": "cuda", "mode": "workflow"})
        case_errors = []
        case_warnings = []
        self.validator.validate_acceleration(case, case["resources"], case_errors, case_warnings)
        self.assertTrue(case_warnings)

        command_cases = [
            {
                "launcher": "auto",
                "scheduler": "pbs",
                "preflight": {"argv": ["x"], "run_in_job": False},
                "parser": {"argv": ["x"], "run_in_job": False},
            },
            {
                "launcher": {"argv": []},
                "scheduler": "slurm",
                "preflight": {"argv": ["x"], "run_in_job": False},
                "parser": {"argv": ["x"], "run_in_job": False},
            },
            {
                "launcher": "raw",
                "scheduler": "slurm",
                "preflight": {"argv": ["x"], "run_in_job": False},
                "parser": {"argv": ["x"], "run_in_job": False},
            },
            {
                "launcher": "",
                "scheduler": "slurm",
                "preflight": "bad",
                "parser": {"argv": ["x"], "run_in_job": False},
            },
            {
                "launcher": "",
                "scheduler": "slurm",
                "preflight": {"command": "x", "argv": ["x"], "run_in_job": "no"},
                "parser": {"unsafe_shell": "x", "argv": ["x"], "run_in_job": False},
            },
        ]
        for case in command_cases:
            case_errors = []
            self.validator._validate_commands(case, case_errors)
            self.assertTrue(case_errors)

        not_required = self.base_manifest()
        not_required.update({"approval": "not_required", "support_level": "L3_EXECUTION_TESTED"})
        approval_errors: list[str] = []
        self.validator._validate_approval(not_required, approval_errors, None)
        self.assertTrue(approval_errors)

        approved = self.base_manifest()
        approved["approval"] = "approved"
        approval_errors = []
        self.validator._validate_approval(approved, approval_errors, None)
        self.assertTrue(approval_errors)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            approved["approval_public_key"] = "../escape.pem"
            approved["approval_attestation"] = {}
            approval_errors = []
            self.validator._validate_approval(approved, approval_errors, root)
            self.assertTrue(approval_errors)
            approved["approval_public_key"] = "missing.pem"
            approval_errors = []
            self.validator._validate_approval(approved, approval_errors, root)
            self.assertTrue(approval_errors)

            key = root / "key.pem"
            binding = {
                "manifest_sha256": self.shell.manifest_sha256(approved),
                "benchmark_plan_id": approved["acceleration"]["benchmark_plan_id"],
                "candidate_id": approved["job_id"],
                "method_fingerprint_digest": self.shell.sha256_object(
                    {"method_fingerprint_id": approved["method_fingerprint_id"]}
                ),
            }
            attestation, public = self.signed_attestation(binding, "execute-reviewed-manifest")
            key.write_bytes(public)
            approved["approval_public_key"] = "key.pem"
            approved["approval_attestation"] = attestation
            approval_errors = []
            self.validator._validate_approval(approved, approval_errors, root)
            self.assertEqual(approval_errors, [])
            approved["approval_attestation"]["decision"] = "rejected"
            approved["approval_attestation"]["scope"] = "wrong"
            approval_errors = []
            self.validator._validate_approval(approved, approval_errors, root)
            self.assertTrue(approval_errors)

        invalid = self.base_manifest()
        invalid.update(
            {
                "engine": "bad",
                "scheduler": "bad",
                "approval": "bad",
                "support_level": "bad",
                "job_id": "bad\njob",
                "executable": "bad exe",
                "input": "../input",
                "workdir": "../work",
                "resources": {
                    "nodes": "1",
                    "tasks_per_node": 8,
                    "cpus_per_task": 8,
                    "cpus_per_node": 4,
                    "memory_gb": 0,
                    "walltime": "bad",
                    "partition": "bad\npartition",
                },
                "environment": {
                    "modules": ["bad;module"],
                    "source": ["../source"],
                    "variables": {
                        "BAD-NAME": True,
                        "OMP_NUM_THREADS": "bad",
                        "MKL_NUM_THREADS": "100",
                        "CONTROL": "bad\nvalue",
                    },
                },
                "scratch": {"path": "../scratch"},
                "expected_outputs": [],
            }
        )
        errors, _ = self.validator.validate(invalid)
        self.assertGreater(len(errors), 10)

        nonmapping = self.base_manifest()
        nonmapping["resources"] = []
        nonmapping["environment"] = []
        nonmapping["expected_outputs"] = "bad"
        errors, _ = self.validator.validate(nonmapping)
        self.assertTrue(errors)

    def test_generator_and_validator_cli_main_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            valid = root / "valid.yaml"
            valid.write_text(yaml.safe_dump(self.base_manifest()), encoding="utf-8")
            generated = root / "job.sh"
            stdout = io.StringIO()
            with (
                patch.object(sys, "argv", ["generate_job_script.py", str(valid), "--out", str(generated)]),
                redirect_stdout(stdout),
            ):
                self.assertEqual(self.generator.main(), 0)
            self.assertTrue(generated.is_file())

            invalid = root / "invalid.yaml"
            invalid.write_text("- bad\n", encoding="utf-8")
            with (
                patch.object(sys, "argv", ["generate_job_script.py", str(invalid), "--out", str(generated)]),
                redirect_stdout(io.StringIO()),
            ):
                self.assertEqual(self.generator.main(), 1)

            with (
                patch.object(sys, "argv", ["validate_hpc_manifest.py", str(valid)]),
                redirect_stdout(io.StringIO()),
            ):
                self.assertEqual(self.validator.main(), 0)
            with (
                patch.object(sys, "argv", ["validate_hpc_manifest.py", str(invalid)]),
                redirect_stdout(io.StringIO()),
            ):
                self.assertEqual(self.validator.main(), 1)


if __name__ == "__main__":
    unittest.main()
