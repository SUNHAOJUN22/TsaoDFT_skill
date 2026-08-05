# TsaoDFT Skill

<p align="center">
  <strong>面向分子与周期体系的 DFT-first、证据锁定、可审计科研操作系统</strong><br>
  从结构准备、真实引擎与科学验收，到 ML、动力学、边缘计算、GPU/HPC 加速和可追溯论文主张
</p>

<p align="center">
  <a href="README.md">中文</a> · <a href="README_EN.md">English</a>
</p>

<p align="center">
  <a href="https://github.com/SUNHAOJUN22/TsaoDFT_skill/actions/workflows/ci.yml"><img src="https://github.com/SUNHAOJUN22/TsaoDFT_skill/actions/workflows/ci.yml/badge.svg?branch=main" alt="CI"></a>
  <img src="https://img.shields.io/badge/Python-3.10%20%7C%203.12%20%7C%203.13-3776AB" alt="Python 3.10, 3.12 and 3.13">
  <img src="https://img.shields.io/badge/tests-539%20passing-16A34A" alt="539 tests passing">
  <img src="https://img.shields.io/badge/coverage-94.38%25%20stmt%20%7C%2084.41%25%20branch-16A34A" alt="94.38 percent statement and 84.41 percent branch coverage">
  <img src="https://img.shields.io/badge/public%20support-L2_VALIDATED_ADAPTER-6D5DFB" alt="Public support L2 validated adapter">
  <img src="https://img.shields.io/badge/license-MIT-16A34A" alt="MIT license">
</p>

> **AI图像声明｜AI-GENERATED CONCEPTUAL ILLUSTRATION：** 下方总览图按照 UI/UX Pro Max 的 Hero-Centric + Evidence Bento 视觉方向生成。图中的分子、晶格、轨道形态、服务器和数据界面只用于表达研究场景，不是 Gaussian、VASP、Quantum ESPRESSO、CP2K、Multiwfn、VMD 或实验产生的结果。其余架构图为仓库控制、可复现的确定性 SVG；全部明确标注为合成示意，任何定量结论仍必须来自经过验收的源文件、计算产物和脚本。

<p align="center">
  <img src="assets/ai/hero/tsao-dft-hero.svg" width="100%" alt="TsaoDFT evidence-first DFT research operating system conceptual overview">
</p>

## 30 秒看懂 TsaoDFT

<table>
<tr>
<td width="25%" valign="top"><strong>DFT-first</strong><br><sub>研究问题先落到结构、方法指纹、参考态与验收条件，再进入执行。</sub></td>
<td width="25%" valign="top"><strong>Evidence graph</strong><br><sub>计算、产物、图件和论文主张之间建立显式 support edge，失败尝试也保留。</sub></td>
<td width="25%" valign="top"><strong>Multi-engine</strong><br><sub>分子侧覆盖 Gaussian / Multiwfn / VMD；周期侧覆盖 VASP / QE / CP2K。</sub></td>
<td width="25%" valign="top"><strong>Scale with provenance</strong><br><sub>CPU/GPU、加速库、ML、动力学和 HPC 只能消费已验收证据。</sub></td>
</tr>
</table>

