# TsaoDFT Skill

<p align="center">
  <strong>面向分子与周期体系的 DFT-first、证据锁定、可审计科研操作系统</strong><br>
  从结构准备与真实引擎执行，到波函数、材料性质、机器学习、动力学、HPC 溯源与论文主张审计
</p>

<p align="center">
  <a href="README.md">中文</a> · <a href="README_EN.md">English</a>
</p>

<p align="center">
  <a href="https://github.com/SUNHAOJUN22/TsaoDFT_skill/actions/workflows/ci.yml"><img src="https://github.com/SUNHAOJUN22/TsaoDFT_skill/actions/workflows/ci.yml/badge.svg?branch=main" alt="CI"></a>
  <img src="https://img.shields.io/badge/Python-3.10%20%7C%203.12%20%7C%203.13-3776AB" alt="Python 3.10, 3.12 and 3.13">
  <img src="https://img.shields.io/badge/tests-127%20passing-16A34A" alt="127 tests passing">
  <img src="https://img.shields.io/badge/support-L0%E2%80%93L3-6D5DFB" alt="Support levels L0 to L3">
  <img src="https://img.shields.io/badge/license-MIT-16A34A" alt="MIT license">
</p>

> **AI图像声明｜AI-GENERATED CONCEPTUAL ILLUSTRATION：** 下方总览图按照 UI/UX Pro Max 的 Hero-Centric + Evidence Bento 设计流程生成。其中的分子、晶格、轨道形态、服务器和数据界面只用于表达研究场景，不是 Gaussian、VASP、Quantum ESPRESSO、CP2K、Multiwfn、VMD 或实验产生的结果；任何定量结论仍必须来自经过验收的源文件、计算产物和可复现脚本。

<p align="center">
  <img src="assets/ai/hero/tsao-dft-hero.svg" width="100%" alt="TsaoDFT evidence-first DFT research operating system conceptual overview">
</p>

## 30 秒看懂 TsaoDFT

<table>
<tr>
<td width="25%" valign="top"><strong>DFT-first</strong><br><sub>研究问题先落到结构、方法指纹、参考态与验收条件，再进入执行。</sub></td>
<td width="25%" valign="top"><strong>Evidence graph</strong><br><sub>计算、产物、图件和论文主张之间建立显式 support edge，失败尝试也保留。</sub></td>
<td width="25%" valign="top"><strong>Multi-engine</strong><br><sub>分子侧覆盖 Gaussian / Multiwfn / VMD；周期侧覆盖 VASP / QE / CP2K。</sub></td>
<td width="25%" valign="top"><strong>Scale with provenance</strong><br><sub>DFT 标签、ML、动力学和 HPC 只能消费已验收证据，不能绕过科学边界。</sub></td>
</tr>
</table>

`TsaoDFT_skill` 不是一组松散提示词。它拒绝把“程序正常结束”“图像漂亮”或“模型分数高”直接升级为科学结论，而是把研究组织为可检查的状态链：

```text
planned
→ prepared
→ completed
→ technically validated
→ scientifically accepted
→ claim accepted
```

## 从科研问题到可发表主张

<p align="center">
  <img src="assets/demo/workflow-architecture.svg" width="100%" alt="TsaoDFT auditable research loop synthetic demonstration">
</p>

每一次状态跃迁都必须回答：

1. **谁负责验收？**
2. **哪一个产物支持该决定？**
3. **使用了什么方法指纹、软件版本和运行环境？**
4. **还有哪些假设、不确定度与主张边界没有关闭？**

## 八个 Skills，一条证据链

