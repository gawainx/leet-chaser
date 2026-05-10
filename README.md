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
cd two-sum
leet-chaser run .
```

## uvx 直接运行

不想把命令安装到当前环境时，可以用 `uvx` 临时运行：

```shell
uvx leet-chaser --help
uvx leet-chaser init two-sum
cd two-sum
uvx leet-chaser run .
```

## 使用方法

### STEP 1: 初始化题目目录

```shell
leet-chaser init two-sum
cd two-sum
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

### STEP 4: 运行验证

```shell
leet-chaser run .
```

## 标准示例

仓库内置了 LeetCode 1. Two Sum 的标准示例：

```shell
uv run leet-chaser run examples/two-sum
```
