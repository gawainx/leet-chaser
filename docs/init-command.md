# Init Command

## 需求内容

Leet-Chaser 需要提供 `leet-chaser init <name>` 命令，方便用户快速创建一个新的题目目录。命令在执行目录下创建 `<name>` 子文件夹，并放入可直接编辑的 `solution.py` 和 `cases.toml`。

`init` 支持 `-t/--type` 参数，用于生成链表、二叉树或矩阵题目的 TOML 模板，避免用户在面试刷题时忘记写 `input_types` 或写错二维数组。

目录名需要对用户输入做统一处理，将特殊符号转换为 `-`，并在控制台打印最终创建的目录名。

## 设计

`init` 是独立 CLI 子命令，目录位置固定使用当前工作目录，避免用户需要额外传入路径参数。命令只创建新目录，不覆盖已有目录，防止误删用户已经写好的 solution 或测试用例。

名称规范化使用保守规则：连续的非英文字母和数字字符统一替换为单个 `-`，并移除首尾 `-`。如果名称里没有任何英文字母或数字，命令直接报参数错误。

`solution.py` 保持空文件，用户可以按题目需要自由粘贴 LeetCode 模板。`cases.toml` 使用仓库当前支持的 `entrypoint` 和 `[[cases]]` 格式，包含入口函数名、数组参数、字符串参数和返回值示例，方便用户直接修改。

不传 `-t` 时，命令保持默认 two-sum 模板。传入 `-t` 后，命令会对类型名做模糊匹配：

- `linklist`、`linkedlist`、`linked_list`、`listnode`、`list` 生成 `linked_list` 模板。
- `bitree`、`binarytree`、`binary_tree`、`tree`、`treenode` 生成 `binary_tree` 模板。
- `matrix`、`grid`、`2d-array` 生成二维矩阵输入模板。

链表和二叉树模板只默认每个 case 的第一个参数是特殊类型。矩阵模板不声明 `input_types`，只提供二维数组输入例子。

## 实现方法

在 `leet_chaser.cli` 中新增：

- `CASE_TEMPLATE_BY_TYPE`：保存默认、链表、二叉树和矩阵 TOML 样例。
- `CASE_TYPE_ALIASES`：保存 `-t/--type` 模糊匹配映射。
- `SOLUTION_TEMPLATE`：保存空 solution 文件内容。
- `normalize_project_name(name)`：将 CLI 输入的名称转换成目录名。
- `resolve_init_case_type(raw_case_type)`：将用户输入的模板类型归一为内部类型名。
- `init(name, case_type)`：创建 `<name>` 目录，并写入 `solution.py` 和匹配的 `cases.toml`。

测试覆盖：

- `test_init_creates_solution_workspace`：验证命令会创建目录、空 solution 文件和可解析的 case 文件。
- `test_init_creates_linked_list_case_template`：验证 `-t linklist` 会生成链表高级类型模板。
- `test_init_creates_binary_tree_case_template`：验证 `-t bitree` 会生成二叉树高级类型模板。
- `test_init_creates_matrix_case_template`：验证 `-t matrix` 会生成二维矩阵输入模板。
- `test_init_rejects_unknown_case_template_type`：验证未知模板类型会报错且不创建目录。
- `test_resolve_init_case_type_accepts_fuzzy_aliases`：验证常见模糊类型名可被解析。
- `test_normalize_project_name_replaces_special_symbols`：验证特殊符号会被转换为 `-`。
- `test_init_uses_normalized_directory_name`：验证命令使用规范化后的目录名。
- `test_init_rejects_names_without_letters_or_numbers`：验证全特殊符号名称会报错。
- `test_init_rejects_existing_directory`：验证已有目录不会被覆盖。
