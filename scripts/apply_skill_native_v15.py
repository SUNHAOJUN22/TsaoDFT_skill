from __future__ import annotations

import json
import re
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
START = "<!-- TSAO_SKILL_NATIVE_V15_START -->"
END = "<!-- TSAO_SKILL_NATIVE_V15_END -->"
OLD = re.compile(r"<!-- TSAO_SKILL_NATIVE_V(?:1[0-4]|[1-9])_START -->.*?<!-- TSAO_SKILL_NATIVE_V(?:1[0-4]|[1-9])_END -->\s*", re.DOTALL)


def clean(value: str) -> str: return textwrap.dedent(value).strip()+"\n"
def write(path: str,value: str)->None:
 p=ROOT/path; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(clean(value),encoding="utf-8",newline="\n")
def merge(path: str,block: str,title: str)->None:
 p=ROOT/path; cur=p.read_text(encoding="utf-8") if p.exists() else f"# {title}\n\n"; cur=OLD.sub("",cur).rstrip()+"\n\n"; p.write_text(cur+START+"\n"+clean(block)+END+"\n",encoding="utf-8",newline="\n")

skill=r'''
---
name: tsao-dft-suite
description: Evidence-first DFT workflow for Gaussian, VASP, Quantum ESPRESSO, CP2K, transition-state theory, HPC provenance, and ML-potential qualification. Use for parser, workflow, quantity-shape, standard-state, convergence, external-execution, or model-acceptance tasks. Do not treat early success text, local fixtures, trainer self-claims, or missing solver receipts as completed external DFT execution.
---

# TSAO DFT Suite

## Parser precedence

Parse complete job boundaries and apply fail-closed precedence:

`FATAL/TRUNCATED > NOT_CONVERGED > SUCCESS`.

An earlier success token cannot override a later fatal termination, missing finalization, or unconverged electronic/ionic cycle.

## Quantity contract

A quantity declares kind, shape, unit, convention, atom mapping, and provenance. Energy is scalar, force is \(N\times3\), stress is \(3\times3\) or an explicitly named Voigt convention.

## Transition-state theory

For molecularity \(n\),

\[
k_n(T)=\kappa\frac{k_BT}{h}\exp\left(-\frac{\Delta G^{\ddagger,\circ}}{RT}\right)(c^\circ)^{1-n},
\]

so the rate-constant units and standard state are explicit.

## Model acceptance

A model cannot be accepted without exact dataset/model/code/environment hashes, applicability domain, calibrated uncertainty, holdout or external validation, and independent approval. A trainer may create a draft, never self-sign `ACCEPTED`.

## Truth boundary

Without a signed Gaussian/VASP/QE/CP2K execution receipt and independent scientific review, retain `EXTERNAL_DFT_EXECUTION_NOT_VERIFIED`.
'''

dod=r'''
# Definition of done

- Gaussian, VASP, QE, and CP2K parsers share fatal and truncation precedence.
- Job boundaries, final electronic/ionic convergence, and expected terminal markers are checked.
- Scalar, vector, force, stress, Hessian, and trajectory shapes are explicit.
- Units, atom mapping, coordinate frame, and Voigt convention are retained.
- TST molecularity, standard state, symmetry, tunneling model, and rate-constant units are explicit.
- Dataset, model, code, environment, applicability domain, uncertainty, and validation hashes are bound.
- External execution and independent scientific approval use separate non-replayable evidence.
- Local fixtures and parser tests never become real DFT execution claims.
'''

openai_yaml=r'''
interface:
  display_name: "TSAO DFT Suite"
  short_description: "Fail-closed DFT parsing, TST, HPC provenance, and model acceptance"
  default_prompt: "Select the minimal DFT workflow, preserve quantity shape and units, apply fatal precedence, bind external execution evidence, and keep model training separate from independent acceptance."
policy:
  allow_implicit_invocation: true
  truth_boundary: "No external DFT execution claim without a signed solver receipt."
'''

