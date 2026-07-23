# TsaoDFT Skill

<p align="center"><strong>结构 → 分子/周期 DFT → 波函数与材料性质 → HPC溯源 → ML/主动学习 → 动力学/多尺度 → 投稿级图件</strong></p>

`TsaoDFT_skill` 将上传的 AI for Science Skill 总目录中的计算化学与 DFT 相关能力，整合为 **7 个有边界、可组合、可验证的 Agent Skills**。仓库只维护 `main`，不使用功能分支。

![TsaoDFT workflow](assets/demo/workflow-architecture.svg)

> README中的所有演示图均由确定性脚本基于模拟数据生成，并在图内标注 `SYNTHETIC DEMO · NOT SCIENTIFIC DATA`。它们展示我们的 Skill 图件风格，不是 Gaussian、VASP、QE、CP2K 或 Multiwfn 结果。

## Skill 体系

| Skill | 适用工作 | 关键边界 |
|---|---|---|
| [`tsao-dft-researcher`](skills/tsao-dft-researcher/) | 分子 DFT/TDDFT、Gaussian、TS/IRC、热化学、光谱、Multiwfn、VMD和证据审计 | Gaussian为最深适配器；其他引擎按支持级别路由 |
| [`tsao-structure-prep`](skills/tsao-structure-prep/) | 分子/配合物/晶体/表面/缺陷/吸附结构与候选矩阵 | 不静默决定电荷、多重度、终止面或质子化态 |
| [`tsao-periodic-dft-materials`](skills/tsao-periodic-dft-materials/) | VASP/QE/CP2K周期DFT、收敛、能带/DOS、表面、缺陷、NEB、声子、高通量 | 不提供执行程序、POTCAR或伪势；能量必须同方法可比 |
| [`tsao-dft-ml-active-learning`](skills/tsao-dft-ml-active-learning/) | DeepChem/RDKit、DFT描述符、GNN/代理模型、不确定性、主动学习、逆向设计 | 防止构象/同源结构泄漏；SHAP不是因果证据 |
| [`tsao-dft-hpc-provenance`](skills/tsao-dft-hpc-provenance/) | Slurm/PBS/本地脚本、批量DAG、监控、恢复、成本、溯源和CI | 生成与审计优先；提交和高成本变更需要批准 |
| [`tsao-dft-kinetics-multiscale`](skills/tsao-dft-kinetics-multiscale/) | Eyring/TST、反应网络、Cantera/RMG/Pyomo/CatMAP、微观动力学和反应器桥接 | 标准态、速率单位、详细平衡和拟合参数必须显式 |
| [`tsao-dft-catalysis-profile`](skills/tsao-dft-catalysis-profile/) | DCS/MCSOMe/DMOS、Si–O/Si–C、Ti/TEA、Ziegler–Natta及聚合机理 | 专用Profile；不适用于无关体系，不凭孤立分子直接宣称工业中毒 |

## 从Excel目录检索并整合的范围

本版重点吸收：

- `S0115–S0144`：分子/周期结构、量化方法、Opt/Freq、TS/IRC、电子结构、表面/缺陷、收敛、能带/DOS、声子、弹性、NEB和高通量DFT；
- `S0080–S0096`：多保真、物理信息ML、GNN、代理模型、校准、适用域、数据泄漏、主动学习、贝叶斯/多目标优化和逆向设计；
- `S0168、S0173–S0178、S0185–S0191`：DFT到微观动力学、反应网络、描述符、火山图、反应器和群体平衡桥接；
- `S0279–S0298`：HPC环境、脚本、批量任务、监控、失败恢复、检查点、资源优化、溯源、DAG、容器、可重复性与科研CI；
- `S0001–S0018、S0028–S0031、S0320–S0322`中的科研路由、审批、证据、审计和幻觉防护能力；
- `E013、E015–E023、E025、E029–E032`中的 Pyomo、Cantera、RMG、pymatgen、AiiDA、atomate2、ASE、Psi4、QE、CP2K、MDAnalysis、DeepChem、RDKit、Snakemake和Nextflow生态。

完整映射见 [`docs/DFT_SKILL_CATALOG_MAPPING.md`](docs/DFT_SKILL_CATALOG_MAPPING.md)。

## 一条统一的科学证据链

```text
scientific question
→ reviewed structure campaign
→ molecular or periodic method fingerprint
→ preflight and approval
→ engine execution
→ technical validation
→ quantitative analysis
→ figure manifest
→ calculation–artifact–claim audit
→ accepted / inconclusive / contradicted
```

![Periodic DFT](assets/demo/periodic-dft-materials.svg)

## 分子与周期DFT

分子端以 Gaussian 16 + Multiwfn + VMD/Tachyon 为最深适配器；周期端使用 VASP、Quantum ESPRESSO 和 CP2K 的结构化交接、收敛与能量表达式检查。仓库不包含商业程序、POTCAR、伪势、基组库或第三方手册。

![Wavefunction and ESP](assets/demo/wavefunction-esp-gallery.svg)

## DFT + ML 与闭环主动学习

模型训练前必须先定义独立样本单位。构象、不同电荷/自旋态、重复计算和不同随机种子不自动构成独立分子。主动学习选出的候选必须重新经过结构、DFT和接受门。

![Active learning](assets/demo/active-learning-loop.svg)

## HPC、溯源与科研CI

`tsao-dft-hpc-provenance`生成并审查本地、Slurm或PBS脚本，记录资源、版本、输入输出哈希、检查点和重启谱系。调度成功不等于计算有效，更不等于科学接受。

![HPC provenance](assets/demo/hpc-provenance.svg)

## DFT到动力学和多尺度

自由能只有在温度、相态、标准态、参考态、路径简并度和隧穿约定一致时才能转成速率。微观动力学、反应器和群体平衡中的拟合参数与第一性原理参数必须分开标记。

![Multiscale kinetics](assets/demo/multiscale-kinetics.svg)

## 安装

列出 Skills：

```bash
python scripts/install.py --list
```

验证全部源码后安装到 Codex：

```bash
python scripts/install.py --agent codex --scope user --skill all --dry-run --validate
python scripts/install.py --agent codex --scope user --skill all
```

只安装通用核心与周期DFT：

```bash
python scripts/install.py --agent codex --scope user --skill tsao-dft-researcher --skill tsao-structure-prep --skill tsao-periodic-dft-materials
```

## 调用示例

```text
使用 $tsao-dft-researcher 作为入口。
先调用 $tsao-structure-prep 建立构象/质子化/自旋候选矩阵。
分子计算走Gaussian；周期表面计算转给 $tsao-periodic-dft-materials。
所有作业脚本转给 $tsao-dft-hpc-provenance，先预演，不提交。
```

```text
使用 $tsao-dft-ml-active-learning。
以parent_structure为分组单位，检查构象泄漏和方法混合，建立3个种子的分组外推验证；只把经过accepted门的DFT标签加入训练集。
```

```text
使用 $tsao-dft-kinetics-multiscale。
把已接受的ΔG与ΔG‡转换为TST速率表，检查1 M/1 atm/表面位点标准态和详细平衡，再生成Cantera/Pyomo交接文件。
```

## 测试与验证

```bash
python -m pip install -r requirements.txt
python scripts/generate_readme_demos.py
python scripts/validate_catalog.py
python scripts/validate_repo.py --strict
python scripts/run_all_tests.py
```

事实边界：本仓库可以确定性测试模板、Manifest、图件、解析和验证脚本；当前交付环境没有执行真实授权 Gaussian/VASP/Multiwfn/VMD 生产计算。科学接受必须由研究者完成。
