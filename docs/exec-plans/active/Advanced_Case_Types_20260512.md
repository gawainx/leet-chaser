# Advanced_Case_Types_20260512

## Related Design Doc

[Advanced_Case_Types_20260512](../../design-docs/Advanced_Case_Types_20260512.md)

## Stage #1: 高级类型解析与链表模型

### Task #1: 新增链表节点和转换工具

**Status:** Finished

**Files:** Create `src/leet_chaser/linked_types.py`; Modify tests as needed.

**Function:** 提供 `ListNode`、`DoublyListNode`、数组到链表、链表到数组、循环链表构造和归一化能力。

**Implementation Notes:** 已新增 `ListNode`、`DoublyListNode` 和转换 helper；空数组返回 `None`；循环链表使用 `{ values, pos }` table 构造，`pos = -1` 表示无环。

**Expected Verification Result:** 单元测试覆盖单链表、双向链表、循环链表和空链表转换。

### Task #2: 扩展 TOML 顶级类型元数据解析

**Status:** Finished

**Files:** Modify `src/leet_chaser/case_file.py`; Modify `tests/test_case_file.py`.

**Function:** 读取 `input_types` 和 `output_type`，按类型转换每个 case 的输入和输出。

**Implementation Notes:** 已保持缺省字段兼容；`raw` 显式表示 TOML 原样解析；已校验类型枚举、`input_types` 长度和循环链表 table 结构；错误统一抛出 `CaseFileError`。

**Expected Verification Result:** 既有 TOML 测试不变；新增类型字段测试通过；非法结构能返回明确错误。

## Stage #2: Runner 比较归一化与 Debug 兼容

### Task #3: 输出比较支持链表归一化

**Status:** Finished

**Files:** Modify `src/leet_chaser/runner.py`; Modify `tests/test_runner.py`.

**Function:** 当 `output_type` 是链表类型时，把 expected 和 actual 转为基础结构后比较和展示。

**Implementation Notes:** `Case` 已携带 `output_type`；runner 通过 `normalize_case_value` 归一化链表 expected/actual，失败结果记录可读基础结构。

**Expected Verification Result:** 返回链表对象的 solution 可以和 TOML 数组期望值匹配；错误 case 仍能继续执行后续 case。

### Task #4: 确认 debug 命令复用高级输入解析

**Status:** Finished

**Files:** Modify `src/leet_chaser/debugger.py` if needed; Modify `tests/test_debugger.py`.

**Function:** debug 单 case 支持高级输入类型，返回值比较逻辑与 run 保持一致。

**Implementation Notes:** debug 已复用 case 文件解析结果，并使用 runner 的 `normalize_case_value` 判断 pass/fail。

**Expected Verification Result:** debug 链表 case 可以运行并正确判断 pass/fail。

## Stage #3: 文档、示例与整体验证

### Task #5: 补充高级数据类型使用文档

**Status:** Finished

**Files:** Create `docs/advanced-case-types.md`; Modify `README.md`.

**Function:** 记录 `input_types`、`output_type`、三类链表枚举、循环链表 table 表达和完整使用示例。

**Implementation Notes:** 已新增 `docs/advanced-case-types.md`，README 已补充链表题入口示例。

**Expected Verification Result:** 用户只看文档即可写出单链表、双向链表、循环链表 case。

### Task #6: 回归验证与进度记录

**Status:** Finished

**Files:** Modify `docs/PROGRESS.md`.

**Function:** 运行完整测试，记录实现摘要、验证结果和后续边界。

**Implementation Notes:** 已更新进度记录；本轮最终统一验证并提交。

**Expected Verification Result:** `uv run pytest` 通过，工作区只包含本需求相关改动。