`TsaoDFT_skill` 不是一组松散提示词，也不把“程序正常结束”“图像漂亮”“GPU 已分配”或“模型分数高”直接升级为科学结论：

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
| [`tsao-dft-researcher`](skills/tsao-dft-researcher/) | Gaussian 分子 DFT/TDDFT、Opt/Freq、TS/IRC、热化学、NMR、Multiwfn、VMD | 真实程序、许可证和执行环境由用户提供 |
| [`tsao-periodic-dft-materials`](skills/tsao-periodic-dft-materials/) | VASP、Quantum ESPRESSO、CP2K，表面/缺陷、能带/DOS、NEB 与收敛 | 不分发 POTCAR、赝势或受限数据库；不混用不兼容能量 |
| [`tsao-dft-ml-active-learning`](skills/tsao-dft-ml-active-learning/) | DFT 标签审计、泄漏防护、适用域、不确定度、主动学习与反向设计 | 高 R²、SHAP 或 acquisition score 不是机理或因果证据 |
| [`tsao-dft-kinetics-multiscale`](skills/tsao-dft-kinetics-multiscale/) | Eyring/TST、反应网络、详细平衡、误差传播、微观动力学与反应器交接 | 只消费标准态、参考态和热化学校验通过的数据 |
| [`tsao-dft-hpc-provenance`](skills/tsao-dft-hpc-provenance/) | Windows 本地 PowerShell、POSIX 本地、Slurm/PBS、结构化 argv、硬件盘点、调优候选、GPU 规划、Parser、真实基准、签名审查和内容寻址证据 | GPU 分配、最快单次运行、自报 L3 或合成 fixture 都不等于真实加速 |
| [`tsao-dft-catalysis-profile`](skills/tsao-dft-catalysis-profile/) | DCS/MCSOMe/DMOS、Si–O/Si–C、Ti/TEA、Ziegler–Natta 与聚烯烃催化 | 专用 Profile，不自动外推到无关体系 |

## 科研图件：概念视觉与确定性证据分轨

下面图件由仓库脚本和固定合成数据控制，全部标注 `SYNTHETIC DEMO · NOT SCIENTIFIC DATA`。它们展示图件合同、证据组织和系统架构，不是生产计算结果。

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

## 加速计算架构图谱

下列五张确定性 SVG 用于解释本仓库如何吸收 C++、OpenMP、Kokkos、CUDA‑X、边缘推理和真实引擎能力。它们采用 AI 辅助的视觉设计方向，但由仓库文本资产定义、可重复检查，并不构成性能或科学数据。

<table>
<tr>
<td width="50%"><img src="assets/demo/hybrid-compute-architecture.svg" width="100%" alt="Hybrid Python native and external-engine architecture"></td>
<td width="50%"><img src="assets/demo/cuda-x-decision-map.svg" width="100%" alt="CUDA-X library decision map"></td>
</tr>
<tr>
<td><img src="assets/demo/edge-hpc-closed-loop.svg" width="100%" alt="Edge to HPC scientific feedback loop"></td>
<td><img src="assets/demo/native-acceleration-roadmap.svg" width="100%" alt="Profile-gated native acceleration roadmap"></td>
</tr>
<tr>
<td colspan="2"><img src="assets/demo/evidence-qualification-pipeline.svg" width="100%" alt="Scoped L3 acceleration evidence qualification pipeline"></td>
</tr>
</table>

视觉体系见 [`docs/README_VISUAL_DESIGN_SYSTEM.md`](docs/README_VISUAL_DESIGN_SYSTEM.md)，AI 图治理见 [`docs/AI_IMAGE_GOVERNANCE.md`](docs/AI_IMAGE_GOVERNANCE.md)。

## Python、C++ 与 GPU 的职责边界

本项目确实以 Python 为主，但 Python 主要承担控制面，而不是重新实现专业 DFT 内核。

| 层 | 推荐技术 | 负责内容 |
|---|---|---|
| 科研控制面 | Python、JSON Schema、YAML、结构化 argv | 工作流、预检、方法指纹、证据、调度、解析与报告 |
| 数值基线 | NumPy、BLAS、LAPACK | 确定性 CPU 参考、向量化、矩阵求解与科学等价基线 |
| 可选原生层 | C++20、OpenMP、Kokkos、窄 C ABI | 真实 profile 证明的邻居表、几何、扫描或批量数值热点 |
| 可选 GPU 层 | CUDA、HIP、SYCL、Array API、DLPack | 大型重复数值内核，且必须计入数据搬运和启动开销 |
| 外部计算面 | VASP、QE、CP2K、Gaussian | FFT、对角化、积分、SCF、MPI/OpenMP/GPU 等专业内核 |

