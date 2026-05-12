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

更多单链表、双向链表和循环链表写法见 [docs/advanced-case-types.md](docs/advanced-case-types.md)。

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
