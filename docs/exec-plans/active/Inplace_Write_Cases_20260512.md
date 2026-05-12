# Inplace_Write_Cases_20260512

## Related Design Doc

[Inplace_Write_Cases_20260512](../../design-docs/Inplace_Write_Cases_20260512.md)

## Stage #1: 原地写入配置解析

### Task #1: 扩展 TOML 顶级原地元数据

**Status:** Finished

**Files:** Modify `src/leet_chaser/case_file.py`; Modify `tests/test_case_file.py`.

**Function:** 读取并校验 `inplace_write` 和 `inplace_index`，把原地写入配置挂到 `CaseFile`。

**Implementation Notes:** 已在 `CaseFile` 增加 `inplace_write` 和 `inplace_index`；缺省保持普通返回值比较；`inplace_write = true` 时要求 `inplace_index` 为 0-based 非负整数，并校验每个 case 的 input 参数数量足够。

**Expected Verification Result:** 新增解析测试通过；非法配置抛出明确 `CaseFileError`；旧 TOML 解析结果保持兼容。

## Stage #2: Runner 和 Debug 原地比较

### Task #2: Runner 使用修改后的输入参数作为 actual

**Status:** Finished

**Files:** Modify `src/leet_chaser/runner.py`; Modify `src/leet_chaser/cli.py`; Modify `tests/test_runner.py`; Modify `tests/test_package.py`.

**Function:** 原地 case 调用后从 `input[inplace_index]` 取 actual，与 `output` 比较；返回值非 `None` 时通过 Rich warning 提醒。

**Implementation Notes:** 已保留既有 `output_type` 归一化；新增 `CaseWarning` 结果字段，CLI 统一打印；warning 不改变 pass/fail/error 计数。

**Expected Verification Result:** “移动零”式 solution 返回 `None` 时可以通过；返回非 `None` 时仍按原地结果比较，并在 CLI 输出 warning。

### Task #3: Debug 命令复用原地 actual 选择逻辑

**Status:** Finished

**Files:** Modify `src/leet_chaser/debugger.py`; Modify `src/leet_chaser/cli.py`; Modify `tests/test_debugger.py`; Modify `tests/test_package.py`.

**Function:** `debug.toml` 支持顶级原地配置，debug 输出中的 actual 为被修改后的输入参数。

**Implementation Notes:** 已复用 runner 的 `select_actual_result`，避免 run/debug 判断分叉。

**Expected Verification Result:** debug 原地 case 正确 pass/fail；返回非 `None` 时 CLI 输出 warning。

## Stage #3: 文档、进度与整体验证

### Task #4: 补充使用文档和进度记录

**Status:** Finished

**Files:** Modify `docs/advanced-case-types.md` or create focused docs as needed; Modify `README.md`; Modify `docs/PROGRESS.md`; Update this plan.

**Function:** 记录原地写入字段、0-based 下标规则、run/debug 行为和 warning 规则。

**Implementation Notes:** 已在 README 和 `docs/advanced-case-types.md` 补充“移动零”示例；`docs/PROGRESS.md` 已记录实现摘要；本计划状态已回写。

**Expected Verification Result:** 用户可以按文档写出原地数组题 TOML；`uv run pytest` 全量通过；工作区只包含本需求相关改动。
