#!/usr/bin/env bash
set +e

: "${AUDIT_DIR:?AUDIT_DIR is required}"
rm -rf "$AUDIT_DIR"
mkdir -p "$AUDIT_DIR"

record_exit() {
  local name="$1"
  shift
  "$@" >"$AUDIT_DIR/${name}.log" 2>&1
  printf '%s\n' "$?" >"$AUDIT_DIR/${name}.exit"
}

git rev-parse HEAD >"$AUDIT_DIR/head.txt"
git branch --show-current >"$AUDIT_DIR/branch.txt"
git tag --list >"$AUDIT_DIR/tags.txt"
git ls-files -z >"$AUDIT_DIR/tracked-files.zlist"
git status --porcelain=v1 >"$AUDIT_DIR/git-status-before.txt"

python scripts/quality_gate.py --json >"$AUDIT_DIR/quality-gate.json" 2>&1
printf '%s\n' "$?" >"$AUDIT_DIR/quality-gate.exit"
record_exit compileall python -m compileall -q -f scripts tests skills

python - <<'PY'
from __future__ import annotations

import hashlib
import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path

root = Path.cwd()
out = Path(os.environ["AUDIT_DIR"])
tracked = [
    Path(item.decode("utf-8", "surrogateescape"))
    for item in (out / "tracked-files.zlist").read_bytes().split(b"\0")
    if item
]
categories = Counter()
suffixes = Counter()
hashes: dict[str, list[str]] = defaultdict(list)
large: list[dict[str, object]] = []
empty: list[str] = []
binary: list[str] = []
generated: list[str] = []
suspicious: list[dict[str, object]] = []
ignored_markers: list[dict[str, object]] = []
patterns = {
    "shell_true": re.compile(r"shell\s*=\s*True"),
    "os_system": re.compile(r"\bos\.system\s*\("),
    "eval_exec": re.compile(r"\b(?:eval|exec)\s*\("),
    "destructive": re.compile(r"\b(?:rmtree|unlink|remove)\s*\("),
    "network": re.compile(r"\b(?:urllib\.request|requests\.|httpx\.|socket\.)"),
    "secrets": re.compile(r"(?i)(api[_-]?key|secret|password|token)\s*=\s*['\"][^'\"]+['\"]"),
}
ignore_re = re.compile(
    r"(#\s*noqa(?::\s*[^\n]+)?|#\s*nosec(?:\s+[^\n]+)?|"
    r"#\s*type:\s*ignore(?:\[[^\]]+\])?|@unittest\.skip|"
    r"pytest\.mark\.(?:skip|xfail))"
)


def category(path: Path) -> str:
    parts = path.parts
    if parts[0] == "skills":
        return "test" if "tests" in parts else "skill"
    if parts[0] == "tests":
        return "test"
    if parts[0] == "scripts":
        return "script"
    if parts[0] == "docs":
        return "documentation"
    if parts[0] == "assets":
        return "asset"
    if parts[:2] == (".github", "workflows"):
        return "workflow"
    if path.suffix in {".yaml", ".yml", ".json", ".toml", ".cff"} or path.name in {"VERSION", "LICENSE"}:
        return "configuration"
    return "root/other"


