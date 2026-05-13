# Leet-Chaser

本地运行 leetcode solution 的命令行框架。

## pip 安装运行

```shell
python -m pip install leet-chaser
leet-chaser --help
```

安装后可以直接使用 `leet-chaser` 命令：

```shell
leet-chaser init two-sum
leet-chaser run two-sum
```

## uvx 直接运行

不想把命令安装到当前环境时，可以用 `uvx` 临时运行：

```shell
uvx leet-chaser --help
uvx leet-chaser init two-sum
uvx leet-chaser run two-sum
```

## 使用方法

### STEP 1: 初始化题目目录

```shell
leet-chaser init two-sum
```

链表或二叉树题可以用 `-t` 生成带高级类型元数据的模板：

```shell
leet-chaser init reverse-list -t linklist
leet-chaser init validate-bst -t bitree
leet-chaser init level-order -t tree
```

命令会在当前目录创建一个题目文件夹：

```text
two-sum/
├── solution.py
└── cases.toml
```

### STEP 2: 编写 `solution.py`

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

### STEP 3: 填写 `cases.toml`

`entrypoint` 是 solution 里的入口方法名。`input` 是传给入口方法的位置参数数组，`output` 是期望返回值。

使用 `init -t` 时，生成的 `cases.toml` 会默认把每个 case 的第一个参数声明为对应高级类型。

```toml
entrypoint = "twoSum"

[[cases]]
input = [[2, 7, 11, 15], 9]
output = [0, 1]

[[cases]]
input = [[3, 2, 4], 6]
output = [1, 2]

[[cases]]
input = [[3, 3], 6]
output = [0, 1]
```

链表题可以通过顶级类型元数据把数组解析成节点对象：

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

更多单链表、双向链表、循环链表和二叉树写法见 [docs/advanced-case-types.md](docs/advanced-case-types.md)。

刷题时可以直接导入内置节点类型：

```python
from leet_chaser.lt_typing import ListNode, TreeNode
```

原地修改数组的题目可以通过顶级原地写入元数据比较被修改后的输入参数：

```toml
entrypoint = "moveZeroes"
inplace_write = true
inplace_index = 0

[[cases]]
input = [[0, 1, 0, 3, 12]]
output = [1, 3, 12, 0, 0]
```

`inplace_index` 使用 0-based 参数下标。开启 `inplace_write` 后，返回值会被忽略；如果返回值不是 `None`，命令行会打印 warning。

三数之和这类输出顺序不重要的题目可以开启顺序无关输出比较：

```toml
entrypoint = "threeSum"
unordered_output = true

[[cases]]
input = [[-1, 0, 1, 2, -1, -4]]
output = [[-1, -1, 2], [-1, 0, 1]]
```

开启 `unordered_output` 后，列表输出会递归忽略元素顺序；未开启时仍按原始列表顺序严格比较。

### STEP 4: 运行验证

```shell
leet-chaser run two-sum
```

### STEP 5: 调试单个用例

把当前要排查的用例写入 `debug.toml`，格式和 `cases.toml` 一致，但只保留一个 `[[cases]]`：

```toml
entrypoint = "twoSum"

[[cases]]
input = [[2, 7, 11, 15], 9]
output = [0, 1]
```

运行 debug 命令会默认读取当前题目目录下的 `debug.toml`，并逐行打印入口函数的变量变化：

```shell
leet-chaser debug two-sum
leet-chaser debug two-sum -t seen -t rest
leet-chaser debug two-sum -c two-sum/custom-debug.toml
```

## 标准示例

仓库内置了 LeetCode 1. Two Sum 的标准示例：

```shell
uv run leet-chaser run examples/two-sum
```

也内置了 LeetCode 206. Reverse Linked List 示例，用来展示 `linked_list` 类型元数据：

```shell
uv run leet-chaser run examples/reverse-linked-list
```

LeetCode 98. Validate Binary Search Tree 示例展示了 `binary_tree` 类型元数据：

```shell
uv run leet-chaser run examples/validate-binary-search-tree
```