evals={"schema":"tsao-dft.skill-routing.v15","skill":"tsao-dft-suite","cases":[
 {"id":"en-parser","language":"en","prompt":"Fix the VASP parser so a late fatal error overrides an earlier convergence line.","expected":"TRIGGER"},
 {"id":"zh-parser","language":"zh","prompt":"修复VASP解析器，让后出现的致命错误覆盖前面的收敛文本。","expected":"TRIGGER"},
 {"id":"en-tst","language":"en","prompt":"Derive a bimolecular TST rate constant with explicit standard state and units.","expected":"TRIGGER"},
 {"id":"zh-tst","language":"zh","prompt":"推导双分子TST速率常数，明确标准态与单位。","expected":"TRIGGER"},
 {"id":"en-negative","language":"en","prompt":"What does DFT stand for?","expected":"NO_TRIGGER"},
 {"id":"zh-negative","language":"zh","prompt":"DFT三个字母代表什么？","expected":"NO_TRIGGER"}
]}

validator=r'''
from __future__ import annotations
import argparse,json
from pathlib import Path
R=(".agents/skills/tsao-dft-suite/SKILL.md",".agents/skills/tsao-dft-suite/agents/openai.yaml",".agents/skills/tsao-dft-suite/references/definition-of-done.md",".agents/skills/tsao-dft-suite/evals/evals.json","assets/diagrams/vision-en.svg","assets/diagrams/vision-zh.svg")
BAD=("\x00","\ufffd","Ã","Â","â€")
def main()->int:
 p=argparse.ArgumentParser();p.add_argument("--root",default=".");p.add_argument("--report",default="artifacts/skill-validation-v15.json");a=p.parse_args();root=Path(a.root).resolve();e=[]
 for x in R:
  if not (root/x).is_file():e.append(f"missing {x}")
 s=root/R[0]
 if s.is_file():
  t=s.read_text(encoding="utf-8")
  if not t.startswith("---\n") or "name: tsao-dft-suite" not in t[:800]:e.append("invalid SKILL.md")
  if "Do not treat early success" not in t[:1300]:e.append("anti-trigger boundary missing")
 for f in root.rglob("*"):
  if f.is_file() and f.suffix.lower() in {".md",".py",".json",".yaml",".yml",".svg"}:
   v=f.read_text(encoding="utf-8")
   if any(m in v for m in BAD):e.append(f"Unicode failure in {f.relative_to(root)}")
 ep=root/R[3]
 if ep.is_file():
  c=json.loads(ep.read_text(encoding="utf-8")).get("cases",[])
  if len(c)<6 or {i.get("expected") for i in c}!={"TRIGGER","NO_TRIGGER"}:e.append("routing evals incomplete")
 o={"schema":"tsao-dft.skill-validation.v15","status":"PASS" if not e else "FAIL","errors":e};q=root/a.report;q.parent.mkdir(parents=True,exist_ok=True);q.write_text(json.dumps(o,ensure_ascii=False,indent=2)+"\n",encoding="utf-8");print(json.dumps(o,ensure_ascii=False));return 0 if not e else 1
if __name__=="__main__":raise SystemExit(main())
'''

