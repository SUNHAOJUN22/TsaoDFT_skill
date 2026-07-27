# TsaoDFT Skill

<p align="center">
  <strong>面向分子与周期体系的 DFT-first、证据锁定、可审计科研操作系统</strong><br>
  从结构准备、计算执行与技术验收，到波函数分析、机器学习、动力学、多尺度交接与论文主张审计
</p>

<p align="center">
  <a href="README.md">中文</a> · <a href="README_EN.md">English</a>
</p>

<p align="center">
  <a href="https://github.com/SUNHAOJUN22/TsaoDFT_skill/actions/workflows/ci.yml"><img src="https://github.com/SUNHAOJUN22/TsaoDFT_skill/actions/workflows/ci.yml/badge.svg?branch=main" alt="CI"></a>
  <img src="https://img.shields.io/badge/Python-3.10%20%7C%203.12%20%7C%203.13-3776AB" alt="Python 3.10, 3.12 and 3.13">
  <img src="https://img.shields.io/badge/tests-92%20passing-16A34A" alt="92 tests passing">
  <img src="https://img.shields.io/badge/support-L0%E2%80%93L3-6D5DFB" alt="Support levels L0 to L3">
  <img src="https://img.shields.io/badge/license-MIT-16A34A" alt="MIT license">
</p>

> **AI图像声明｜AI-GENERATED CONCEPTUAL ILLUSTRATION：** 下方深色总览图是 AI 辅助的概念性视觉，只用于呈现项目定位、能力边界和工作流结构；图中的分子、晶格、服务器、轨道与图表不是 Gaussian、VASP、Quantum ESPRESSO、CP2K、Multiwfn、VMD 或实验产生的结果。所有定量结论必须来自经过验收的源文件、计算产物和可复现脚本。

<p align="center">
  <img src="assets/ai/hero/tsao-dft-hero.svg" width="100%" alt="TsaoDFT dark scientific research operating system conceptual overview">
</p>

## 为什么是 TsaoDFT

`TsaoDFT_skill` 不是一组彼此孤立的提示词，也不把“程序运行结束”“图像看起来合理”或“模型分数较高”直接升级为科学结论。它把计算研究组织为一条可追踪的证据链：

```text
planned
→ prepared
→ completed
→ technically validated
→ scientifically accepted
→ claim accepted
```

| 核心原则 | TsaoDFT 的处理方式 |
|---|---|
| **模型身份清楚** | 结构、电荷、自旋、原子顺序、方法指纹和参考态显式记录 |
| **计算结果可审计** | 输入、实际执行脚本、软件版本、输出、哈希、重启谱系与失败尝试均可追溯 |
| **技术验收与科学验收分开** | 正常终止不等于结构、能量、频率、电子态或机理已被科学接受 |
| **主张强度受证据约束** | 图、表、模型解释和论文语句必须有对应源产物、适用范围与不确定度 |
| **自动化不绕过审批** | 高成本计算、HPC 提交、方法变更和破坏性操作仍需要明确授权 |

## 研究操作系统

<p align="center">
  <img src="assets/demo/workflow-architecture.svg" width="100%" alt="TsaoDFT auditable research loop synthetic demonstration">
</p>

每一次状态跃迁都应同时回答四个问题：

1. **谁负责验收？**
2. **验收依据是什么产物？**
3. **使用了哪个方法指纹与软件环境？**
4. **尚未解决的假设和主张边界是什么？**

## 八个可组合 Skills

