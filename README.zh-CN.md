# TsaoDFT Skill 中文入口

规范中文说明统一维护在 [README.md](README.md)：安装、代码能力、数理合同、使用策略、验收命令和中文 AI 概念图均在该文件中。英文说明见 [README_EN.md](README_EN.md)。

软件门禁、解析通过、真实外部执行和科学批准分别留证。缺少真实引擎/站点/输入/输出与独立审核记录时，外部科学资格保持 `EXTERNAL_HOLD`。历史回执不能替代当前提交的测试。

## 维护与去重策略

- `scripts/` 保留可重复运行的构建、验证和分析工具；已完成使命的一次性原地迁移脚本不进入生产树。
- 兼容入口可以保留，最终状态、有限数检查、数量种类和形状必须服从规范 parser contract，避免两套验收语义漂移。
- Python 字节码、覆盖率数据库和临时构建文件不进入版本库；原始运行与科学工件独立保存。

软件合同通过不等于 Gaussian、VASP、Quantum ESPRESSO 或 CP2K 已在真实许可环境执行，也不等于科学结论获得独立审核。缺少可核验的运行证据时，执行状态仍为 `EXTERNAL_DFT_EXECUTION_NOT_VERIFIED`。

- [引擎支持矩阵](docs/ENGINE_SUPPORT_MATRIX.md)
- [软件与科学验收边界](README_ACCEPTANCE.md)
- [AI 图像治理](docs/AI_IMAGE_GOVERNANCE.md)
