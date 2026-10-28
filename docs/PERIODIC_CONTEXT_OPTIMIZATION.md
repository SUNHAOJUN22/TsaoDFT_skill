# Request-scoped periodic geometry / 请求级周期几何优化

## Scope / 范围

`neighbor_list.py` prepares immutable cell metadata once per NumPy or cell-list
search. This is repository-owned geometry software, not an optimization of an
external DFT executable. External compute qualification remains `EXTERNAL_HOLD`.

`neighbor_list.py` 在每次 NumPy 或 cell-list 邻居搜索中仅准备一次不可变晶胞信息。
优化对象是仓库自有的几何计算，不是外部 DFT 引擎；外部计算资格保持 `EXTERNAL_HOLD`。

## Numerical contract / 数值合同

For a fixed periodic basis `B`, each displacement `d` needs the same least-squares
projection operator. The prepared path reuses the basis singular-value bound and
projection while retaining the original bounded integer-lattice enumeration,
minimum-distance comparison, tie ordering and singular-cell rejection.
The scalar `reference` backend deliberately retains the unprepared calculation.

对于固定周期基 `B`，各位移 `d` 共用最小二乘投影算子。准备路径复用奇异值下界与投影，
但保留原有整数晶格候选枚举、最短距离比较、相同距离时的确定性排序及奇异晶胞拒绝规则。
标量 `reference` 后端有意保留未预计算的实现，作为独立对照。

The context owns read-only copies and lives only for one search. It is not a
process-global cache: changing the caller's box between searches cannot reuse a
stale projection. Nonperiodic and exactly orthogonal cells need no SVD or
least-squares decomposition. Partial periodicity remains supported.

上下文持有只读副本，仅在本次搜索有效，不使用进程级缓存。调用者在两次搜索间修改晶胞时，
不得复用旧投影。非周期及严格正交晶胞不进行 SVD 或最小二乘分解；部分周期轴继续受支持。

## Permanent evidence / 永久回归

```bash
python -m pytest -q skills/tsao-structure-prep/tests/test_periodic_context_reuse.py
python -m pytest -q skills/tsao-structure-prep/tests
python scripts/quality_gate.py --report-dir ../tsao-dft-acceptance
```

The operation-count regression checks a 12-atom triclinic search against the
unprepared reference. Each optimized search performs one SVD and one
least-squares factorization, rather than repeating them for each of its 66
candidate pairs. Tests cover both optimized backends, full/partial periodicity,
zero-decomposition cases and mutated boxes across requests.

操作次数回归将 12 原子的三斜晶胞搜索与未准备的参考后端比较。每次优化搜索进行一次 SVD
和一次最小二乘分解，而不是对 66 个候选对逐一分解。测试覆盖两个优化后端、全部及部分周期轴、
无需分解的情况和请求间晶胞变化。

A reduced decomposition count is deterministic evidence, not a universal wall-time
speedup. Performance comparisons must use the same structure, cutoff, periodic
axes, numerical tolerance, interpreter, NumPy/BLAS build and hardware; include
context preparation and output construction. Do not describe these measurements
as VASP, CP2K, Quantum ESPRESSO or Gaussian acceleration.

分解次数减少是确定性证据，不代表所有工作负载都获得相同的耗时提升。耗时比较必须固定结构、
截断距离、周期轴、容差、解释器、NumPy/BLAS 和硬件，并计入上下文准备及结果构造成本。
不得将这些测量称为 VASP、CP2K、Quantum ESPRESSO 或 Gaussian 的加速。