contracts=r'''
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from math import exp, isfinite
from typing import Sequence

BOLTZMANN = 1.380649e-23
PLANCK = 6.62607015e-34
GAS_CONSTANT = 8.31446261815324


class ParseSeverity(IntEnum):
    SUCCESS = 0
    NOT_CONVERGED = 1
    TRUNCATED = 2
    FATAL = 3


@dataclass(frozen=True)
class ParseDecision:
    status: str
    reason_codes: tuple[str, ...]


def final_parse_status(events: Sequence[str], *, expected_terminal_seen: bool) -> ParseDecision:
    normalized = [event.strip().upper() for event in events]
    reasons: list[str] = []
    severity = ParseSeverity.SUCCESS
    if any(event in {"FATAL", "ERROR_TERMINATION", "SEGMENTATION_FAULT"} for event in normalized):
        severity = ParseSeverity.FATAL; reasons.append("FATAL_EVENT")
    elif not expected_terminal_seen:
        severity = ParseSeverity.TRUNCATED; reasons.append("EXPECTED_TERMINAL_MISSING")
    elif any(event in {"SCF_NOT_CONVERGED", "IONIC_NOT_CONVERGED"} for event in normalized):
        severity = ParseSeverity.NOT_CONVERGED; reasons.append("FINAL_CONVERGENCE_MISSING")
    mapping = {ParseSeverity.SUCCESS:"SUCCESS",ParseSeverity.NOT_CONVERGED:"NOT_CONVERGED",ParseSeverity.TRUNCATED:"TRUNCATED",ParseSeverity.FATAL:"FATAL"}
    return ParseDecision(mapping[severity],tuple(reasons))


@dataclass(frozen=True)
class Quantity:
    values: tuple[float, ...]
    shape: tuple[int, ...]
    unit: str
    kind: str
    convention: str | None = None

    def validate(self) -> None:
        if not self.unit or not self.kind or any(isinstance(v,bool) or not isfinite(float(v)) for v in self.values):
            raise ValueError("quantity requires finite non-boolean values, unit, and kind")
        size=1
        for axis in self.shape:
            if axis<=0:raise ValueError("shape axes must be positive")
            size*=axis
        if size!=len(self.values):raise ValueError("shape does not match flattened values")
        if self.kind=="force" and (len(self.shape)!=2 or self.shape[1]!=3):raise ValueError("force shape must be N x 3")
        if self.kind=="stress" and self.shape not in {(3,3),(6,)}:raise ValueError("stress shape must be 3 x 3 or explicit Voigt-6")
        if self.kind=="stress" and self.shape==(6,) and not self.convention:raise ValueError("Voigt stress requires a convention")


def tst_rate_constant(*, temperature_k: float, delta_g_j_per_mol: float, molecularity: int, standard_concentration_mol_per_m3: float=1000.0, kappa: float=1.0) -> float:
    values=(temperature_k,delta_g_j_per_mol,standard_concentration_mol_per_m3,kappa)
    if any(isinstance(v,bool) or not isfinite(float(v)) for v in values):raise ValueError("TST inputs must be finite non-boolean reals")
    if temperature_k<=0 or standard_concentration_mol_per_m3<=0 or kappa<=0 or molecularity<1:raise ValueError("invalid TST domain")
    return kappa*(BOLTZMANN*temperature_k/PLANCK)*exp(-delta_g_j_per_mol/(GAS_CONSTANT*temperature_k))*standard_concentration_mol_per_m3**(1-molecularity)


def model_acceptance(*,dataset_hash:bool,model_hash:bool,code_hash:bool,environment_hash:bool,applicability_domain:bool,calibrated_uncertainty:bool,holdout_validation:bool,independent_approval:bool)->str:
    if all((dataset_hash,model_hash,code_hash,environment_hash,applicability_domain,calibrated_uncertainty,holdout_validation,independent_approval)):return "ACCEPTED"
    return "HOLD"
'''

tests=r'''
from __future__ import annotations
import importlib.util,math,unittest
from pathlib import Path
P=Path(__file__).resolve().parents[1]/"skills/tsao-dft-hpc-provenance/scripts/scientific_contracts_v15.py";S=importlib.util.spec_from_file_location("dft_v15",P);assert S and S.loader;M=importlib.util.module_from_spec(S);S.loader.exec_module(M)
class Tests(unittest.TestCase):
 def test_fatal_overrides_success(self)->None:self.assertEqual(M.final_parse_status(["SUCCESS","FATAL"],expected_terminal_seen=True).status,"FATAL")
 def test_missing_terminal_is_truncated(self)->None:self.assertEqual(M.final_parse_status(["SUCCESS"],expected_terminal_seen=False).status,"TRUNCATED")
 def test_force_shape(self)->None:
  q=M.Quantity((1.0,2.0,3.0,4.0,5.0,6.0),(2,3),"eV/A","force");q.validate()
  with self.assertRaises(ValueError):M.Quantity((1.0,2.0),(2,),"eV/A","force").validate()
 def test_bimolecular_tst_has_inverse_concentration_factor(self)->None:
  k1=M.tst_rate_constant(temperature_k=298.15,delta_g_j_per_mol=50000.0,molecularity=1);k2=M.tst_rate_constant(temperature_k=298.15,delta_g_j_per_mol=50000.0,molecularity=2);self.assertAlmostEqual(k2,k1/1000.0)
 def test_trainer_cannot_self_accept(self)->None:self.assertEqual(M.model_acceptance(dataset_hash=True,model_hash=True,code_hash=True,environment_hash=True,applicability_domain=True,calibrated_uncertainty=True,holdout_validation=True,independent_approval=False),"HOLD")
if __name__=="__main__":unittest.main()
'''