原则是：**先剖析，后向量化；先保留 CPU 参考，再引入原生层；只有端到端收益和数值等价同时成立，才接受 GPU 或 C++ 后端。**

## CUDA‑X 与其他加速库如何进入

| 库/路线 | 可以用于 | 不能被解释为 |
|---|---|---|
| cuBLAS / cuSOLVER | 大型、重复、已驻留 GPU 的密集矩阵与求解 | “Python 代码天然已加速” |
| cuFFT / cuFFTMp | 支持该路径的外部引擎构建，或明确的自有 FFT 内核 | Python wrapper 自动加速 VASP/QE/CP2K |
| cuSPARSE | 明确的稀疏矩阵热点 | 小型密集表格的通用优化 |
| cuTENSOR | 经过 profile 的高阶张量收缩、置换和约化 | 外部 DFT 程序的通用开关 |
| cuEquivariance | MACE、NequIP、e3nn 等已验收等变模型 | Kohn–Sham DFT 加速器 |
| NCCL / NVSHMEM | 兼容构建中的多 GPU 通信与分布式工作负载 | 单 GPU、小文件或 Parser 优化 |
| TensorRT / ONNX Runtime | 有 UQ/OOD 门和远程 DFT 回退的边缘 surrogate | 生产 DFT 的替代品 |

## 支持等级

| 等级 | 含义 | 报告边界 |
|---|---|---|
| `L0_REFERENCE` | 方法、边界和参考说明 | 只能作为方法参考 |
| `L1_HANDOFF` | 能生成结构化 Manifest 或下游交接文件 | 需下游验证 |
| `L2_VALIDATED_ADAPTER` | 有确定性预检、Parser、验证脚本和仓库测试 | 可报告“适配器已验证”，不能声称真实引擎已回归 |
| `L3_EXECUTION_TESTED` | L2 + 真实引擎、版本、构建、场站、硬件和不可变回归证据 | 只能在记录的明确范围内报告真实执行覆盖 |

Gaussian、VASP、Quantum ESPRESSO 和 CP2K 当前提供选定字段的 **L2 适配器**。公开能力仍是 `L2_VALIDATED_ADAPTER`。`QUALIFIED_FOR_SCOPED_L3_PERFORMANCE_EVIDENCE` 只表示某个证据包具备审查资格，绝不自动改变公开能力登记。

## 快速开始

```bash
python scripts/install.py --list

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

安装器使用所有权 marker、原子暂存/替换、失败回滚和并发锁。真实生产计算仍需合法配置引擎、许可证、赝势/基组、场站指南和执行权限。

## Windows 原生本地作业脚本

Windows 本地工作流可直接生成 PowerShell 7 脚本，不依赖 WSL，也不会把结构化参数拼接为命令字符串：

```powershell
python skills/tsao-dft-hpc-provenance/scripts/generate_job_script.py `
  .\build\hpc-manifest.yaml `
  --shell powershell `
  --out .\build\job.ps1

pwsh -NoProfile -File .\build\job.ps1
```

Linux、本地 POSIX、Slurm 或 PBS 继续使用原有后端：

```bash
python skills/tsao-dft-hpc-provenance/scripts/generate_job_script.py \
  build/hpc-manifest.yaml \
  --shell posix \
  --out build/job.sh
```

PowerShell 后端的边界是显式的：

- 只接受 `scheduler: local`；Slurm/PBS 仍属于 POSIX/HPC 执行面；
- 拒绝 `environment.modules` 和 `environment.source`，避免把 Unix 环境模块语义伪装成 Windows 支持；
- 通过 `.NET ProcessStartInfo.ArgumentList` 传递结构化 argv，并以异步流复制处理 stdout/stderr；
- 不使用 `Invoke-Expression`、`cmd.exe` 或 shell 字符串拼接；
- 保留审批门、预检、Parser、stdin/stdout/stderr、环境变量、scratch、退出码优先级和运行证据合同；
- Windows 本地执行能力不等于 Gaussian、VASP、QE、CP2K 或 GPU 得到加速。

