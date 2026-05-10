# Leet-Chaser

本地运行 leetcode solution 的命令行框架。

## 使用方法

### STEP 1 编写 solution 文件

```python
class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        return []
```

### STEP 2: 填写测试用例 `cases.toml`
```toml
[[mappings]]
input = "src_a"
output = "dst_a"

[[mappings]]
input = "src_b"
output = "dst_b"
```

### STEP 3: 运行验证

```shell
leet-chaser <solution.py> <case.toml>
```