| Skill | 主要用途 | 关键科学边界 |
|---|---|---|
| [`tsao-dft-suite`](skills/tsao-dft-suite/) | DFT-first 总入口、任务 DAG、跨 Skill 路由、成本与审批门 | 负责协调，不替代引擎级科学判断 |
| [`tsao-structure-prep`](skills/tsao-structure-prep/) | 分子、构象、晶体、表面、缺陷、吸附结构与原子映射 | 不静默决定电荷、自旋、氧化态、终止面或质子化状态 |
| [`tsao-dft-researcher`](skills/tsao-dft-researcher/) | Gaussian 分子 DFT/TDDFT、Opt/Freq、TS/IRC、热化学、NMR、Multiwfn、VMD | 真实程序与许可证由用户环境提供；适配器不伪造运行结果 |
| [`tsao-periodic-dft-materials`](skills/tsao-periodic-dft-materials/) | VASP、Quantum ESPRESSO、CP2K，表面、缺陷、能带/DOS、NEB 与收敛 | 不分发 POTCAR、赝势或受限数据库；不可混用不兼容能量 |
| [`tsao-dft-hpc-provenance`](skills/tsao-dft-hpc-provenance/) | 本地/Slurm/PBS、资源估算、数组任务、检查点、重启谱系与哈希 | 调度器成功只表示进程结束，不代表科学验收 |
| [`tsao-dft-ml-active-learning`](skills/tsao-dft-ml-active-learning/) | DFT 标签审计、泄漏防护、适用域、不确定度、主动学习与反向设计 | 高 R²、SHAP 或 acquisition score 不能自动证明机理、因果或可合成性 |
| [`tsao-dft-kinetics-multiscale`](skills/tsao-dft-kinetics-multiscale/) | Eyring/TST、反应网络、详细平衡、误差传播、微观动力学与反应器交接 | 只消费标准态、参考态和热化学校验通过的数据 |
| [`tsao-dft-catalysis-profile`](skills/tsao-dft-catalysis-profile/) | DCS/MCSOMe/DMOS、Si–O/Si–C、Ti/TEA、Ziegler–Natta 与聚烯烃催化 | 专用 Profile，不自动外推到无关催化体系 |

## 支持等级

| 等级 | 含义 |
|---|---|
| `L0_REFERENCE` | 只有方法说明、科学边界和参考资料 |
| `L1_HANDOFF` | 能生成结构化 Manifest 或下游交接文件 |
| `L2_VALIDATED_ADAPTER` | 有确定性预检、解析、验证脚本和仓库测试 |
| `L3_EXECUTION_TESTED` | 在 L2 基础上，有真实引擎、版本、场站和不可变回归证据 |

Gaussian、VASP、Quantum ESPRESSO 和 CP2K 当前提供选定字段的 **L2 适配器**。仓库不会在缺少合法真实引擎回归材料时宣称 L3。

## 精选科研演示

以下图件由仓库脚本和固定合成数据生成，全部标注 `SYNTHETIC DEMO · NOT SCIENTIFIC DATA`。它们用于展示图件合同、证据门和结果组织方式，不是生产计算数据。

<table>
<tr>
<td width="50%"><img src="assets/demo/wavefunction-esp-gallery.svg" width="100%" alt="Wavefunction and ESP figure contract"></td>
<td width="50%"><img src="assets/demo/periodic-dft-materials.svg" width="100%" alt="Periodic DFT evidence chain"></td>
</tr>
<tr>
<td><img src="assets/demo/dft-ml-dashboard.svg" width="100%" alt="DFT ML provenance-aware dashboard"></td>
<td><img src="assets/demo/multiscale-kinetics.svg" width="100%" alt="DFT to kinetics multiscale handoff"></td>
</tr>
</table>

其他确定性演示还包括：

- [`free-energy-profile.svg`](assets/demo/free-energy-profile.svg)：自由能、TS、IRC 与标准态验收；
- [`active-learning-loop.svg`](assets/demo/active-learning-loop.svg)：主动学习目标、约束、批次与停止准则；
- [`hpc-provenance.svg`](assets/demo/hpc-provenance.svg)：HPC 执行、检查点、解析与不可变谱系；
- [`workflow-architecture.svg`](assets/demo/workflow-architecture.svg)：跨阶段证据账本。

完整视觉系统、配色、排版、密度、反模式与可访问性清单见 [`docs/README_VISUAL_DESIGN_SYSTEM.md`](docs/README_VISUAL_DESIGN_SYSTEM.md)。

## 计算效率架构

本仓库已经实现并测试的效率优化包括：

