# Operations_Mode_Cases_20260514

## Related Design Doc

- `docs/design-docs/Operations_Mode_Cases_20260514.md`

## Stage #1: Operations Case Model And Runner

### Task #1: 解析 operations case 文件

**Status:** Finished

**Files:** Modify `src/leet_chaser/case_file.py`; Verify `tests/test_case_file.py`.

- Function: 支持 `mode = "operations"`、`class_name`、`operations/input/output` 三数组结构。
- Implementation Notes: 已新增 `OperationCase`、`mode`、`class_name` 和 `operation_cases`；普通 TOML 未声明 `mode` 时仍按现有 `entrypoint` 模式解析；operations case 校验三数组等长、参数数组结构和构造函数名。
- Expected Verification Result: `tests/test_case_file.py` 已覆盖 LRU 风格 TOML、长度不一致和构造函数不匹配。

### Task #2: 执行 operations 操作序列

**Status:** Finished

**Files:** Modify `src/leet_chaser/runner.py`, `src/leet_chaser/cli.py`; Verify `tests/test_runner.py`.

- Function: 根据 operations case 构造类实例并按 step 调用方法，比较每一步返回值。
- Implementation Notes: `run_problem` 已按 case mode 分派；operations 模式解析 `class_name` 对应类，每个 case 创建新实例并按 step 执行；失败和异常结果携带 `step` 与 `operation`，CLI failure table 和 error 输出可展示定位信息。
- Expected Verification Result: `tests/test_runner.py` 已覆盖 LRUCache 示例通过、错误返回值 step 定位和异常 step 定位。

## Stage #2: Remote Init Operations Detection

### Task #3: 识别 Python3 类模板

**Status:** Finished

**Files:** Modify `src/leet_chaser/leetcode_client.py`; Verify dedicated parser tests.

- Function: 远端题目没有 `class Solution` 方法入口时，解析顶层用户类名并标记为 operations 模式。
- Implementation Notes: `LeetCodeQuestionMetadata` 已增加 `case_mode` 与 `class_name`；普通题继续解析 `class Solution` 里的 entrypoint 和参数名；设计题解析顶层类名，目录名使用 `lt{题号三位}.{class_name}`。
- Expected Verification Result: `tests/test_package.py` 已覆盖 `parse_class_name_from_python_code` 和 LRUCache 风格远端初始化。

### Task #4: 生成 operations TOML

**Status:** Finished

**Files:** Modify `src/leet_chaser/leetcode_client.py`; Verify parser and formatting tests.

- Function: 从 LeetCode operations 示例生成 `mode = "operations"` 的 `cases.toml`。
- Implementation Notes: `parse_examples` 已按 `case_mode` 分派；operations 示例解析 `Input` 中的操作名数组和参数数组，并解析 `Output` 数组；输出 TOML 保留 LeetCode 原始的 `operations/input/output` 三数组。
- Expected Verification Result: `tests/test_package.py` 已覆盖 operations mode TOML 格式化、`init -q 146` 风格 mock 生成和 case 文件可解析性。

## Stage #3: Documentation, Regression, And Commit

### Task #5: 更新用户文档

**Status:** Finished

**Files:** Modify `README.md`, `docs/init-command.md`, `docs/test-case-toml.md`, `docs/PROGRESS.md`.

- Function: 说明 operations 模式字段、示例、边界和远端初始化行为。
- Implementation Notes: README 已给出 operations 最短示例；`docs/test-case-toml.md` 记录完整字段约束；`docs/init-command.md` 说明 `init -q` 对设计题的自动识别；`docs/PROGRESS.md` 已记录本次进展。
- Expected Verification Result: 用户可以按文档手写 LRUCache TOML，并理解第一版不支持多实例和 debug。

### Task #6: 整体验证与提交

**Status:** Finished

**Files:** Verify full test suite; Modify this plan with final implementation notes.

- Function: 运行回归测试，更新计划任务状态和实现记录，并按仓库提交规范提交。
- Implementation Notes: 已运行 `uv run pytest tests/test_package.py tests/test_case_file.py tests/test_runner.py -q` 和 `uv run pytest -q`；提交信息使用 Conventional Commit，例如 `feat: add operations mode cases`。
- Expected Verification Result: 全量测试通过；工作区只包含本需求相关改动；提交后工作区干净。
