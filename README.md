# TsaoDFT Skill

<p align="center">
  <strong>面向分子与周期体系的 DFT-first、证据锁定、可审计科研工作流</strong><br>
  结构审查 → 方法指纹 → 计算执行 → 技术验收 → 性质分析 → 多尺度交接 → 图件与主张审计
</p>

<p align="center">
  <a href="README.md">中文</a> · <a href="README_EN.md">English</a>
</p>

<p align="center">
  <a href="https://github.com/SUNHAOJUN22/TsaoDFT_skill/actions/workflows/ci.yml"><img src="https://github.com/SUNHAOJUN22/TsaoDFT_skill/actions/workflows/ci.yml/badge.svg?branch=main" alt="CI"></a>
  <img src="https://img.shields.io/badge/Python-3.10%20%7C%203.12%20%7C%203.13-3776AB" alt="Python 3.10, 3.12 and 3.13">
  <img src="https://img.shields.io/badge/tests-68%20passing-16A34A" alt="68 tests passing">
  <img src="https://img.shields.io/badge/support-L0%E2%80%93L3-6D5DFB" alt="Support levels L0 to L3">
  <img src="https://img.shields.io/badge/license-MIT-16A34A" alt="MIT license">
</p>

> **AI图像声明｜AI-GENERATED CONCEPTUAL ILLUSTRATION：** 下方封面是 AI 辅助的概念图，仅用于表达项目定位；它不是分子结构、轨道、静电势、能带、自由能、反应机理或实验结果。所有定量结论必须来自经过验收的计算数据、源文件和可复现脚本。

<p align="center">
  <img src="assets/ai/hero/tsao-dft-hero.svg" width="100%" alt="TsaoDFT AI-assisted conceptual cover">
</p>

## 项目定位

`TsaoDFT_skill` 以 **DFT 证据链** 为核心。它不把“程序正常结束”“图像看起来合理”或“模型分数较高”直接等同于科学结论，而是把每项工作拆分为可检查状态：

```text
planned → prepared → completed → technically validated → scientifically accepted → claim accepted
```

核心原则：**计算、产物和论文主张必须逐级可追溯，未解决的假设不得被静默隐藏。**

<p align="center">
  <img src="assets/demo/workflow-architecture.svg" width="100%" alt="Auditable DFT research loop synthetic demo">
</p>

## 8 个可组合 Skills

| Skill | 主要用途 | 关键边界 |
|---|---|---|
| [`tsao-dft-suite`](skills/tsao-dft-suite/) | DFT-first 总入口、任务 DAG、支持等级路由、成本与审批门 | 负责协调，不替代引擎级判断 |
| [`tsao-structure-prep`](skills/tsao-structure-prep/) | 分子、晶体、表面、缺陷、吸附结构与原子映射 | 不静默决定电荷、自旋、氧化态或终止面 |
| [`tsao-dft-researcher`](skills/tsao-dft-researcher/) | Gaussian 分子 DFT/TDDFT、Opt/Freq、TS/IRC、热化学、NMR、Multiwfn、VMD | 当前最深的分子 DFT 适配器；真实软件由用户环境提供 |
| [`tsao-periodic-dft-materials`](skills/tsao-periodic-dft-materials/) | VASP、Quantum ESPRESSO、CP2K，表面、缺陷、能带/DOS、NEB 与收敛 | 不分发 POTCAR、赝势或受限数据库 |
| [`tsao-dft-hpc-provenance`](skills/tsao-dft-hpc-provenance/) | 本地/Slurm/PBS、资源估算、检查点、重启谱系与哈希 | 调度成功不等于科学验收 |
| [`tsao-dft-ml-active-learning`](skills/tsao-dft-ml-active-learning/) | DFT 标签审计、泄漏防护、适用域、不确定度与主动学习 | 相关性和 SHAP 不能替代因果或机理证据 |
| [`tsao-dft-kinetics-multiscale`](skills/tsao-dft-kinetics-multiscale/) | Eyring/TST、反应网络、详细平衡、误差传播与微观动力学交接 | 只消费标准态和热化学校验通过的 DFT 数据 |
| [`tsao-dft-catalysis-profile`](skills/tsao-dft-catalysis-profile/) | DCS/MCSOMe/DMOS、Si–O/Si–C、Ti/TEA、Ziegler–Natta 与聚烯烃催化 | 专用 Profile，不自动外推到无关体系 |

