# Immediate Case Status Output

## 需求内容

用户需要 `leet-chaser run` 在每个 case 执行结束后立即展示该 case 的执行情况。该能力不需要新增命令行参数或 `cases.toml` 配置，也不能改变最后的汇总输出。

本次输出只增加简短状态行。失败表格、异常 traceback 和最后 Summary 继续沿用现有输出，避免重复打印详细内容。

## 设计

保持 `runner.py` 的结构化执行结果不变，由 CLI 输出层根据 `ProblemRunResult` 中的 `passed`、`failed` 和 `errors` 结果按执行顺序打印简短状态。

普通模式按 case index 排序输出：

- `PASS case 1`
- `FAIL case 2`
- `ERROR case 3`

operations 模式沿用当前 step 级统计模型，每个 step 作为一个执行结果输出，并包含 step 与 operation 信息：

- `PASS case 1 step 2 put`
- `FAIL case 1 step 3 get`
- `ERROR case 1 step 4 get`

原有详细输出保持不变：失败 case 仍进入失败表格，异常 case 仍打印 traceback，最后 Summary 仍使用现有 `passed / failed / errors` 统计。

## 实现方法

在 `src/leet_chaser/cli.py` 中新增按执行顺序构建和打印简短状态的函数，`run` 命令调用该函数替代原本只遍历 `result.passed` 的输出逻辑。

测试重点放在 CLI 行为：

- 普通模式混合 pass、fail、error 时，简短状态按 case 顺序出现。
- 详细失败表格、异常 traceback 和 Summary 保持在简短状态之后。
- operations 模式输出 step 和 operation，且 Summary 不变。