| 热点 | 当前实现 | 边界 |
|---|---|---|
| VASP / QE / CP2K 大型输出 | 只读 `mmap`、bytes 正则、末值聚合，避免整文件反复解码 | 不改变字段与验收判据 |
| DFT-ML Ridge | 按训练矩阵形状自动选择 primal / dual；`alpha = 0` 使用稳定最小二乘 | 不把基线模型包装成机理证据 |
| 文件与数据集哈希 | 分块 SHA-256 与有界规范编码 | 缓存不能跨越文件内容或方法指纹变化 |
| HPC 同构任务 | Slurm Job Array + JSONL 任务表 + 并发上限 | 生成器不自动提交真实作业 |
| 线程与资源 | OpenMP、BLAS、MPI 与节点容量显式检查 | 不自动增加资源或延长 walltime |

进一步阅读：

- [`docs/PERFORMANCE_AUDIT.md`](docs/PERFORMANCE_AUDIT.md)
- [`docs/PERFORMANCE_GUIDE.md`](docs/PERFORMANCE_GUIDE.md)

## 快速开始

列出可安装 Skills：

```bash
python scripts/install.py --list
```

在用户级 Codex 环境进行无写入验证：

```bash
python scripts/install.py \
  --agent codex \
  --scope user \
  --skill all \
  --dry-run \
  --validate
```

正式安装全部 Skills：

```bash
python scripts/install.py \
  --agent codex \
  --scope user \
  --skill all
```

真实计算开始前，仍需由用户提供合法的引擎、许可证、赝势/基组、场站指南和执行权限。

## 一键质量门

```bash
python -m pip install -r requirements-dev.txt
python scripts/quality_gate.py
```

质量门顺序：

```text
validate all versioned demo assets
→ catalog validation
→ governed AI-cover integrity and provenance
→ bilingual README visual completeness
→ offline README local-link validation
→ Ruff lint
→ Ruff formatting check
→ strict repository audit
→ all non-empty unittest suites
```

单独定位问题：

```bash
python scripts/generate_readme_demos.py
python scripts/validate_catalog.py
python scripts/validate_ai_assets.py
python scripts/validate_readme_visuals.py --strict
python scripts/validate_readme_links.py
python scripts/benchmark_performance.py --quick
python -m ruff check .
python -m ruff format --check .
python scripts/validate_repo.py --strict
python scripts/run_all_tests.py
```

## 科学边界

本仓库：

- 不分发 Gaussian、VASP、Quantum ESPRESSO、CP2K、Multiwfn、VMD、POTCAR、赝势或受限基组/势函数库；
- 不绕过许可证、场站规定或软件访问控制；
- 不把 AI 概念图描述为轨道、ESP、能带、自由能、过渡态、机理或实验结果；
- 不把正常终止、调度成功、模型分数或漂亮图形直接等同于科学接受；
- 不在缺少真实引擎回归证据时宣称 `L3_EXECUTION_TESTED`。

## 文档地图

| 文档 | 内容 |
|---|---|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | 总体架构和状态流 |
| [`docs/ENGINE_SUPPORT_MATRIX.md`](docs/ENGINE_SUPPORT_MATRIX.md) | 引擎支持范围与等级 |
| [`docs/CAPABILITY_STATUS.yaml`](docs/CAPABILITY_STATUS.yaml) | 机器可读能力状态 |
| [`docs/SCIENTIFIC_BOUNDARIES.md`](docs/SCIENTIFIC_BOUNDARIES.md) | 科学边界与非主张 |
| [`docs/CROSS_SKILL_HANDOFF.md`](docs/CROSS_SKILL_HANDOFF.md) | 跨 Skill 交接合同 |
| [`docs/AI_IMAGE_GOVERNANCE.md`](docs/AI_IMAGE_GOVERNANCE.md) | AI 图像治理 |
| [`docs/README_VISUAL_DESIGN_SYSTEM.md`](docs/README_VISUAL_DESIGN_SYSTEM.md) | README 深色科研视觉系统 |
| [`docs/TEST_REPORT.md`](docs/TEST_REPORT.md) | 测试、视觉与工程门禁报告 |

仓库维护策略：直接在 `main` 上工作；发布快照使用 Tags / Releases，不创建长期功能、修复或临时分支。
