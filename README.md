# TsaoDFT Skill

<p align="center"><strong>结构审查 → 分子/周期 DFT → 技术验收 → 波函数与材料性质 → HPC溯源 → ML/动力学 → 证据与图件</strong></p>

<p align="center"><a href="README.md">中文</a> · <a href="README_EN.md">English</a></p>

<p align="center">
  <a href="https://github.com/SUNHAOJUN22/TsaoDFT_skill/actions/workflows/ci.yml"><img src="https://github.com/SUNHAOJUN22/TsaoDFT_skill/actions/workflows/ci.yml/badge.svg?branch=main" alt="CI"></a>
  <img src="https://img.shields.io/badge/Python-3.10%20%7C%203.12%20%7C%203.13-3776AB" alt="Python versions">
  <img src="https://img.shields.io/badge/DFT--first-auditable-6D5DFB" alt="DFT first">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT license">
</p>

<p align="center">
  <img src="assets/ai/hero/tsao-dft-hero.svg" alt="TsaoDFT AI-generated conceptual hero" width="100%">
</p>

> **AI图像声明：** 上方主视觉及文中的模块场景图属于 `AI-GENERATED CONCEPTUAL ILLUSTRATION`，仅用于表达研究场景与平台定位，不是分子结构、轨道、ESP、能带、自由能、反应机理或实验结果。定量内容必须由仓库脚本或经过验收的真实数据生成。

`TsaoDFT_skill` 是一套以 **DFT证据链** 为中心的 Agent Skills 仓库。它不把“支持某个软件”写成空泛口号，而是区分方法参考、结构化交接、确定性适配器和真实引擎回归四个等级。

```text
scientific question
→ reviewed structure campaign
→ molecular/periodic method fingerprint
→ preflight + approval
→ DFT engine execution
→ technical validation
→ quantitative analysis
→ accepted artifact
→ optional ML / kinetics
→ calculation–artifact–claim audit
```

![TsaoDFT workflow](assets/demo/workflow-architecture.svg)

README采用双轨图像体系：`assets/ai/` 保存有生成记录和用途边界的AI概念图；`assets/demo/` 保存由脚本和模拟源数据确定性生成的科研演示图。治理规则见 [`docs/AI_IMAGE_GOVERNANCE.md`](docs/AI_IMAGE_GOVERNANCE.md)。

## 8个DFT相关Skills

| Skill | 适用工作 | 深度与边界 |
|---|---|---|
| [`tsao-dft-suite`](skills/tsao-dft-suite/) | 仓库总入口；建立DFT任务DAG、方法指纹、跨Skill交接、成本和审批门 | 只负责DFT优先编排，不替代引擎Skill |
| [`tsao-structure-prep`](skills/tsao-structure-prep/) | 分子、配合物、晶体、表面、缺陷、吸附与候选结构矩阵 | 不静默决定电荷、自旋、终止面或氧化态 |
| [`tsao-dft-researcher`](skills/tsao-dft-researcher/) | Gaussian分子DFT/TDDFT、Opt/Freq、TS/IRC、热化学、NMR、Multiwfn、VMD及证据审计 | 当前最深的分子DFT适配器；真实软件仍由用户提供 |
| [`tsao-periodic-dft-materials`](skills/tsao-periodic-dft-materials/) | VASP、QE、CP2K周期DFT、表面/缺陷、能带/DOS、NEB、声子和收敛 | 不分发POTCAR、赝势或受限数据 |
| [`tsao-dft-hpc-provenance`](skills/tsao-dft-hpc-provenance/) | 本地/Slurm/PBS脚本、资源估算、站点Profile、检查点和重启谱系 | 负责执行机制，不决定泛函、基组、U值或模型 |
| [`tsao-dft-ml-active-learning`](skills/tsao-dft-ml-active-learning/) | DFT标签、泄漏审计、基线模型、适用域、主动学习和逆向设计 | SHAP和相关性不是机理或因果证据 |
| [`tsao-dft-kinetics-multiscale`](skills/tsao-dft-kinetics-multiscale/) | Eyring/TST、反应网络、详细平衡、速率不确定度及Cantera/CatMAP/Pyomo交接 | 只消费已接受DFT热化学 |
| [`tsao-dft-catalysis-profile`](skills/tsao-dft-catalysis-profile/) | DCS/MCSOMe/DMOS、Si–O/Si–C、Ti/TEA、Ziegler–Natta和聚烯烃催化问题 | 专用Profile，不得用于无关体系 |