## 精选科研演示

README 只展示最能代表核心能力的图件，避免形成重复的“功能海报墙”。仓库中的 8 张确定性演示 SVG 仍全部接受 XML、尺寸、标题、可访问性描述和非数据标签校验；这里只精选 4 张，加上前面的工作流总览。

<table>
<tr>
<td width="50%"><img src="assets/demo/wavefunction-esp-gallery.svg" width="100%" alt="Wavefunction and ESP figure contract"></td>
<td width="50%"><img src="assets/demo/periodic-dft-materials.svg" width="100%" alt="Periodic DFT evidence"></td>
</tr>
<tr>
<td><img src="assets/demo/dft-ml-dashboard.svg" width="100%" alt="DFT ML evidence dashboard"></td>
<td><img src="assets/demo/multiscale-kinetics.svg" width="100%" alt="DFT to kinetics multiscale handoff"></td>
</tr>
</table>

所有演示图均标注 `SYNTHETIC DEMO · NOT SCIENTIFIC DATA`，用于展示图件规范与证据门，不是生产计算结果。兼容命令 [`scripts/generate_readme_demos.py`](scripts/generate_readme_demos.py) 是严格只读校验器，不会自动写入占位图。

## 支持等级

| 等级 | 含义 |
|---|---|
| `L0_REFERENCE` | 只有方法、边界和参考说明 |
| `L1_HANDOFF` | 能生成结构化 Manifest 或下游交接文件 |
| `L2_VALIDATED_ADAPTER` | 有确定性预检、解析、验证脚本及仓库测试 |
| `L3_EXECUTION_TESTED` | 在 L2 基础上，有真实引擎、版本和环境的不可变回归证据 |

Gaussian、VASP、Quantum ESPRESSO 和 CP2K 当前提供选定字段的 **L2 适配器**。仓库不会在缺少合法真实引擎回归记录时宣称 L3。

## 安装

```bash
python scripts/install.py --list
python scripts/install.py --agent codex --scope user --skill all --dry-run --validate
python scripts/install.py --agent codex --scope user --skill all
```

## 一键质量门

```bash
python -m pip install -r requirements-dev.txt
python scripts/quality_gate.py
```

```text
validate all versioned demo assets
→ catalog validation
→ minimal AI-cover integrity and provenance
→ curated README visual completeness
→ Ruff lint
→ Ruff formatting check
→ strict repository audit
→ all non-empty unittest suites
```

需要单独定位问题时：

```bash
python scripts/generate_readme_demos.py
python scripts/validate_catalog.py
python scripts/validate_ai_assets.py
python scripts/validate_readme_visuals.py --strict
python -m ruff check .
python -m ruff format --check .
python scripts/validate_repo.py --strict
python scripts/run_all_tests.py
```

## 科学边界

本仓库不分发 Gaussian、VASP、Quantum ESPRESSO、CP2K、Multiwfn、VMD、POTCAR、赝势或受限基组/势函数库，也不绕过许可证。真实生产计算必须在用户合法配置的环境中执行。

进一步阅读：

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- [`docs/ENGINE_SUPPORT_MATRIX.md`](docs/ENGINE_SUPPORT_MATRIX.md)
- [`docs/CAPABILITY_STATUS.yaml`](docs/CAPABILITY_STATUS.yaml)
- [`docs/SCIENTIFIC_BOUNDARIES.md`](docs/SCIENTIFIC_BOUNDARIES.md)
- [`docs/AI_IMAGE_GOVERNANCE.md`](docs/AI_IMAGE_GOVERNANCE.md)
- [`docs/TEST_REPORT.md`](docs/TEST_REPORT.md)

仓库维护策略：只在 `main` 上工作；发布快照使用 Tags / Releases，不创建功能、修复或临时分支。