| Skill | 适用于什么工作 | 不可越过的边界 |
|---|---|---|
| [`tsao-dft-suite`](skills/tsao-dft-suite/) | DFT-first 总入口、任务 DAG、跨 Skill 路由、成本与审批门 | 负责协调，不替代引擎级科学判断 |
| [`tsao-structure-prep`](skills/tsao-structure-prep/) | 分子、构象、晶体、表面、缺陷、吸附结构和原子映射 | 不静默决定电荷、自旋、氧化态、终止面或质子化状态 |
| [`tsao-dft-researcher`](skills/tsao-dft-researcher/) | Gaussian 分子 DFT/TDDFT、Opt/Freq、TS/IRC、热化学、NMR、Multiwfn、VMD | 真实程序、许可证和执行环境由用户提供；适配器不伪造运行结果 |
| [`tsao-periodic-dft-materials`](skills/tsao-periodic-dft-materials/) | VASP、Quantum ESPRESSO、CP2K，表面/缺陷、能带/DOS、NEB 与收敛 | 不分发 POTCAR、赝势或受限数据库；不混用不兼容能量 |
| [`tsao-dft-ml-active-learning`](skills/tsao-dft-ml-active-learning/) | DFT 标签审计、数据泄漏防护、适用域、不确定度、主动学习与反向设计 | 高 R²、SHAP 或 acquisition score 不是机理、因果或可合成性证据 |
| [`tsao-dft-kinetics-multiscale`](skills/tsao-dft-kinetics-multiscale/) | Eyring/TST、反应网络、详细平衡、误差传播、微观动力学与反应器交接 | 只消费标准态、参考态和热化学校验通过的数据 |
| [`tsao-dft-hpc-provenance`](skills/tsao-dft-hpc-provenance/) | 本地/Slurm/PBS、资源估算、数组任务、检查点、重启谱系与哈希 | 调度器成功只说明进程结束，不等于科学验收 |
| [`tsao-dft-catalysis-profile`](skills/tsao-dft-catalysis-profile/) | DCS/MCSOMe/DMOS、Si–O/Si–C、Ti/TEA、Ziegler–Natta 与聚烯烃催化 | 专用 Profile，不自动外推到无关体系 |

## 科研图件：概念视觉与确定性证据分轨

下面四张图由仓库脚本和固定合成数据生成，全部标注 `SYNTHETIC DEMO · NOT SCIENTIFIC DATA`。它们用于展示图件合同、验收门与证据组织方式，不是生产计算结果。

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

视觉体系遵循 UI/UX Pro Max 的产品分类、Pattern、Style、Colors、Typography、Density、Anti-pattern 和 Accessibility 流程，完整记录见 [`docs/README_VISUAL_DESIGN_SYSTEM.md`](docs/README_VISUAL_DESIGN_SYSTEM.md)。AI 图治理见 [`docs/AI_IMAGE_GOVERNANCE.md`](docs/AI_IMAGE_GOVERNANCE.md)。

## 支持等级

| 等级 | 含义 | 可以写进论文或报告吗 |
|---|---|---|
| `L0_REFERENCE` | 方法、边界和参考说明 | 只能作为方法参考 |
| `L1_HANDOFF` | 能生成结构化 Manifest 或下游交接文件 | 需下游验证 |
| `L2_VALIDATED_ADAPTER` | 有确定性预检、解析、验证脚本和仓库测试 | 可报告“适配器已验证”，不能声称真实引擎已回归 |
| `L3_EXECUTION_TESTED` | L2 + 真实引擎、版本、场站和不可变回归证据 | 可在明确范围内报告真实执行覆盖 |

Gaussian、VASP、Quantum ESPRESSO 和 CP2K 当前提供选定字段的 **L2 适配器**。缺少合法真实引擎回归材料时，仓库不会宣称 L3。机器可读主张边界见 [`docs/SCIENTIFIC_CLAIM_POLICY.yaml`](docs/SCIENTIFIC_CLAIM_POLICY.yaml)。

## 快速开始

列出可安装 Skills：

```bash
python scripts/install.py --list
```

先做无写入验证：

```bash
python scripts/install.py \
  --agent codex \
  --scope user \
  --skill all \
  --dry-run \
  --validate
```

正式安装：

```bash
python scripts/install.py \
  --agent codex \
  --scope user \
  --skill all
```

真实生产计算仍需用户合法配置引擎、许可证、赝势/基组、场站指南和执行权限。

## 工程质量与一键验收

```bash
python -m pip install -c constraints/py312.txt -r requirements-dev.txt
python -m pip check
python scripts/quality_gate.py
```