永久 Windows CI 会在真实 `pwsh` 下执行带特殊字符的参数、Gaussian stdin、预检、Parser、输出流和失败退出码测试。

## GPU、并行与证据资格入口

先做无外部引擎调用的环境盘点，再生成加速规划与待审批候选：

```bash
python skills/tsao-dft-hpc-provenance/scripts/plan_acceleration.py \
  --inspect-environment --out build/acceleration-environment.json

python skills/tsao-dft-hpc-provenance/scripts/plan_acceleration.py \
  skills/tsao-dft-hpc-provenance/templates/acceleration-profile.yaml \
  --out build/acceleration-plan.json

python skills/tsao-dft-hpc-provenance/scripts/materialize_acceleration_campaign.py \
  skills/tsao-dft-hpc-provenance/templates/vasp-gpu-hpc-manifest.yaml \
  skills/tsao-dft-hpc-provenance/templates/acceleration-profile.yaml \
  --manifest-out build/vasp-h100.yaml \
  --matrix-out build/benchmark-matrix.csv \
  --candidate-dir build/candidates \
  --plan-out build/acceleration-plan.json
```

所有候选强制为 `approval: pending`；工具只写文件，不提交作业。正式命令、launcher、preflight 和 Parser 使用结构化 argv；审批必须绑定 Manifest 哈希、计划、候选和方法指纹。

### 验证单个真实 benchmark 结果

根目录中的 benchmark Schema 和 L3 policy 已纳入永久质量门。可独立验证结果文件：

```bash
python scripts/validate_acceleration_contracts.py \
  --result build/benchmark-result.json \
  --json
```

该门会拒绝零墙钟时间、NaN/Inf、布尔整数、非小写 SHA‑256、未知字段、无效时间戳和缺失的构建/硬件/科学结果身份。

### 导入、资格化与验证证据包

```bash
python skills/tsao-dft-hpc-provenance/scripts/import_benchmark_evidence.py \
  results/* \
  --schema skills/tsao-dft-hpc-provenance/templates/benchmark-result.schema.json \
  --artifact-root run-artifacts \
  --out build/evidence.jsonl

python skills/tsao-dft-hpc-provenance/scripts/qualify_performance_evidence.py \
  results/* \
  --result-schema skills/tsao-dft-hpc-provenance/templates/benchmark-result.schema.json \
  --policy skills/tsao-dft-hpc-provenance/templates/performance-qualification-policy.yaml \
  --policy-schema skills/tsao-dft-hpc-provenance/templates/performance-qualification-policy.schema.json \
  --artifact-root run-artifacts \
  --review signed-review-attestation.json \
  --review-public-key reviewer-ed25519-public.pem \
  --out-parent build/performance-evidence

python skills/tsao-dft-hpc-provenance/scripts/verify_evidence_bundle.py \
  build/performance-evidence/evidence-<root_sha256>
```

正式比较只允许一个 benchmark plan。在计算有效加速比前，必须通过 Schema、输入、方法、构建、硬件、拓扑、Parser 和数值等价性。Review 必须采用 Ed25519 签名并绑定 Policy、计划、候选和证据根；证据目录在暂存校验后原子发布。

## 工程质量与一键验收

```bash
python -m pip install -c constraints/py312.txt -r requirements-dev.txt
python -m pip check
python scripts/quality_gate.py
```

当前 Linux 代码资格基线：**539 项测试、9 个隔离套件、0 个失败套件；94.38% statement / 84.41% branch coverage。**

Windows 永久门运行同一组 **539 项测试**，实测为 **94.32% statement / 84.22% branch coverage**；`generate_job_script.py` 在 Linux 与 Windows 均保持 **100% statement / 100% branch coverage**。