workflow=r'''
name: Skill-native portability
on:
  push:
    branches: [main]
  pull_request:
  workflow_dispatch:
permissions:
  contents: read
jobs:
  validate:
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-24.04, windows-2025]
    runs-on: ${{ matrix.os }}
    timeout-minutes: 12
    steps:
      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262
        with:
          persist-credentials: false
      - run: python scripts/validate_skill.py --root . --report artifacts/skill-validation-v15.json
      - run: python -m unittest tests.test_scientific_contracts_v15 -v
'''

svg_en=r'''
<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900" viewBox="0 0 1600 900"><defs><linearGradient id="g" x2="1" y2="1"><stop stop-color="#08122a"/><stop offset=".5" stop-color="#26375e"/><stop offset="1" stop-color="#090f20"/></linearGradient><linearGradient id="c" x2="1" y2="1"><stop stop-color="#2a4d78"/><stop offset="1" stop-color="#17243f"/></linearGradient></defs><rect width="1600" height="900" fill="url(#g)"/><g opacity=".16" stroke="#79ddff"><path d="M0 180H1600M0 360H1600M0 540H1600M0 720H1600"/><path d="M200 0V900M500 0V900M800 0V900M1100 0V900M1400 0V900"/></g><text x="80" y="100" fill="#fff" font-family="Arial" font-size="50" font-weight="700">TSAO DFT Suite · Fail-Closed Quantum Evidence</text><text x="85" y="148" fill="#b8e9ff" font-family="Arial" font-size="24">Gaussian · VASP · QE · CP2K → quantities → TST → model provenance → independent review</text><g transform="translate(75 225)"><rect width="450" height="405" rx="28" fill="url(#c)" stroke="#54d9ff" stroke-width="2"/><text x="35" y="65" fill="#fff" font-family="Arial" font-size="29" font-weight="700">Parser precedence</text><text x="35" y="130" fill="#c8efff" font-family="Arial" font-size="22">FATAL / TRUNCATED</text><text x="35" y="170" fill="#c8efff" font-family="Arial" font-size="22">&gt; NOT_CONVERGED &gt; SUCCESS</text><text x="35" y="245" fill="#75f0bd" font-family="Arial" font-size="21">Late fatal evidence wins.</text><text x="35" y="285" fill="#75f0bd" font-family="Arial" font-size="21">Missing terminal fails closed.</text><text x="35" y="345" fill="#fff" font-family="Arial" font-size="20">Multi-job and chunk-boundary aware</text></g><g transform="translate(575 225)"><rect width="450" height="405" rx="28" fill="url(#c)" stroke="#b79cff" stroke-width="2"/><text x="35" y="65" fill="#fff" font-family="Arial" font-size="29" font-weight="700">TST & quantity shape</text><text x="35" y="125" fill="#e2d9ff" font-family="Arial" font-size="20">kn = κ kBT/h · exp(−ΔG‡°/RT)</text><text x="35" y="165" fill="#e2d9ff" font-family="Arial" font-size="20">· (c°)^(1−n)</text><text x="35" y="230" fill="#d9f2ff" font-family="Arial" font-size="21">energy scalar · force N×3</text><text x="35" y="270" fill="#d9f2ff" font-family="Arial" font-size="21">stress 3×3 / named Voigt-6</text><text x="35" y="340" fill="#75f0bd" font-family="Arial" font-size="20">Units and conventions are evidence.</text></g><g transform="translate(1075 225)"><rect width="450" height="405" rx="28" fill="url(#c)" stroke="#ffbd65" stroke-width="2"/><text x="35" y="65" fill="#fff" font-family="Arial" font-size="29" font-weight="700">Model acceptance chain</text><text x="35" y="125" fill="#ffe0ad" font-family="Arial" font-size="20">dataset → model → AD/UQ</text><text x="35" y="165" fill="#ffe0ad" font-family="Arial" font-size="20">→ holdout → independent approval</text><text x="35" y="235" fill="#d9f2ff" font-family="Arial" font-size="20">exact code/environment hashes</text><text x="35" y="275" fill="#d9f2ff" font-family="Arial" font-size="20">external solver receipt</text><text x="35" y="340" fill="#75f0bd" font-family="Arial" font-size="20">Trainer cannot self-sign ACCEPTED.</text></g><rect x="75" y="695" width="1450" height="115" rx="24" fill="#071b34" stroke="#4bcdf2"/><text x="115" y="747" fill="#fff" font-family="Arial" font-size="25" font-weight="700">Truth boundary</text><text x="360" y="747" fill="#c7edff" font-family="Arial" font-size="22">External Gaussian/VASP/QE/CP2K execution remains NOT VERIFIED without a signed exact receipt.</text></svg>
'''

