# Case Traceback Output

## Phase #1: 保留 case 异常堆栈

### Task #1: Runner 记录完整 traceback

**Status:** Finished

**Files:**
- Modify: `src/leet_chaser/runner.py`
- Modify: `tests/test_runner.py`

- Function: case 执行抛异常时，结构化错误结果保留异常类型、异常消息和完整 traceback。
- Implementation Notes: 使用标准库 `traceback.format_exception()`，不改变继续执行后续 case 的行为。
- Expected Verification Result: `test_run_problem_collects_all_failures_and_errors` 能断言 traceback 里包含 `Traceback (most recent call last):` 和用户代码抛错行。

## Phase #2: CLI 按 case 输出异常详情

### Task #2: 分离普通失败表格和异常 traceback 输出

**Status:** Finished

**Files:**
- Modify: `src/leet_chaser/cli.py`
- Modify: `tests/test_package.py`

- Function: CLI 先打印 PASS 和普通失败表格，再按 case 打印所有异常 traceback，最后打印汇总行。
- Implementation Notes: `build_failure_table()` 只负责普通失败；新增 `print_error_tracebacks()` 负责异常 case 分块输出。
- Expected Verification Result: `test_run_command_prints_case_tracebacks_after_normal_case_output` 验证输出顺序、多个异常 case 和 traceback 内容。

## Phase #3: 文档与收尾

### Task #3: 记录需求、设计和实现

**Status:** Finished

**Files:**
- Create: `docs/design-docs/Case_Traceback_Output_20260513.md`
- Create: `docs/exec-plans/active/Case_Traceback_Output_20260513.md`
- Modify: `docs/PROGRESS.md`

- Function: 记录本次异常输出改善的需求内容、设计、实现方法和验证方式。
- Implementation Notes: 文档范围只覆盖 traceback 输出，不扩展 CLI 开关。
- Expected Verification Result: 文档包含「需求内容」「设计」「实现方法」，进度文件记录实现摘要。