当前基线：**127 项单元测试、9 个隔离套件、0 个失败套件**。每个质量阶段都有明确超时，`--json` 输出可直接供机器解析。质量门依次检查：

```text
versioned demo assets
→ dependency and version contract
→ cross-version exact CI constraints
→ repository-only packaging model
→ DFT catalog
→ Agent eval contracts
→ governance and workflow policy
→ capability and scientific-claim boundaries
→ high-confidence secret patterns
→ explained ignore markers
→ governed AI cover
→ bilingual README visuals
→ offline local links
→ Ruff lint
→ Ruff formatting
→ isolated mypy type checks
→ Bandit production audit
→ strict repository audit
→ all non-empty test suites
```

GitHub Actions 以 Python 3.10 / 3.12 / 3.13 的独立约束快照运行，并每周重新执行 CodeQL `security-extended`、运行时/开发/锁定环境 `pip-audit`，生成锁定环境 CycloneDX JSON SBOM。约束更新必须通过审查后的快照流程，不能手工静默漂移。

工程审计、供应链、安全模型与性能边界见：

- [`docs/REPOSITORY_FULL_AUDIT.md`](docs/REPOSITORY_FULL_AUDIT.md)
- [`docs/CODE_QUALITY_AUDIT.md`](docs/CODE_QUALITY_AUDIT.md)
- [`docs/AGENT_SECURITY_MODEL.md`](docs/AGENT_SECURITY_MODEL.md)
- [`docs/SUPPLY_CHAIN_POLICY.md`](docs/SUPPLY_CHAIN_POLICY.md)
- [`docs/SCIENTIFIC_CLAIM_POLICY.yaml`](docs/SCIENTIFIC_CLAIM_POLICY.yaml)
- [`docs/PERFORMANCE_AUDIT.md`](docs/PERFORMANCE_AUDIT.md)
- [`docs/PERFORMANCE_GUIDE.md`](docs/PERFORMANCE_GUIDE.md)
- [`docs/TEST_REPORT.md`](docs/TEST_REPORT.md)

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
| [`docs/ENGINE_SUPPORT_MATRIX.md`](docs/ENGINE_SUPPORT_MATRIX.md) | 引擎覆盖与支持等级 |
| [`docs/CAPABILITY_STATUS.yaml`](docs/CAPABILITY_STATUS.yaml) | 机器可读能力状态 |
| [`docs/SCIENTIFIC_BOUNDARIES.md`](docs/SCIENTIFIC_BOUNDARIES.md) | 科学边界与非主张 |
| [`docs/SCIENTIFIC_CLAIM_POLICY.yaml`](docs/SCIENTIFIC_CLAIM_POLICY.yaml) | 机器可读主张强度与 L3 证据合同 |
| [`docs/CROSS_SKILL_HANDOFF.md`](docs/CROSS_SKILL_HANDOFF.md) | 跨 Skill 交接合同 |
| [`docs/REPOSITORY_FULL_AUDIT.md`](docs/REPOSITORY_FULL_AUDIT.md) | 全仓库安全、供应链与 Agent Skill 审计 |
| [`docs/CODE_QUALITY_AUDIT.md`](docs/CODE_QUALITY_AUDIT.md) | 全仓库代码、测试与 CI 审计 |
| [`docs/SUPPLY_CHAIN_POLICY.md`](docs/SUPPLY_CHAIN_POLICY.md) | 依赖锁定、漏洞审计、SBOM 与发布策略 |
| [`docs/AI_IMAGE_GOVERNANCE.md`](docs/AI_IMAGE_GOVERNANCE.md) | AI 图像治理 |
| [`docs/README_VISUAL_DESIGN_SYSTEM.md`](docs/README_VISUAL_DESIGN_SYSTEM.md) | README 视觉设计系统 |
| [`docs/TEST_REPORT.md`](docs/TEST_REPORT.md) | 测试、图件与工程验收 |

仓库策略：**只在 `main` 工作，不创建功能、修复或临时分支；发布快照使用 Tag / Release。**