svg_zh=r'''
<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900" viewBox="0 0 1600 900"><defs><linearGradient id="g" x2="1" y2="1"><stop stop-color="#08122a"/><stop offset=".5" stop-color="#26375e"/><stop offset="1" stop-color="#090f20"/></linearGradient><linearGradient id="c" x2="1" y2="1"><stop stop-color="#2a4d78"/><stop offset="1" stop-color="#17243f"/></linearGradient></defs><rect width="1600" height="900" fill="url(#g)"/><g opacity=".16" stroke="#79ddff"><path d="M0 180H1600M0 360H1600M0 540H1600M0 720H1600"/><path d="M200 0V900M500 0V900M800 0V900M1100 0V900M1400 0V900"/></g><text x="80" y="100" fill="#fff" font-family="Microsoft YaHei,Arial" font-size="50" font-weight="700">TSAO DFT Suite · 失效闭合量子证据链</text><text x="85" y="148" fill="#b8e9ff" font-family="Microsoft YaHei,Arial" font-size="24">Gaussian · VASP · QE · CP2K → 量值 → TST → 模型谱系 → 独立复核</text><g transform="translate(75 225)"><rect width="450" height="405" rx="28" fill="url(#c)" stroke="#54d9ff" stroke-width="2"/><text x="35" y="65" fill="#fff" font-family="Microsoft YaHei,Arial" font-size="29" font-weight="700">解析优先级</text><text x="35" y="130" fill="#c8efff" font-family="Arial" font-size="22">FATAL / TRUNCATED</text><text x="35" y="170" fill="#c8efff" font-family="Arial" font-size="22">&gt; NOT_CONVERGED &gt; SUCCESS</text><text x="35" y="245" fill="#75f0bd" font-family="Microsoft YaHei,Arial" font-size="21">后出现的致命证据优先</text><text x="35" y="285" fill="#75f0bd" font-family="Microsoft YaHei,Arial" font-size="21">缺终止标记即失效闭合</text><text x="35" y="345" fill="#fff" font-family="Microsoft YaHei,Arial" font-size="20">支持多任务与分块边界</text></g><g transform="translate(575 225)"><rect width="450" height="405" rx="28" fill="url(#c)" stroke="#b79cff" stroke-width="2"/><text x="35" y="65" fill="#fff" font-family="Microsoft YaHei,Arial" font-size="29" font-weight="700">TST与量值形状</text><text x="35" y="125" fill="#e2d9ff" font-family="Arial" font-size="20">kn = κ kBT/h · exp(−ΔG‡°/RT)</text><text x="35" y="165" fill="#e2d9ff" font-family="Arial" font-size="20">· (c°)^(1−n)</text><text x="35" y="230" fill="#d9f2ff" font-family="Microsoft YaHei,Arial" font-size="21">能量标量 · 力 N×3</text><text x="35" y="270" fill="#d9f2ff" font-family="Microsoft YaHei,Arial" font-size="21">应力3×3 / 显式Voigt-6</text><text x="35" y="340" fill="#75f0bd" font-family="Microsoft YaHei,Arial" font-size="20">单位与约定也是证据</text></g><g transform="translate(1075 225)"><rect width="450" height="405" rx="28" fill="url(#c)" stroke="#ffbd65" stroke-width="2"/><text x="35" y="65" fill="#fff" font-family="Microsoft YaHei,Arial" font-size="29" font-weight="700">模型接受链</text><text x="35" y="125" fill="#ffe0ad" font-family="Microsoft YaHei,Arial" font-size="20">数据集 → 模型 → 适用域/UQ</text><text x="35" y="165" fill="#ffe0ad" font-family="Microsoft YaHei,Arial" font-size="20">→ 留出验证 → 独立批准</text><text x="35" y="235" fill="#d9f2ff" font-family="Microsoft YaHei,Arial" font-size="20">精确代码/环境哈希</text><text x="35" y="275" fill="#d9f2ff" font-family="Microsoft YaHei,Arial" font-size="20">真实求解器回执</text><text x="35" y="340" fill="#75f0bd" font-family="Microsoft YaHei,Arial" font-size="20">训练者不得自签ACCEPTED</text></g><rect x="75" y="695" width="1450" height="115" rx="24" fill="#071b34" stroke="#4bcdf2"/><text x="115" y="747" fill="#fff" font-family="Microsoft YaHei,Arial" font-size="25" font-weight="700">真实性边界</text><text x="360" y="747" fill="#c7edff" font-family="Microsoft YaHei,Arial" font-size="22">没有精确签名回执时，外部Gaussian/VASP/QE/CP2K执行保持“未验证”。</text></svg>
'''

