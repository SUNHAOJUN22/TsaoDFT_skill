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
  <img src="https://img.shields.io/badge/support-L0%E2%80%93L3-6D5DFB" alt="Support levels L0 to L3">
  <img src="https://img.shields.io/badge/license-MIT-16A34A" alt="MIT license">
</p>

> **AI图像声明｜AI-GENERATED CONCEPTUAL ILLUSTRATION：** 下方主视觉与模块卡片属于 AI 生成或 AI 辅助的概念图，仅用于表达 TsaoDFT 的研究场景与软件定位。它们不是分子结构、轨道、静电势、能带、自由能、反应机理或实验结果。所有定量结论必须来自经过验收的计算数据、源文件和可复现脚本。

<p align="center">
  <img src="assets/ai/hero/tsao-dft-hero.svg" width="100%" alt="TsaoDFT AI-assisted conceptual architecture">
</p>

## 项目定位

`TsaoDFT_skill` 是一套以 **DFT 证据链** 为核心的 Agent Skills 仓库。它不把“程序正常结束”“图像看起来合理”或“模型分数较高”直接等同于科学结论，而是把每一项工作拆分为可检查的状态：

```text
planned → prepared → completed → technically validated → scientifically accepted → claim accepted
```

核心原则只有一句：**计算、产物和论文主张必须能够逐级追溯，且未解决的假设不能被静默隐藏。**

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

## 概念场景图集

所有概念图均登记在 [`assets/ai/manifest.yaml`](assets/ai/manifest.yaml)，包含尺寸、SHA-256、生成记录、允许用途和禁止用途。它们只负责讲清“模块做什么”，不承担任何定量证据。

<table>
<tr>
<td width="50%" align="center"><img src="assets/ai/modules/molecular-dft.svg" width="100%" alt="Molecular DFT concept"><br><strong>分子 DFT 与波函数证据</strong></td>
<td width="50%" align="center"><img src="assets/ai/modules/periodic-dft.svg" width="100%" alt="Periodic DFT concept"><br><strong>周期 DFT、表面与缺陷</strong></td>
</tr>
<tr>
<td align="center"><img src="assets/ai/modules/dft-ml.svg" width="100%" alt="DFT and ML concept"><br><strong>DFT 标签、机器学习与主动学习</strong></td>
<td align="center"><img src="assets/ai/modules/dft-kinetics.svg" width="100%" alt="DFT kinetics concept"><br><strong>DFT 到动力学与多尺度模型</strong></td>
</tr>
<tr>
<td align="center"><img src="assets/ai/modules/hpc-provenance.svg" width="100%" alt="HPC provenance concept"><br><strong>HPC 执行、哈希与重启谱系</strong></td>
<td align="center"><img src="assets/ai/modules/catalysis.svg" width="100%" alt="Catalysis concept"><br><strong>催化与聚烯烃专用 Profile</strong></td>
</tr>
<tr>
<td colspan="2" align="center"><img src="assets/ai/modules/ecosystem.svg" width="76%" alt="TsaoDFT evidence ecosystem concept"><br><strong>统一 DFT 证据生态</strong></td>
</tr>
</table>

## 确定性科研演示

下列 SVG 是版本化、确定性的合成演示资产，并在图内标注 `SYNTHETIC DEMO · NOT SCIENTIFIC DATA`。为兼容既有命令，校验入口仍保留为 [`scripts/generate_readme_demos.py`](scripts/generate_readme_demos.py)，但它现在是**严格只读校验器**：检查 XML、尺寸、标题、可访问性描述、README 引用和非数据标签；图片缺失、退化或出现占位内容时质量门直接失败，绝不自动写入低质量 placeholder。

<table>
<tr>
<td width="50%"><img src="assets/demo/wavefunction-esp-gallery.svg" width="100%" alt="Wavefunction and ESP figure contract"></td>
<td width="50%"><img src="assets/demo/free-energy-profile.svg" width="100%" alt="Free energy evidence gates"></td>
</tr>
<tr>
<td><img src="assets/demo/periodic-dft-materials.svg" width="100%" alt="Periodic DFT evidence"></td>
<td><img src="assets/demo/dft-ml-dashboard.svg" width="100%" alt="DFT ML evidence dashboard"></td>
</tr>
<tr>
<td><img src="assets/demo/active-learning-loop.svg" width="100%" alt="Active learning provenance loop"></td>
<td><img src="assets/demo/hpc-provenance.svg" width="100%" alt="HPC provenance"></td>
</tr>
<tr>
<td colspan="2" align="center"><img src="assets/demo/multiscale-kinetics.svg" width="88%" alt="DFT to kinetics multiscale handoff"></td>
</tr>
</table>

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
python -m pip install -r requirements.txt
python scripts/quality_gate.py
```

质量门按固定顺序执行：

```text
validate versioned demo assets
→ catalog validation
→ AI asset integrity and provenance
→ README visual completeness
→ strict repository audit
→ all unittest suites
```

需要单独定位问题时，可运行：

```bash
python scripts/generate_readme_demos.py
python scripts/validate_catalog.py
python scripts/validate_ai_assets.py
python scripts/validate_readme_visuals.py --strict
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
