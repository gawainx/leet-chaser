# Commented Init Case Template Plan

## Phase 1: Template Design

### Task 1: Add shared comment blocks

- Status: Finished
- Function: 为普通模式和 operations 模式提供可取消注释的 TOML 配置提示。
- Implementation Notes: 普通模式提示 `input_types`、`output_type`、`inplace_write`、`inplace_index`、`unordered_output` 和类型枚举；operations 模式提示三数组对齐和构造函数规则。
- Expected Tests: 生成的本地和远程模板文本包含关键注释字段。

## Phase 2: Init Generation

### Task 2: Update local init templates

- Status: Finished
- Function: 让 `leet-chaser init <name>` 和 `-t` 模板都输出注释配置区。
- Implementation Notes: 在现有硬编码模板前拼接普通模式注释，不改变有效 TOML 字段。
- Expected Tests: 本地 raw、linked_list、binary_tree、matrix 模板仍可解析。

### Task 3: Update remote init formatting

- Status: Finished
- Function: 让 `leet-chaser init -q <num>` 生成的普通题和设计题模板都带注释。
- Implementation Notes: `format_remote_case_toml()` 按普通模式和 operations 模式插入对应注释区。
- Expected Tests: 远程普通题和 operations 题模板仍可解析。

## Phase 3: Verification and Docs

### Task 4: Update tests and progress

- Status: Finished
- Function: 补充测试和进度记录。
- Implementation Notes: 测试同时检查注释存在与解析结果不变。
- Expected Tests: `uv run pytest tests/test_package.py -q` 通过。
