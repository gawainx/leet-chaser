# Init Advanced Type Template

## 需求内容

用户希望 `leet-chaser init` 支持 `-t` 参数，用来快速生成链表、二叉树和矩阵等常见输入类型的 `cases.toml`。实际面试刷题时，如果忘记在 TOML 中写 `input_types`，或写错二维数组嵌套结构，会导致误判或调试乌龙。

## 设计

新增 `leet-chaser init <name> -t <type>`。不传 `-t` 时保持现有 two-sum 默认模板不变。传入 `-t` 后，命令会把模糊类型名归一到内部高级类型：

- 链表：`linklist`、`linkedlist`、`linked_list`、`listnode`、`list`
- 二叉树：`bitree`、`binarytree`、`binary_tree`、`tree`、`treenode`
- 矩阵：`matrix`、`grid`、`2d-array`

链表和二叉树模板只默认第一个输入参数是特殊类型。链表模板使用 `input_types = ["linked_list"]` 和 `output_type = "linked_list"` 展示反转链表类题目；二叉树模板使用 `input_types = ["binary_tree"]` 展示验证二叉搜索树类题目。矩阵模板不声明额外类型，只展示二维数组作为第一个参数的 TOML 写法。暂不支持在 init 阶段配置多个特殊参数、输出类型独立选择或每个 case 不同类型。

## 实现方法

- 在 `src/leet_chaser/cli.py` 新增类型 alias 解析函数。
- 将固定 `CASE_TEMPLATE` 拆为默认模板、链表模板、二叉树模板和矩阵模板。
- `init` 增加 `-t/--type` 参数，解析失败时抛出 `typer.BadParameter`。
- 更新 README 和 `docs/init-command.md`。
- 补充 package 测试覆盖默认行为、链表 alias、二叉树 alias、矩阵 alias 和非法类型。
