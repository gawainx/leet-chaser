# Immediate Case Status Output 实现计划

> **给 Claude：** 必需工作流：使用 superpowers:executing-plans 逐任务实现此计划。

**目标：** 让 `leet-chaser run` 在每个执行结果后展示简短 case 状态，同时保持现有详细输出和 Summary 不变。

**相关设计文档：** `docs/design-docs/Immediate_Case_Status_Output_20260521.md`

**架构：** runner 继续只负责执行和结构化结果收集。CLI 根据 `ProblemRunResult` 的结果列表按 case/step 顺序打印简短状态行，再复用既有失败表格、异常 traceback 和 Summary 输出。

**技术栈：** Python 3.12、Typer、Rich、pytest、uv。

**范围 / 非范围：** 范围包含 `run` 命令普通模式和 operations 模式的简短状态输出、测试和文档记录；不包含新增配置、改变比较逻辑、改变 Summary 统计或 debug 命令输出。

---

## Phase #1: CLI 输出增强

### Task #1: 按执行顺序打印简短状态

**状态：** Finished

**文件：**
- 修改：`src/leet_chaser/cli.py`
- 验证：`tests/test_package.py`

- 功能：`run` 命令对 pass、fail 和 error 都打印简短状态行，并在 operations 模式包含 step 与 operation。
- 实现说明：新增 helper 函数复用 `PassedCaseResult`、`FailedCaseResult` 和 `ErrorCaseResult` 的公共字段；普通模式按 `index` 排序，operations 模式按 `(index, step)` 排序。
- 预期验证结果：普通模式混合结果输出顺序为 PASS/FAIL/ERROR 简短状态、失败表格、异常 traceback、Summary；operations 模式简短状态包含 step 与 operation。
- 完成时间：2026-05-21

### Task #2: 更新文档与进度

**状态：** Finished

**文件：**
- 修改：`docs/run-command.md`
- 修改：`docs/PROGRESS.md`
- 修改：`docs/plans/2026-05-21-immediate-case-status-output.md`
- 验证：`uv run pytest tests/test_package.py -q`

- 功能：记录新输出行为和验证结果。
- 实现说明：只补充与本需求直接相关的 run 输出说明和进度条目，不调整无关文档结构。
- 预期验证结果：定向测试通过，计划状态回写为 Finished。
- 完成时间：2026-05-21
