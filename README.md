# Leet-Chaser

本地运行 leetcode solution 的命令行框架。

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

`input` 是传给 solution 方法的位置参数数组，`output` 是期望返回值。

```toml
[[cases]]
input = [[2, 7, 11, 15], 9]
output = [0, 1]

[[cases]]
input = [["flower", "flow", "flight"]]
output = "fl"
```

### STEP 4: 运行验证

```shell
leet-chaser run solution.py cases.toml
```
