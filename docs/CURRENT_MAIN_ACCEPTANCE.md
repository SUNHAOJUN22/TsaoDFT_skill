# TsaoDFT Skill — code-backed documentation

- [`skills/tsao-structure-prep/scripts/neighbor_list.py`](../skills/tsao-structure-prep/scripts/neighbor_list.py)
- [`scripts/build_release_acceptance.py`](../scripts/build_release_acceptance.py)
- [`scripts/capture_compute_contract_evidence.py`](../scripts/capture_compute_contract_evidence.py)

软件门禁只验证控制面、参考数值与证据合同；Gaussian、VASP、QE、CP2K 等外部引擎未在此自动执行，保持 EXTERNAL_HOLD。

Software gates validate the control plane, reference numerics and evidence contracts only; external engines such as Gaussian, VASP, QE and CP2K are not executed here and remain EXTERNAL_HOLD.

The equations and diagrams document the declared implementation and its interpretation limits. They are not an execution attestation.
