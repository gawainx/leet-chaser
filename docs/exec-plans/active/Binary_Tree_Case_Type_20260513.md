# Binary Tree Case Type Implementation Plan

> **For Claude:** REQUIRED WORKFLOW: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为 Leet-Chaser 增加 LeetCode 层序数组到二叉树节点的解析与输出比较能力。

**Related Design Doc:** `docs/design-docs/Binary_Tree_Case_Type_20260513.md`

**Architecture:** 沿用现有高级 case 类型架构，在类型枚举中增加 `binary_tree`。树结构的构建和归一化放在独立模块，case 解析负责把 TOML 值转为节点，runner 负责把返回值归一化为可比较数组。

**Tech Stack:** Python 3.12、dataclasses、TOML case 文件、pytest、uv。

**Scope / Out of Scope:** 范围包含二叉树输入解析、二叉树输出归一化、测试和文档；不包含 N 叉树、父指针树、可视化树、case 级类型覆盖。

---

## Phase #1: Core Binary Tree Type

### Task #1: Tree Node And Conversion Helpers

**Status:** Finished

**Files:**
- Create: `src/leet_chaser/tree_types.py`
- Modify: `tests/test_case_file.py`

- Function: 新增 `TreeNode`，支持层序数组构建二叉树和二叉树转层序数组。
- Implementation Notes: 已新增 `TreeNode`、`build_binary_tree`、`binary_tree_to_array` 和 `normalize_tree_value`；空节点标记使用字符串 `"null"`；空数组返回 `None`；序列化时去掉末尾多余 `"null"`。
- Expected Verification Result: `uv run pytest tests/test_case_file.py tests/test_runner.py -q` 已通过，case 文件测试确认树节点结构、空树和稀疏树解析正确。

### Task #2: Case Type Integration

**Status:** Finished

**Files:**
- Modify: `src/leet_chaser/case_file.py`
- Modify: `src/leet_chaser/runner.py`
- Modify: `tests/test_runner.py`

- Function: 把 `binary_tree` 接入 `input_types` / `output_type`，并让 runner 比较返回树。
- Implementation Notes: 已保持 `raw` 与既有链表类型行为不变；错误信息沿用 `CaseFileError`；runner 通过 `normalize_case_value` 对 `binary_tree` 输出归一化。
- Expected Verification Result: `uv run pytest tests/test_case_file.py tests/test_runner.py -q` 已通过，BST、层序遍历、返回树比较场景通过 pytest。

## Phase #2: Documentation And Progress

### Task #3: User Documentation

**Status:** Finished

**Files:**
- Modify: `README.md`
- Modify: `docs/advanced-case-types.md`
- Modify: `docs/PROGRESS.md`
- Modify: `docs/exec-plans/active/Binary_Tree_Case_Type_20260513.md`

- Function: 记录 `binary_tree` 的 TOML 写法、空节点约定和实现进度。
- Implementation Notes: README 和高级类型文档已用实际 LeetCode 风格例子说明，不扩展未实现类型；`docs/PROGRESS.md` 已记录完成内容。
- Expected Verification Result: `uv run pytest -q` 已通过；文档包含「需求内容」「设计」「实现方法」信息，并且计划状态已回写为 Finished。
