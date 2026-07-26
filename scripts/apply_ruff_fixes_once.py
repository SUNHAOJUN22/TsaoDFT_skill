#!/usr/bin/env python3
"""Apply the audited final Ruff repairs, then remove this one-time script."""
from __future__ import annotations

from pathlib import Path

REPLACEMENTS: dict[str, list[tuple[str, str]]] = {
    "skills/tsao-dft-researcher/scripts/validate_figure_manifest.py": [
        (
            '("somo", "alpha", "beta", "α", "β")',
            '("somo", "alpha", "beta", "\\N{GREEK SMALL LETTER ALPHA}", "\\N{GREEK SMALL LETTER BETA}")',
        ),
        (
            '''                    if isinstance(vmin, (int, float)) and isinstance(vmax, (int, float)):
                        if not vmin < 0 < vmax:
                            errors.append(f"{pwhere}: ESP scale must cross zero")
                        if not math.isclose(abs(float(vmin)), abs(float(vmax)), rel_tol=1e-6, abs_tol=1e-12):
                            errors.append(f"{pwhere}: ESP comparison scale must be symmetric")''',
            '''                    numeric_scale = isinstance(vmin, (int, float)) and isinstance(vmax, (int, float))
                    if numeric_scale and not vmin < 0 < vmax:
                        errors.append(f"{pwhere}: ESP scale must cross zero")
                    if numeric_scale and not math.isclose(
                        abs(float(vmin)), abs(float(vmax)), rel_tol=1e-6, abs_tol=1e-12
                    ):
                        errors.append(f"{pwhere}: ESP comparison scale must be symmetric")''',
        ),
        (
            '''                if field in base_params or field in params:
                    if params.get(field) != base_params.get(field):
                        message = (
                            f"comparison_group {group}: parameter {field} differs between {baseline_where} and {where}"
                        )
                        (errors if strict else warnings).append(message)''',
            '''                if (field in base_params or field in params) and params.get(field) != base_params.get(field):
                    message = (
                        f"comparison_group {group}: parameter {field} differs between {baseline_where} and {where}"
                    )
                    (errors if strict else warnings).append(message)''',
        ),
    ],
    "skills/tsao-dft-researcher/scripts/validate_figure_spec.py": [
        (
            '''        if shared.get("esp_min") is not None and shared.get("esp_max") is not None:
            if float(shared["esp_min"]) >= float(shared["esp_max"]):
                failures.append("esp_min must be less than esp_max")''',
            '''        if (
            shared.get("esp_min") is not None
            and shared.get("esp_max") is not None
            and float(shared["esp_min"]) >= float(shared["esp_max"])
        ):
            failures.append("esp_min must be less than esp_max")''',
        ),
        (
            '''    if any(token in ftype for token in ["esp", "orbital", "iri", "igmh", "nto"]):
        if not ({".png", ".tif", ".tiff"} & suffixes):
            warnings.append("molecular-surface figure has no high-resolution raster output")''',
            '''    if any(token in ftype for token in ["esp", "orbital", "iri", "igmh", "nto"]) and not (
        {".png", ".tif", ".tiff"} & suffixes
    ):
        warnings.append("molecular-surface figure has no high-resolution raster output")''',
        ),
    ],
    "skills/tsao-dft-researcher/scripts/validate_research_manifest.py": [
        (
            '''        if accepted and calc.get("task_type") in {"minimum", "transition_state", "excited_opt", "conformer"}:
            if validation.get("optimization_converged") is not True:
                errors.append(f"{where}: accepted optimized structure requires optimization_converged=true")''',
            '''        if (
            accepted
            and calc.get("task_type") in {"minimum", "transition_state", "excited_opt", "conformer"}
            and validation.get("optimization_converged") is not True
        ):
            errors.append(f"{where}: accepted optimized structure requires optimization_converged=true")''',
        ),
        (
            '''        if accepted and calc.get("task_type") in {"minimum", "conformer"}:
            if validation.get("imaginary_frequency_count") != 0:
                errors.append(f"{where}: accepted minimum/conformer must have zero imaginary frequencies")''',
            '''        if (
            accepted
            and calc.get("task_type") in {"minimum", "conformer"}
            and validation.get("imaginary_frequency_count") != 0
        ):
            errors.append(f"{where}: accepted minimum/conformer must have zero imaginary frequencies")''',
        ),
        (
            '''        if grade == "B" and linked_artifacts:
            if not any(
                a.get("source_type") == "experiment" and a.get("status") == "accepted" for a in linked_artifacts
            ):
                errors.append(f"{where}: grade B requires at least one accepted experimental artifact")''',
            '''        if grade == "B" and linked_artifacts and not any(
            artifact.get("source_type") == "experiment" and artifact.get("status") == "accepted"
            for artifact in linked_artifacts
        ):
            errors.append(f"{where}: grade B requires at least one accepted experimental artifact")''',
        ),
        (
            '''        if grade == "C" and linked_artifacts:
            if not any(a.get("source_type") in {"literature", "external"} for a in linked_artifacts):
                warnings.append(f"{where}: grade C usually links literature or external evidence")''',
            '''        if grade == "C" and linked_artifacts and not any(
            artifact.get("source_type") in {"literature", "external"} for artifact in linked_artifacts
        ):
            warnings.append(f"{where}: grade C usually links literature or external evidence")''',
        ),
    ],
    "skills/tsao-dft-researcher/tests/test_parse_gaussian_rich.py": [
        (
            "from parse_gaussian import parse_log",
            "from parse_gaussian import parse_log  # noqa: E402 -- path injection is intentional for script testing",
        ),
    ],
    "skills/tsao-structure-prep/scripts/inspect_xyz.py": [
        (
            '''    except ValueError:
        raise ValueError("first line must be atom count")''',
            '''    except ValueError as exc:
        raise ValueError("first line must be atom count") from exc''',
        ),
        (
            '''        except ValueError:
            raise ValueError(f"non-numeric coordinate at atom {i}")''',
            '''        except ValueError as exc:
            raise ValueError(f"non-numeric coordinate at atom {i}") from exc''',
        ),
        (
            '    print(text if True else ("PASS" if r["ok"] else "FAIL"))',
            "    print(text)",
        ),
    ],
}


def main() -> int:
    for filename, replacements in REPLACEMENTS.items():
        path = Path(filename)
        text = path.read_text(encoding="utf-8")
        for old, new in replacements:
            count = text.count(old)
            if count != 1:
                raise RuntimeError(f"{filename}: expected one exact match, found {count}")
            text = text.replace(old, new)
        path.write_text(text, encoding="utf-8", newline="\n")

    Path(__file__).unlink()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