for rel in tracked:
    path = root / rel
    if not path.is_file():
        continue
    data = path.read_bytes()
    size = len(data)
    categories[category(rel)] += 1
    suffixes[path.suffix.lower() or "<none>"] += 1
    hashes[hashlib.sha256(data).hexdigest()].append(rel.as_posix())
    if size == 0:
        empty.append(rel.as_posix())
    if size > 1_000_000:
        large.append({"path": rel.as_posix(), "bytes": size})
    if any(part in {"dist", "build", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"} for part in rel.parts):
        generated.append(rel.as_posix())
    if b"\0" in data[:8192]:
        binary.append(rel.as_posix())
        continue
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        binary.append(rel.as_posix())
        continue
    for line_no, line in enumerate(text.splitlines(), start=1):
        for name, pattern in patterns.items():
            if pattern.search(line):
                suspicious.append(
                    {"path": rel.as_posix(), "line": line_no, "kind": name, "text": line.strip()[:240]}
                )
        for match in ignore_re.finditer(line):
            ignored_markers.append(
                {"path": rel.as_posix(), "line": line_no, "marker": match.group(0), "text": line.strip()[:240]}
            )

duplicates = [paths for paths in hashes.values() if len(paths) > 1]
payload = {
    "tracked_file_count": len(tracked),
    "categories": dict(sorted(categories.items())),
    "suffixes": dict(sorted(suffixes.items())),
    "empty_files": sorted(empty),
    "large_files": sorted(large, key=lambda item: int(item["bytes"]), reverse=True),
    "binary_files": sorted(binary),
    "generated_or_cache_files": sorted(generated),
    "duplicate_content_groups": sorted(duplicates, key=lambda group: (-len(group), group)),
    "suspicious_code_patterns": suspicious,
    "ignore_markers": ignored_markers,
}
(out / "inventory.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
PY

: >"$AUDIT_DIR/mypy.log"
mypy_status=0
for target in scripts tests; do
  python -m mypy "$target" --ignore-missing-imports --show-error-codes --no-error-summary --pretty \
    >>"$AUDIT_DIR/mypy.log" 2>&1 || mypy_status=1
done
for skill in skills/*; do
  for kind in scripts tests; do
    if [ -d "$skill/$kind" ]; then
      printf '=== %s/%s ===\n' "$skill" "$kind" >>"$AUDIT_DIR/mypy.log"
      python -m mypy "$skill/$kind" --ignore-missing-imports --show-error-codes --no-error-summary --pretty \
        >>"$AUDIT_DIR/mypy.log" 2>&1 || mypy_status=1
    fi
  done
done
printf '%s\n' "$mypy_status" >"$AUDIT_DIR/mypy.exit"

python -m bandit -r scripts skills -x '*/tests/*' -f json -o "$AUDIT_DIR/bandit.json" \
  >"$AUDIT_DIR/bandit-console.log" 2>&1
printf '%s\n' "$?" >"$AUDIT_DIR/bandit.exit"

python -m pip_audit -r requirements.txt --format json --output "$AUDIT_DIR/pip-audit-runtime.json" \
  >"$AUDIT_DIR/pip-audit-runtime.log" 2>&1
printf '%s\n' "$?" >"$AUDIT_DIR/pip-audit-runtime.exit"
python -m pip_audit -r requirements-dev.txt --format json --output "$AUDIT_DIR/pip-audit-dev.json" \
  >"$AUDIT_DIR/pip-audit-dev.log" 2>&1
printf '%s\n' "$?" >"$AUDIT_DIR/pip-audit-dev.exit"
python -m pip_audit -r requirements-dev.txt --format cyclonedx-json --output "$AUDIT_DIR/sbom.cdx.json" \
  >"$AUDIT_DIR/sbom.log" 2>&1
printf '%s\n' "$?" >"$AUDIT_DIR/sbom.exit"

rm -rf dist build ./*.egg-info
python -m build --sdist --wheel >"$AUDIT_DIR/build.log" 2>&1
printf '%s\n' "$?" >"$AUDIT_DIR/build.exit"
find dist -maxdepth 2 -type f -printf '%p\t%s bytes\n' 2>/dev/null >"$AUDIT_DIR/build-artifacts.txt"

python - <<'PY'
from __future__ import annotations

import json
import os
from collections import defaultdict
from pathlib import Path

import yaml

root = Path.cwd()
out = Path(os.environ["AUDIT_DIR"])
findings: list[dict[str, object]] = []
trigger_map: dict[str, list[str]] = defaultdict(list)
rows: list[dict[str, object]] = []
injection_terms = (
    "untrusted",
    "prompt injection",
    "external content",
    "do not follow instructions",
    "treat as data",
)


def frontmatter(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    _, raw, _ = text.split("---", 2)
    value = yaml.safe_load(raw)
    return value if isinstance(value, dict) else {}


for skill_dir in sorted(path for path in (root / "skills").iterdir() if path.is_dir()):
    skill_md = skill_dir / "SKILL.md"
    manifest_path = skill_dir / "manifest.yaml"
    agent_path = skill_dir / "agents" / "openai.yaml"
    fm = frontmatter(skill_md) if skill_md.is_file() else {}
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) if manifest_path.is_file() else {}
    agent = yaml.safe_load(agent_path.read_text(encoding="utf-8")) if agent_path.is_file() else {}
    body = skill_md.read_text(encoding="utf-8") if skill_md.is_file() else ""
    has_injection_boundary = any(term in body.lower() for term in injection_terms)
    routes = manifest.get("routes", {}) if isinstance(manifest, dict) else {}
    triggers: list[str] = []
    if isinstance(routes, dict):
        for route_name, route in routes.items():
            if not isinstance(route, dict):
                findings.append({"severity": "high", "skill": skill_dir.name, "issue": f"route {route_name} is not mapping"})
                continue
            for trigger in route.get("triggers", []) or []:
                normalized = str(trigger).strip().lower()
                triggers.append(normalized)
                trigger_map[normalized].append(skill_dir.name)
            for rel in route.get("load", []) or []:
                if not (skill_dir / str(rel)).exists():
                    findings.append({"severity": "high", "skill": skill_dir.name, "issue": f"missing route load: {rel}"})
    if isinstance(manifest, dict):
        for rel in manifest.get("always_load", []) or []:
            if not (skill_dir / str(rel)).exists():
                findings.append({"severity": "high", "skill": skill_dir.name, "issue": f"missing always_load: {rel}"})
    metadata = fm.get("metadata", {}) if isinstance(fm.get("metadata"), dict) else {}
    if fm.get("name") != skill_dir.name:
        findings.append({"severity": "high", "skill": skill_dir.name, "issue": "frontmatter name differs from directory"})
    if manifest.get("version") != metadata.get("version"):
        findings.append({"severity": "medium", "skill": skill_dir.name, "issue": "manifest/frontmatter version mismatch"})
    if not has_injection_boundary:
        findings.append({"severity": "high", "skill": skill_dir.name, "issue": "no explicit external-content/prompt-injection boundary"})
    interface = agent.get("interface", {}) if isinstance(agent, dict) else {}
    prompt = interface.get("default_prompt") if isinstance(interface, dict) else None
    if not isinstance(prompt, str) or not prompt.strip():
        findings.append({"severity": "medium", "skill": skill_dir.name, "issue": "missing agents/openai.yaml default_prompt"})
    rows.append(
        {
            "skill": skill_dir.name,
            "frontmatter": fm,
            "manifest_version": manifest.get("version") if isinstance(manifest, dict) else None,
            "route_count": len(routes) if isinstance(routes, dict) else 0,
            "triggers": triggers,
            "prompt_injection_boundary": has_injection_boundary,
            "agent_default_prompt": prompt,
        }
    )

for trigger, owners in sorted(trigger_map.items()):
    unique = sorted(set(owners))
    if trigger and len(unique) > 1:
        severity = "low" if "tsao-dft-suite" in unique else "medium"
        findings.append({"severity": severity, "issue": f"trigger collision: {trigger}", "skills": unique})

(out / "skill-audit.json").write_text(
    json.dumps({"skills": rows, "findings": findings}, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
PY

python - <<'PY'
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path.cwd()
out = Path(os.environ["AUDIT_DIR"])
results: list[dict[str, object]] = []


def run(label: str, args: list[str], expected: int | None = None) -> None:
    completed = subprocess.run(args, cwd=root, capture_output=True, text=True, check=False)
    results.append(
        {
            "label": label,
            "command": args,
            "returncode": completed.returncode,
            "expected": expected,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
    )


with tempfile.TemporaryDirectory() as temporary:
    temp = Path(temporary)
    copy_target = temp / "copy"
    link_target = temp / "link"
    foreign_target = temp / "foreign"
    run(
        "copy install",
        [sys.executable, "scripts/install.py", "--agent", "codex", "--scope", "project", "--target", str(copy_target), "--skill", "tsao-dft-suite"],
        0,
    )
    run(
        "repeat install without force",
        [sys.executable, "scripts/install.py", "--agent", "codex", "--scope", "project", "--target", str(copy_target), "--skill", "tsao-dft-suite"],
        1,
    )
    run(
        "copy uninstall",
        [sys.executable, "scripts/install.py", "--agent", "codex", "--scope", "project", "--target", str(copy_target), "--skill", "tsao-dft-suite", "--uninstall"],
        0,
    )
    run(
        "symlink install",
        [sys.executable, "scripts/install.py", "--agent", "codex", "--scope", "project", "--target", str(link_target), "--skill", "tsao-dft-suite", "--method", "symlink"],
        0,
    )
    run(
        "symlink uninstall",
        [sys.executable, "scripts/install.py", "--agent", "codex", "--scope", "project", "--target", str(link_target), "--skill", "tsao-dft-suite", "--uninstall"],
        0,
    )
    victim = foreign_target / "tsao-dft-suite"
    victim.mkdir(parents=True)
    sentinel = victim / "FOREIGN_DATA.txt"
    sentinel.write_text("must survive\n", encoding="utf-8")
    run(
        "force over foreign directory",
        [sys.executable, "scripts/install.py", "--agent", "codex", "--scope", "project", "--target", str(foreign_target), "--skill", "tsao-dft-suite", "--force"],
    )
    results.append(
        {
            "label": "foreign directory ownership result",
            "sentinel_survived": sentinel.exists(),
            "destination_exists": victim.exists(),
        }
    )

(out / "installer-audit.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
PY

python - <<'PY'
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import yaml

root = Path.cwd()
out = Path(os.environ["AUDIT_DIR"])
required = [
    "SECURITY.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    ".github/CODEOWNERS",
    ".github/dependabot.yml",
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/pull_request_template.md",
    "CITATION.cff",
    "THIRD_PARTY.md",
]
files = {item: (root / item).exists() for item in required}
workflows = sorted(path.relative_to(root).as_posix() for path in (root / ".github/workflows").glob("*.y*ml"))
workflow_findings: list[str] = []


def walk(value: Any):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key, item
            yield from walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from walk(item)


for rel in workflows:
    data = yaml.load((root / rel).read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    if not isinstance(data, dict):
        workflow_findings.append(f"{rel}: workflow root is not a mapping")
        continue
    triggers = data.get("on", {})
    if isinstance(triggers, list):
        trigger_names = set(triggers)
    elif isinstance(triggers, dict):
        trigger_names = set(triggers)
    else:
        trigger_names = {triggers}
    for sensitive in {"pull_request_target", "workflow_run", "issues", "issue_comment"} & trigger_names:
        workflow_findings.append(f"{rel}: dangerous/sensitive trigger present: {sensitive}")
    for key, value in walk(data):
        if key != "uses" or not isinstance(value, str):
            continue
        if "@" not in value:
            workflow_findings.append(f"{rel}: invalid action reference: {value}")
            continue
        action, ref = value.rsplit("@", 1)
        if len(ref) != 40 or any(char not in "0123456789abcdef" for char in ref.lower()):
            workflow_findings.append(f"{rel}: action not pinned to full SHA: {action}@{ref}")

(out / "governance-audit.json").write_text(
    json.dumps(
        {"standard_files": files, "workflows": workflows, "workflow_findings": workflow_findings},
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)
PY

export GH_TOKEN="${GITHUB_TOKEN:-}"
gh api "repos/$GITHUB_REPOSITORY" >"$AUDIT_DIR/repository-api.json" 2>"$AUDIT_DIR/repository-api.error"
printf '%s\n' "$?" >"$AUDIT_DIR/repository-api.exit"
gh api "repos/$GITHUB_REPOSITORY/releases" >"$AUDIT_DIR/releases.json" 2>"$AUDIT_DIR/releases.error"
printf '%s\n' "$?" >"$AUDIT_DIR/releases.exit"
gh api "repos/$GITHUB_REPOSITORY/branches/main/protection" >"$AUDIT_DIR/branch-protection.json" 2>"$AUDIT_DIR/branch-protection.error"
printf '%s\n' "$?" >"$AUDIT_DIR/branch-protection.exit"
gh api "repos/$GITHUB_REPOSITORY/code-scanning/default-setup" >"$AUDIT_DIR/codeql-default-setup.json" 2>"$AUDIT_DIR/codeql-default-setup.error"
printf '%s\n' "$?" >"$AUDIT_DIR/codeql-default-setup.exit"
gh api -i "repos/$GITHUB_REPOSITORY/vulnerability-alerts" >"$AUDIT_DIR/dependabot-alerts-status.txt" 2>"$AUDIT_DIR/dependabot-alerts-status.error"
printf '%s\n' "$?" >"$AUDIT_DIR/dependabot-alerts-status.exit"

git status --porcelain=v1 >"$AUDIT_DIR/git-status-after.txt"
exit 0