## AI生成科研场景图集

下面不是单纯流程框，而是围绕不同DFT工作场景生成的概念视觉。它们用于README叙事和模块识别；任何数值、结构、轨道、表面、能带或反应机理仍须由真实计算与确定性图件支持。

<table>
<tr>
<td width="50%" align="center"><img src="assets/ai/modules/molecular-dft.svg" alt="AI molecular DFT concept" width="100%"><br><strong>分子DFT与波函数分析</strong></td>
<td width="50%" align="center"><img src="assets/ai/modules/periodic-dft.svg" alt="AI periodic DFT concept" width="100%"><br><strong>周期DFT、表面与缺陷</strong></td>
</tr>
<tr>
<td align="center"><img src="assets/ai/modules/dft-ml.svg" alt="AI DFT ML concept" width="100%"><br><strong>DFT标签与主动学习</strong></td>
<td align="center"><img src="assets/ai/modules/dft-kinetics.svg" alt="AI DFT kinetics concept" width="100%"><br><strong>DFT到速率与多尺度</strong></td>
</tr>
<tr>
<td align="center"><img src="assets/ai/modules/hpc-provenance.svg" alt="AI HPC provenance concept" width="100%"><br><strong>HPC、检查点与溯源</strong></td>
<td align="center"><img src="assets/ai/modules/catalysis.svg" alt="AI catalysis concept" width="100%"><br><strong>催化与聚烯烃专用Profile</strong></td>
</tr>
<tr>
<td colspan="2" align="center"><img src="assets/ai/modules/ecosystem.svg" alt="AI TsaoDFT ecosystem concept" width="76%"><br><strong>DFT证据链生态总览</strong></td>
</tr>
</table>

所有AI视觉均登记于 [`assets/ai/manifest.yaml`](assets/ai/manifest.yaml)，并由 `validate_ai_assets.py` 与 `validate_readme_visuals.py` 双重校验。

## 支持等级

| 等级 | 含义 |
|---|---|
| `L0_REFERENCE` | 只有方法与边界说明 |
| `L1_HANDOFF` | 能输出结构化Manifest或交接文件 |
| `L2_VALIDATED_ADAPTER` | 有确定性预检、解析、验证脚本和测试 |
| `L3_EXECUTION_TESTED` | L2基础上，已在真实引擎、版本和站点完成回归 |

当前Gaussian、VASP、QE和CP2K属于**选定字段的L2适配器**，不是完整解析器，也没有在当前交付环境声称L3。详见 [`docs/ENGINE_SUPPORT_MATRIX.md`](docs/ENGINE_SUPPORT_MATRIX.md) 和 [`docs/CAPABILITY_STATUS.yaml`](docs/CAPABILITY_STATUS.yaml)。

## 分子DFT：Gaussian → Multiwfn → VMD

核心能力：Gaussian输入预检；route、方法/基组、溶剂、色散、积分网格和作业类型提取；SCF、优化、频率、热化学、S²、稳定性、轨道能、偶极矩、NMR、TD跃迁组分和最终坐标解析；TS虚频、正反向IRC和端点证据门；Multiwfn语义配方；VMD/Tachyon统一渲染；DFT不确定度预算。

![Wavefunction and ESP](assets/demo/wavefunction-esp-gallery.svg)

