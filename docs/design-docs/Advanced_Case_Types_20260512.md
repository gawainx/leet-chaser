# Advanced_Case_Types_20260512

## 核心功能（WHAT）

为 `cases.toml` 和 `debug.toml` 增加可选的顶级类型元数据，用来声明输入参数和输出结果的期望解析类型。未声明类型的位置继续按 TOML 基础类型原样解析。

本期先支持链表系高级类型：

- `linked_list`：单链表。
- `doubly_linked_list`：双向链表。
- `circular_linked_list`：循环单链表。

推荐格式：

```toml
entrypoint = "mergeTwoLists"
input_types = ["linked_list", "linked_list"]
output_type = "linked_list"

[[cases]]
input = [[1, 2, 4], [1, 3, 4]]
output = [1, 1, 2, 3, 4, 4]
```

循环链表使用 table 表达节点值和入环位置：

```toml
entrypoint = "hasCycle"
input_types = ["circular_linked_list"]

[[cases]]
input = [{ values = [3, 2, 0, -4], pos = 1 }]
output = true
```

`pos = -1` 表示无环；`pos >= 0` 表示尾节点指向 `values[pos]`。

### 需求背景（WHY）

LeetCode 上部分链表题的样例输入仍以数组形式展示，但实际传入 `Solution` 方法的是链表节点对象。当前 Leet-Chaser 会把 TOML 数组原样传入，无法直接覆盖链表题的本地运行需求。

### 需求目标（GOAL）

- 用户可以在 TOML 顶级声明输入和输出的高级解析类型。
- 框架内置链表节点类，尽量对齐 LeetCode 常见 Python 节点结构。
- solution 接收到的参数是链表节点对象，而不是数组。
- 输出比较时支持把实际返回链表归一化为数组，与期望输出稳定比较。
- 高级数据类型的 TOML 表达和使用方式要在 `docs/` 中独立记录，方便后续扩展。

### 范围边界

In Scope:

- 新增顶级 `input_types` 和 `output_type` 字段。
- 支持 `linked_list`、`doubly_linked_list`、`circular_linked_list`。
- 新增框架内置节点类和数组转换工具。
- runner/debugger 复用同一套解析结果。
- runner 输出比较对链表类输出做数组化归一。
- README 和 `docs/` 增加高级数据类型示例。

Out of Scope:

- 不复用用户 `solution.py` 中自定义的 `ListNode` 类。
- 不支持树、图、嵌套对象等非链表类型。
- 不实现每个 case 单独覆盖类型元数据。
- 不实现自定义 matcher 或多答案校验。
- 不改变现有无类型元数据 TOML 的兼容行为。

## 实现流程（HOW）

当前 `case_file.py` 在 TOML 加载后只校验 `entrypoint`、`[[cases]]` 和 `input` 是否为参数数组，然后把值原样写入 `Case`。本次会在 `parse_case_data` 阶段读取顶级类型元数据，并在 `_parse_case` 中按类型转换 input/output。

类型字段规则：

- `input_types` 可缺省；缺省时所有输入参数原样解析。
- `input_types` 存在时必须是数组，长度必须等于每个 case 的 `input` 参数个数。
- `input_types` 中的元素必须是字符串；由于 TOML 数组不能直接包含 `null`，用户需要用 `"raw"` 表达原样解析。
- `output_type` 可缺省；缺省时输出原样解析。
- 类型枚举只接受 `raw`、`linked_list`、`doubly_linked_list`、`circular_linked_list`。后续如需基础类型名，可在新需求中扩展。

节点模型：

- `ListNode` 对齐 LeetCode 常见结构，包含 `val` 和 `next`。
- `DoublyListNode` 包含 `val`、`prev` 和 `next`。
- 循环链表复用 `ListNode`，构造时按 `pos` 连接尾节点。
- 空数组转换为 `None`，对齐 LeetCode 空链表习惯。

比较策略：

- `Case.output` 保留期望的原始可比较值或高级类型期望值。
- runner 在比较前按 `output_type` 把 actual 和 expected 归一化为基础结构。
- 链表归一化为数组。
- 循环链表归一化为 `{ "values": [...], "pos": n }`，避免无限遍历。
- 失败表格展示归一化后的 actual/expected，降低对象地址噪音。

文档策略：

- 新增 `docs/advanced-case-types.md`，记录字段、类型枚举、链表表达、循环链表 `pos` 规则和完整示例。
- README 在 TOML 使用章节补充高级类型入口，保持主文档简洁。

## 测试用例

编译检查：

- 运行 `uv run pytest`，确认全部测试通过。

手工检查：

- 新建链表题示例 TOML，确认 `Solution` 收到 `ListNode`/`DoublyListNode`。
- 对循环链表用 `pos = -1` 和 `pos = 1` 分别验证无环和有环。

回归检查：

- 不包含 `input_types` / `output_type` 的既有 two-sum 用例解析结果保持不变。
- `debug.toml` 仍要求恰好一个 case。
- 非法类型名、`input_types` 长度不匹配、循环链表 `pos` 越界时返回清晰的 `CaseFileError`。
