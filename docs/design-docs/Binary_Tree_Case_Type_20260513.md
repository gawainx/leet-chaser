# Binary Tree Case Type

## 需求内容

用户在刷二叉树题目时，需要把 LeetCode 层序数组输入解析为二叉树节点，例如 `98. 验证二叉搜索树`、二叉树层序遍历、翻转二叉树等题目。`cases.toml` 和 `debug.toml` 需要支持声明二叉树参数，并在必要时支持二叉树返回值比较。

## 设计

新增高级 case 类型 `binary_tree`，复用现有 `input_types` / `output_type` 元数据：

```toml
entrypoint = "isValidBST"
input_types = ["binary_tree"]

[[cases]]
input = [[5, 1, 4, "null", "null", 3, 6]]
output = false
```

TOML 数组不能直接表达 `null`，所以空节点使用字符串 `"null"`。空数组解析为 `None`。树节点结构对齐 LeetCode Python 模板，包含 `val`、`left`、`right` 三个字段。

输出类型也支持 `binary_tree`，runner/debugger 在比较前把返回的 `TreeNode` 转回层序数组，并去掉末尾多余 `"null"`，让 `[1, 2, 3]` 和 `[1, 2, 3, "null", "null"]` 归一化后等价。

不支持树节点带父指针、N 叉树、二叉树 cycle、每个 case 单独覆盖类型元数据。

## 实现方法

- 新增 `src/leet_chaser/tree_types.py`，提供 `TreeNode`、`build_binary_tree`、`binary_tree_to_array`、`normalize_tree_value`。
- 更新 `src/leet_chaser/case_file.py`，把 `binary_tree` 加入支持类型，并在 `_parse_typed_value` 中解析层序数组。
- 更新 `src/leet_chaser/runner.py`，对 `binary_tree` 输出执行归一化比较。
- 补充单元测试覆盖普通树、空树、带 `"null"` 的稀疏树、非法空节点标记、返回树比较。
- 更新 README、`docs/advanced-case-types.md` 和 `docs/PROGRESS.md`。
