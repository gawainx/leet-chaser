# Operations_Mode_Cases_20260514

## 核心功能（WHAT）

为 leet-chaser 增加 `mode = "operations"` 用例模式，用来运行 LeetCode 设计题中的操作序列。用户可以直接把 LeetCode 示例中的 `Input` / `Output` 迁移到 `cases.toml`，本地验证类构造、方法调用和每一步返回值。

### 需求背景（WHY）

当前 leet-chaser 的运行模型是 `Solution()` 实例化后调用一个 `entrypoint(*input)`，再比较单次返回值。这个模型适合 Two Sum、Reverse Linked List 这类函数题，但无法覆盖 146. LRU Cache 这种设计题。

设计题通常要求先构造一个类实例，再按顺序调用多个方法，并逐步比较每一次调用的返回值。用户明确希望 TOML 尽可能贴近 LeetCode 原始格式，减少手工迁移成本，并且 `init -q` 需要自动识别这类题并生成可用模板。

### 需求目标（GOAL）

- 支持 `cases.toml` 顶层 `mode = "operations"`。
- 支持顶层 `class_name = "..."` 指定要构造和调用的类。
- 支持每个 case 使用 `operations`、`input`、`output` 三个数组表达操作序列。
- `leet-chaser run` 能执行构造函数和实例方法，并按 step 比较返回值。
- 失败和异常输出需要包含 case 编号、step 编号、操作名、输入、期望值和实际值。
- `leet-chaser init -q 146` 这类远程初始化能自动识别 operations 题，并生成 `mode = "operations"` 的 `cases.toml`。
- 保持现有普通 `entrypoint` 模式兼容。

### 范围边界

In Scope:

- 单实例操作序列。
- 每个 `[[cases]]` 之间重新构造实例，避免状态泄露。
- LeetCode 原始格式风格的 `operations`、`input`、`output` 三数组。
- 构造函数作为 `operations[0]`，并要求等于 `class_name`。
- 远端初始化按 Python3 snippet 和题面示例自动识别 operations 题。
- 单元测试覆盖手写 operations case、失败 step 定位、异常 step 定位和远端 operations 示例生成。

Out of Scope:

- 多实例交互。
- 属性断言。
- 自定义 comparator。
- operations 模式下的 `debug` 命令。
- operations 参数里的高级类型自动转换。
- 在线提交或官方 judge。

## 实现流程（HOW）

当前 `src/leet_chaser/case_file.py` 的 `CaseFile` 只表达普通函数题。新增模式时保持普通模式默认值不变，避免旧 TOML 迁移成本。

推荐新增常量与结构：

- `CASE_MODE_NORMAL = "normal"`
- `CASE_MODE_OPERATIONS = "operations"`
- `OperationCase`：保存 `operations: list[str]`、`input: list[list[Any]]`、`output: list[Any]`。
- `CaseFile.mode`：默认 `normal`。
- `CaseFile.class_name`：仅 operations 模式需要。
- `CaseFile.operation_cases`：仅 operations 模式使用。

解析规则：

- 未声明 `mode` 时按现有普通模式解析，仍要求 `entrypoint` 和 `[[cases]] input/output`。
- `mode = "operations"` 时要求顶层 `class_name`，不要求 `entrypoint`。
- 每个 case 必须包含等长的 `operations`、`input`、`output`。
- `operations` 必须是非空字符串数组。
- `input` 必须是数组，且每一项都是参数数组。
- `output` 必须是数组。
- `operations[0]` 必须等于 `class_name`。

运行规则：

- `run_problem` 加载 `CaseFile` 后根据 `mode` 分派普通模式或 operations 模式。
- 普通模式继续使用现有 `resolve_solution_method` 和 `run_cases`。
- operations 模式从 module 里取 `class_name`，确认它是可调用类。
- 每个 case 先执行 `class_name(*input[0])` 创建实例。
- 后续 step 执行 `getattr(instance, operation)(*input[step])`。
- 每个 step 返回值与 `output[step]` 比较；构造函数通常期望 `"null"`，运行时按 `None` 比较。
- 比较逻辑复用现有输出规范化和 `unordered_output` 能力中安全可复用的部分；第一版不接入高级类型元数据。

远端初始化规则：

- `leetcode_client.py` 解析 Python3 snippet 时，如果没有 `class Solution` 入口函数，并能解析到顶层用户类名，则识别为 operations 题。
- `parse_examples` 在 operations 模式下解析题面中的两个输入数组和输出数组。
- `format_remote_case_toml` 根据 metadata 生成：

```toml
mode = "operations"
class_name = "LRUCache"

[[cases]]
operations = ["LRUCache", "put", "put", "get"]
input = [[2], [1, 1], [2, 2], [1]]
output = ["null", "null", "null", 1]
```

文档更新：

- README 增加 operations 模式示例。
- `docs/init-command.md` 说明 `init -q` 能识别设计题。
- 新增或更新 case 格式文档，记录 `mode = "operations"` 的字段和边界。
- `docs/PROGRESS.md` 记录需求完成情况。

## 测试用例

编译检查:

- `uv run pytest -q`

手工检查:

- `leet-chaser init -q 146` 生成 `mode = "operations"`、`class_name = "LRUCache"` 和操作序列用例。
- `leet-chaser run lt146.LRUCache` 可以运行用户实现并输出 step 级结果。

回归检查:

- 现有普通函数题 `entrypoint` 模式继续通过。
- `leet-chaser init -q 1` 仍生成普通 `entrypoint` 模式。
- operations case 中数组长度不一致时报 case 文件结构错误。
- operations case 中 `operations[0] != class_name` 时报 case 文件结构错误。