```bash
python skills/tsao-dft-researcher/scripts/preflight_gaussian_input.py job.gjf --json
python skills/tsao-dft-researcher/scripts/parse_gaussian.py job.log --json --out parsed.json
python skills/tsao-dft-researcher/scripts/validate_multiwfn_recipe.py recipe.yaml
python skills/tsao-dft-researcher/scripts/validate_uncertainty_budget.py uncertainty.yaml
```

## 周期DFT：VASP / QE / CP2K

- **VASP**：INCAR、POSCAR、KPOINTS、POTCAR `TITEL`顺序，OUTCAR总能、电子/离子收敛、力、费米能和计时；
- **Quantum ESPRESSO**：`pw.x` namelist、结构卡、赝势文件名、cutoff、k点、自旋，总能、SCF、力、压力和费米能；
- **CP2K**：RUN_TYPE、MOLOPT/GTH文件、CUTOFF/REL_CUTOFF、KIND、PBC/Poisson和SCF，总能与几何收敛；
- cutoff、k点、超胞、真空和其他单参数收敛分析；
- 吸附、缺陷、表面和NEB任务专用Manifest门。

![Periodic DFT](assets/demo/periodic-dft-materials.svg)

## DFT＋ML闭环

模型训练前必须固定独立样本单位。构象、电荷态、自旋态、重复计算或随机种子不自动成为独立样本。已实现方法指纹和保真度审计、跨split泄漏检查、分组ridge基线、model card、适用域警告和active-learning候选选择。

![Active learning](assets/demo/active-learning-loop.svg)

## HPC与计算溯源

记录引擎版本、模块、队列、MPI/OpenMP/GPU布局、资源上界、scratch、实际脚本、输入输出哈希和重启谱系。调度成功只说明进程结束，不代表科学接受。

![HPC provenance](assets/demo/hpc-provenance.svg)

## DFT到速率与多尺度

只有在温度、相态、标准态、反应物参考、路径简并度、隧穿和分子数约定清楚时，DFT势垒才能转成速率。已实现元素/电荷/位点守恒、正反势垒闭合、Eyring速率、势垒不确定度传播和审查型Cantera交接。

![Multiscale kinetics](assets/demo/multiscale-kinetics.svg)

## AI视觉资产与科研图件边界

| 图像类型 | 允许用途 | 禁止用途 |
|---|---|---|
| AI概念图（`assets/ai/`） | README封面、研究场景、模块视觉识别 | 轨道、ESP、能带、结构、机理、自由能等定量证据 |
| 确定性演示图（`assets/demo/`） | 展示图件标准、Schema和绘图风格 | 冒充真实计算或实验结果 |
| 真实科研图 | 论文、报告、SI和结论证据 | 脱离源数据、方法指纹和验收状态使用 |

## 安装

```bash
python scripts/install.py --list
python scripts/install.py --agent codex --scope user --skill all --dry-run --validate
python scripts/install.py --agent codex --scope user --skill all
```

## 自动验证与托管证明

常规 `CI` 在每次推送到 `main` 时使用Python 3.10、3.12和3.13运行。`CI Attestation` 不创建分支，只有GitHub托管runner完成全部检查后，才会由 `github-actions[bot]` 更新 [`docs/CI_VERIFIED.md`](docs/CI_VERIFIED.md)。

```bash
python -m pip install -r requirements.txt
python scripts/generate_readme_demos.py
python scripts/validate_catalog.py
python scripts/validate_ai_assets.py
python scripts/validate_readme_visuals.py --strict
python scripts/validate_repo.py --strict
python scripts/run_all_tests.py
```

仓库规则：**只在 `main` 工作，不创建功能、修复或发布分支。**项目运行状态写入 `.research/`，发布版本使用tag和Release。

## 事实与许可证边界

本仓库不包含Gaussian、VASP、POTCAR、QE赝势、CP2K基组/势文件、Multiwfn、VMD/Tachyon、DeepChem、Cantera或调度器。当前环境完成的是脚本、Manifest、合成fixture和图件的确定性测试，没有声称完成真实授权生产计算。科学接受始终需要研究者审核。
