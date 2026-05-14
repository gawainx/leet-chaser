# Leet-Chaser

Leet-Chaser 是一个本地运行 LeetCode Python solution 的命令行工具。它把 `solution.py` 和 `cases.toml` 放在同一个题目目录里，让你可以在本地快速运行样例、补充 case、调试单个用例。

它支持普通函数题，也支持链表、二叉树、原地修改、顺序无关输出，以及 LRU Cache 这类设计题的操作序列。

English documentation: [README_en.md](README_en.md)

## 安装

使用 pip 安装：

```shell
python -m pip install leet-chaser
leet-chaser --help
```

不想安装到当前环境时，可以用 `uvx` 临时运行：

```shell
uvx leet-chaser --help
uvx leet-chaser init two-sum
uvx leet-chaser run two-sum
```

在仓库内开发或验证时，可以直接运行：

```shell
uv run leet-chaser --help
```

## 快速开始

创建题目目录：

```shell
leet-chaser init two-sum
```

生成结果：

```text
two-sum/
├── solution.py
└── cases.toml
```

编写 `solution.py`：

```python
from typing import List


class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        seen = {}
        for index, num in enumerate(nums):
            rest = target - num
            if rest in seen:
                return [seen[rest], index]
            seen[num] = index
        return []
```

填写或修改 `cases.toml`：

```toml
entrypoint = "twoSum"

[[cases]]
input = [[2, 7, 11, 15], 9]
output = [0, 1]

[[cases]]
input = [[3, 2, 4], 6]
output = [1, 2]
```

运行验证：

```shell
leet-chaser run two-sum
```

## 按题号初始化

可以直接按公开 LeetCode 题号初始化。命令会拉取 Python3 模板和题面示例，不需要登录、OAuth 或 cookie：

```shell
leet-chaser init -q 1
leet-chaser init --question-number 1
```

默认目录名是 `lt{题号三位}.{入口名}`：

```text
lt001.twoSum/
├── solution.py
└── cases.toml
```

也可以指定目录名：

```shell
leet-chaser init custom-two-sum -q 1
```

拉取过程中会输出题号查询、题目详情、文件生成和写入完成等进度。失败时错误会说明阶段和类型，例如公开题库找不到、付费题、GraphQL schema 变化、网络不可达或示例解析失败。

## 初始化模板

链表、二叉树和矩阵题可以用 `-t/--type` 生成更贴近题型的 TOML 模板：

```shell
leet-chaser init reverse-list -t linklist
leet-chaser init validate-bst -t bitree
leet-chaser init level-order -t tree
leet-chaser init search-matrix -t matrix
```

常用别名：

- `linklist`、`linked_list`、`listnode` 生成链表模板。
- `bitree`、`binary_tree`、`tree`、`treenode` 生成二叉树模板。
- `matrix`、`grid`、`2d-array` 生成二维数组模板。

`-q/--question-number` 和 `-t/--type` 不能同时使用，因为题号初始化会根据题面生成具体 case。

## Case 文件格式

普通函数题使用顶层 `entrypoint` 指定 `Solution` 类里的方法名。每个 `[[cases]]` 的 `input` 是位置参数数组，`output` 是期望返回值：

```toml
entrypoint = "twoSum"

[[cases]]
input = [[2, 7, 11, 15], 9]
output = [0, 1]
```

单参数题也要把参数放进数组：

```toml
entrypoint = "isPalindrome"

[[cases]]
input = [121]
output = true
```

## 高级类型

链表题可以通过类型元数据把数组解析成节点对象：

```toml
entrypoint = "reverseList"
input_types = ["linked_list"]
output_type = "linked_list"

[[cases]]
input = [[1, 2, 3]]
output = [3, 2, 1]
```

二叉树题可以用 LeetCode 层序数组表达，空节点写成字符串 `"null"`：

```toml
entrypoint = "isValidBST"
input_types = ["binary_tree"]

[[cases]]
input = [[5, 1, 4, "null", "null", 3, 6]]
output = false
```

刷题时可以直接导入内置节点类型：

```python
from leet_chaser.lt_typing import ListNode, TreeNode
```

更多单链表、双向链表、循环链表和二叉树写法见 [docs/advanced-case-types.md](docs/advanced-case-types.md)。

## 原地修改和顺序无关输出

原地修改数组的题目可以比较被修改后的输入参数：

```toml
entrypoint = "moveZeroes"
inplace_write = true
inplace_index = 0

[[cases]]
input = [[0, 1, 0, 3, 12]]
output = [1, 3, 12, 0, 0]
```

`inplace_index` 使用 0-based 参数下标。开启 `inplace_write` 后，返回值会被忽略；如果返回值不是 `None`，命令行会打印 warning。

三数之和这类输出顺序不重要的题目可以开启递归顺序无关比较：

```toml
entrypoint = "threeSum"
unordered_output = true

[[cases]]
input = [[-1, 0, 1, 2, -1, -4]]
output = [[-1, -1, 2], [-1, 0, 1]]
```

## 设计题 operations 模式

LRU Cache、Min Stack、Trie 这类设计题可以使用 `mode = "operations"`。这个格式贴近 LeetCode 原始示例，方便从题面迁移：

```toml
mode = "operations"
class_name = "LRUCache"

[[cases]]
operations = ["LRUCache", "put", "put", "get", "put", "get"]
input = [[2], [1, 1], [2, 2], [1], [3, 3], [2]]
output = ["null", "null", "null", 1, "null", -1]
```

规则：

- `class_name` 是 `solution.py` 中要实例化的类名。
- `operations[0]` 必须等于 `class_name`。
- `input[0]` 用于构造实例，后续 input 用于调用同下标 operation。
- `operations`、`input`、`output` 必须等长。
- LeetCode 的 `null` 在 TOML 中写成 `"null"`，运行时按 Python `None` 比较。
- 每个 case 都会创建一个新实例。

`leet-chaser init -q 146` 会自动识别 LRU Cache 这类题，并生成 operations 模式的 `cases.toml`。

## 调试单个用例

把当前要排查的用例写入 `debug.toml`，格式和 `cases.toml` 一致，但只保留一个 `[[cases]]`：

```toml
entrypoint = "twoSum"

[[cases]]
input = [[2, 7, 11, 15], 9]
output = [0, 1]
```

运行 debug 命令会默认读取 `<problem-dir>/debug.toml`，并逐行打印入口函数里的变量变化：

```shell
leet-chaser debug two-sum
leet-chaser debug two-sum -t seen -t rest
leet-chaser debug two-sum -c two-sum/custom-debug.toml
```

当前 debug 命令面向普通 `entrypoint` 模式；operations 模式可以先用 `run` 的 case、step、operation 输出定位失败步骤。

## 内置示例

运行 LeetCode 1. Two Sum：

```shell
uv run leet-chaser run examples/two-sum
```

运行 LeetCode 206. Reverse Linked List：

```shell
uv run leet-chaser run examples/reverse-linked-list
```

运行 LeetCode 98. Validate Binary Search Tree：

```shell
uv run leet-chaser run examples/validate-binary-search-tree
```

## 更多文档

- [docs/init-command.md](docs/init-command.md)：init 命令设计与行为。
- [docs/run-command.md](docs/run-command.md)：run 命令设计与行为。
- [docs/debug-command.md](docs/debug-command.md)：debug 命令设计与行为。
- [docs/test-case-toml.md](docs/test-case-toml.md)：TOML case 格式。
- [docs/advanced-case-types.md](docs/advanced-case-types.md)：链表和二叉树等高级类型。
