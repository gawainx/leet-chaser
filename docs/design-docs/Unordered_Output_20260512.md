# Unordered Output Comparison

## 需求内容

用户在求解三数之和时，需要支持 LeetCode 约束“输出的顺序和三元组的顺序并不重要”。当前 runner 对普通列表输出使用严格相等比较，会把顺序不同但语义等价的答案判为失败。

## 设计

新增顶层 case 元数据 `unordered_output = true`。默认值为 `false`，保持既有题目的严格顺序比较。

开启后，runner 对实际输出和期望输出构造递归顺序无关比较 key。列表元素会先转换成 key 再排序比较，所以可以同时覆盖三数之和的外层结果顺序和单个三元组内部顺序。

该能力不和题目名称绑定，适用于所有以列表表达“集合式答案”的题目。链表等 typed output 仍先按既有逻辑归一化，再由比较逻辑决定是否启用顺序无关比较。

## 实现方法

- `CaseFile` 新增 `unordered_output: bool` 字段。
- `read_case_file` 解析顶层 `unordered_output`，非布尔值报 `CaseFileError`。
- `write_case_file` 在字段为 `true` 时写回 TOML。
- `run_cases` 改用 `compare_case_values`，默认严格比较，开启后使用 `unordered_case_key` 比较。
- 测试覆盖 three-sum 顺序不同通过、缺少结果失败、默认严格比较不变、TOML 读写和非法类型校验。
