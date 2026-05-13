# Init Advanced Type Template Implementation Plan

> **For Claude:** REQUIRED WORKFLOW: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 让 `leet-chaser init` 能通过 `-t` 生成带高级输入类型元数据的 TOML 模板。

**Related Design Doc:** `docs/design-docs/Init_Advanced_Type_Template_20260513.md`

**Architecture:** 在 CLI 层解析用户传入的模糊类型名，并选择静态 TOML 模板。case 解析、runner 和高级类型本身不变。

**Tech Stack:** Python 3.12、Typer、TOML case 文件、pytest、uv。

**Scope / Out of Scope:** 范围包含链表和二叉树 init 模板；不包含多个高级参数、按题号自动识别模板、输出类型命令行配置。

---

## Phase #1: CLI Template Selection

### Task #1: Type Alias Parsing

**Status:** Finished

**Files:**
- Modify: `src/leet_chaser/cli.py`
- Verify: `tests/test_package.py`

- Function: 新增 `-t/--type` 参数，把 linklist/listnode/tree/bitree 等模糊输入归一为已有高级类型。
- Implementation Notes: 已实现归一化逻辑，移除非字母数字字符并转小写；非法类型使用 `typer.BadParameter`。
- Expected Verification Result: `uv run pytest tests/test_package.py -q` 已通过，package 测试覆盖合法 alias 和非法类型。

### Task #2: Advanced Case Templates

**Status:** Finished

**Files:**
- Modify: `src/leet_chaser/cli.py`
- Modify: `tests/test_package.py`

- Function: 根据归一化类型写入默认、链表或二叉树 `cases.toml`。
- Implementation Notes: 已新增默认、链表和二叉树模板；只默认每个 case 的第一个参数是特殊类型；默认 init 行为保持不变。
- Expected Verification Result: `uv run pytest tests/test_package.py -q` 已通过，生成的 TOML 可被 `read_case_file` 解析，且高级类型元数据正确。

## Phase #2: Documentation

### Task #3: Docs And Progress

**Status:** Finished

**Files:**
- Modify: `README.md`
- Modify: `docs/init-command.md`
- Modify: `docs/PROGRESS.md`
- Modify: `docs/exec-plans/active/Init_Advanced_Type_Template_20260513.md`

- Function: 记录 `init -t` 用法、支持 alias 和验证结果。
- Implementation Notes: README、init 文档和 PROGRESS 已记录链表与二叉树模板。
- Expected Verification Result: `uv run pytest -q` 已通过，计划状态已回写为 Finished。