当前永久质量门包括 9 个隔离测试套件、Python 3.10 / 3.12 / 3.13、Windows PowerShell、语句与分支覆盖率、18 个 mypy 目标、4 个严格信任边界类型目标、Ruff、Bandit、仓库审计、CodeQL、三层 `pip-audit` 和 CycloneDX JSON SBOM。供应链任务即使失败也会先保留完整审计 JSON 和 SBOM，再使工作流失败。

```text
assets and executable contracts
→ dependency and constraint validation
→ acceleration evidence schema/policy validation
→ governance, capability and security validators
→ Ruff lint and formatting
→ isolated mypy + strict trust-boundary mypy
→ Linux and Windows statement/branch coverage
→ Bandit + strict repository audit
→ all isolated unittest suites + real pwsh execution
→ pip-audit + SBOM + CodeQL
```

工程审计见：

- [`docs/REPOSITORY_FULL_AUDIT.md`](docs/REPOSITORY_FULL_AUDIT.md)
- [`docs/CODE_QUALITY_AUDIT.md`](docs/CODE_QUALITY_AUDIT.md)
- [`docs/TEST_REPORT.md`](docs/TEST_REPORT.md)
- [`docs/PERFORMANCE_GUIDE.md`](docs/PERFORMANCE_GUIDE.md)
- [`docs/SCIENTIFIC_CLAIM_POLICY.yaml`](docs/SCIENTIFIC_CLAIM_POLICY.yaml)

## 科学边界

本仓库：

- 不分发或绕过任何受限引擎、许可证、POTCAR、赝势或基组/势函数库；
- 不把 AI 概念图或合成 SVG 描述为计算或实验结果；
- 不把正常终止、调度成功、模型分数、漂亮图形、GPU 分配或托管 fixture 等同于科学接受；
- 不接受普通 `approved` 字段代替签名审批；
- 不在缺少真实引擎、构建、硬件、重复运行、内容寻址证据根、签名独立审查和显式注册时宣称 `L3_EXECUTION_TESTED`。

## 文档地图

| 文档 | 内容 |
|---|---|
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | 总体架构和状态流 |
| [`docs/ENGINE_SUPPORT_MATRIX.md`](docs/ENGINE_SUPPORT_MATRIX.md) | 引擎覆盖与支持等级 |
| [`docs/CAPABILITY_STATUS.yaml`](docs/CAPABILITY_STATUS.yaml) | 机器可读能力状态 |
| [`docs/SCIENTIFIC_BOUNDARIES.md`](docs/SCIENTIFIC_BOUNDARIES.md) | 科学边界与非主张 |
| [`docs/SCIENTIFIC_CLAIM_POLICY.yaml`](docs/SCIENTIFIC_CLAIM_POLICY.yaml) | 通用与加速 L3 证据合同 |
| [`docs/CROSS_SKILL_HANDOFF.md`](docs/CROSS_SKILL_HANDOFF.md) | 跨 Skill 交接合同 |
| [`docs/REPOSITORY_FULL_AUDIT.md`](docs/REPOSITORY_FULL_AUDIT.md) | 全仓库安全、供应链与 Agent Skill 审计 |
| [`docs/CODE_QUALITY_AUDIT.md`](docs/CODE_QUALITY_AUDIT.md) | 代码、测试、coverage 与 CI 审计 |
| [`docs/SUPPLY_CHAIN_POLICY.md`](docs/SUPPLY_CHAIN_POLICY.md) | 依赖锁定、漏洞审计、SBOM 与发布策略 |
| [`docs/AI_IMAGE_GOVERNANCE.md`](docs/AI_IMAGE_GOVERNANCE.md) | AI 图像和确定性示意图治理 |
| [`docs/PERFORMANCE_GUIDE.md`](docs/PERFORMANCE_GUIDE.md) | 执行、加速与签名证据边界 |
| [`docs/TEST_REPORT.md`](docs/TEST_REPORT.md) | 测试和工程验收 |

仓库策略：**只在 `main` 工作，不创建功能、修复或临时分支；发布快照使用 Tag / Release。**