readme_en=r'''
## Skill-native DFT suite

![TSAO DFT evidence architecture](assets/diagrams/vision-en.svg)

The canonical Skill is `.agents/skills/tsao-dft-suite/SKILL.md`. It routes the minimum required DFT, parser, TST, provenance, or model-acceptance workflow and progressively loads specialist resources.

Parser status obeys `FATAL/TRUNCATED > NOT_CONVERGED > SUCCESS`. For molecularity \(n\), \(k_n=\kappa k_BT/h\exp(-\Delta G^{\ddagger,\circ}/RT)(c^\circ)^{1-n}\). Model training never self-issues independent acceptance.

```bash
python scripts/validate_skill.py --root . --report artifacts/skill-validation-v15.json
python -m unittest tests.test_scientific_contracts_v15 -v
```
'''

readme_zh=r'''
## Skill 原生 DFT 套件

![TSAO DFT 证据架构](assets/diagrams/vision-zh.svg)

规范 Skill 位于 `.agents/skills/tsao-dft-suite/SKILL.md`。它只路由当前任务需要的 DFT、解析、TST、谱系或模型接受流程，并按需加载专业资源。

解析状态遵循 `FATAL/TRUNCATED > NOT_CONVERGED > SUCCESS`。对分子数 \(n\)，\(k_n=\kappa k_BT/h\exp(-\Delta G^{\ddagger,\circ}/RT)(c^\circ)^{1-n}\)。模型训练不能自行签发独立接受。

```bash
python scripts/validate_skill.py --root . --report artifacts/skill-validation-v15.json
python -m unittest tests.test_scientific_contracts_v15 -v
```
'''

write(".agents/skills/tsao-dft-suite/SKILL.md",skill);write(".agents/skills/tsao-dft-suite/references/definition-of-done.md",dod);write(".agents/skills/tsao-dft-suite/agents/openai.yaml",openai_yaml);write(".agents/skills/tsao-dft-suite/evals/evals.json",json.dumps(evals,ensure_ascii=False,indent=2));write("scripts/validate_skill.py",validator);write("skills/tsao-dft-hpc-provenance/scripts/scientific_contracts_v15.py",contracts);write("tests/test_scientific_contracts_v15.py",tests);write(".github/workflows/skill-native-ci.yml",workflow);write("assets/diagrams/vision-en.svg",svg_en);write("assets/diagrams/vision-zh.svg",svg_zh);merge("README.md",readme_en,"TSAO DFT Suite");zh="README.zh-CN.md" if (ROOT/"README.zh-CN.md").exists() else "README_CN.md";merge(zh,readme_zh,"TSAO DFT Suite 中文说明");print(json.dumps({"status":"APPLIED","version":"15.0.0"},ensure_ascii=False))
