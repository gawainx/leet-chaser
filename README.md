# Leet-Chaser

本地运行 leetcode solution 的命令行框架。

## 使用方法

### STEP 0: 初始化题目目录

```shell
leet-chaser init two-sum
```

命令会在当前目录创建 `two-sum/solution.py` 和 `two-sum/cases.toml`。

### STEP 1 编写 solution 文件

```python
class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        return []
```

### STEP 2: 填写测试用例 `cases.toml`
```toml
[[cases]]
input = [[2, 7, 11, 15], 9]
output = [0, 1]

[[cases]]
input = [["flower", "flow", "flight"]]
output = "fl"
```

### STEP 3: 运行验证

```shell
leet-chaser run <solution.py> <cases.toml>
```
