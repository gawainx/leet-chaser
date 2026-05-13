# Case Traceback Output

## 需求内容

当 `leet-chaser run` 执行 case 时，如果某个 case 抛出异常，CLI 需要默认打印完整异常堆栈，方便定位 `solution.py` 中的出错行。多个异常 case 需要全部打印，并按 case 组织输出。

当一次运行同时包含通过、失败和异常 case 时，输出顺序为：先打印正常运行的 case 情况和失败表格，再统一打印异常 case 的完整 traceback，最后打印一行汇总。

## 设计

保留现有“单个 case 异常不阻断后续 case”的执行模型。`runner` 继续捕获每个 case 的异常并汇总结果，同时把异常对应的完整 traceback 保存到结构化结果中。

CLI 输出层把普通断言失败和异常失败分开展示：

- 普通失败继续进入 `Failed Cases` 表格，展示 case、input、expected 和 actual。
- 异常 case 不再塞进表格的 actual 列，而是按 case 单独打印 `ERROR case <index>`、input、expected 和完整 traceback。
- 汇总行保持最后输出，继续展示通过数、失败数和异常数。

## 实现方法

- `src/leet_chaser/runner.py`：为 `ErrorCaseResult` 增加 `traceback` 字段；`run_cases()` 捕获异常时使用 `traceback.format_exception()` 保存完整堆栈文本。
- `src/leet_chaser/cli.py`：`build_failure_table()` 只处理普通失败；新增 `print_error_tracebacks()` 按 case 打印异常详情；`run()` 在普通结果之后、汇总之前统一打印异常。
- `tests/test_runner.py`：验证结构化异常结果包含完整 traceback。
- `tests/test_package.py`：验证 CLI 混合输出顺序、多个异常 case 全部打印，并且 traceback 包含用户代码抛错行。

验证方式：

```shell
uv run pytest tests/test_runner.py::test_run_problem_collects_all_failures_and_errors tests/test_package.py::test_run_command_prints_case_tracebacks_after_normal_case_output -q
uv run pytest -q
```
