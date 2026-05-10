# Init Command

## 需求内容

Leet-Chaser 需要提供 `leet-chaser init <name>` 命令，方便用户快速创建一个新的题目目录。命令在执行目录下创建 `<name>` 子文件夹，并放入可直接编辑的 `solution.py` 和 `cases.toml`。

目录名需要对用户输入做统一处理，将特殊符号转换为 `-`，并在控制台打印最终创建的目录名。

## 设计

`init` 是独立 CLI 子命令，目录位置固定使用当前工作目录，避免用户需要额外传入路径参数。命令只创建新目录，不覆盖已有目录，防止误删用户已经写好的 solution 或测试用例。

名称规范化使用保守规则：连续的非英文字母和数字字符统一替换为单个 `-`，并移除首尾 `-`。如果名称里没有任何英文字母或数字，命令直接报参数错误。

`solution.py` 保持空文件，用户可以按题目需要自由粘贴 LeetCode 模板。`cases.toml` 使用仓库当前支持的 `[[cases]]` 格式，包含数组参数、字符串参数和返回值示例，方便用户直接修改。

## 实现方法

在 `leet_chaser.cli` 中新增：

- `CASE_TEMPLATE`：保存可被 `read_case_file` 读取的 TOML 样例。
- `SOLUTION_TEMPLATE`：保存空 solution 文件内容。
- `normalize_project_name(name)`：将 CLI 输入的名称转换成目录名。
- `init(name)`：创建 `<name>` 目录，并写入 `solution.py` 和 `cases.toml`。

测试覆盖：

- `test_init_creates_solution_workspace`：验证命令会创建目录、空 solution 文件和可解析的 case 文件。
- `test_normalize_project_name_replaces_special_symbols`：验证特殊符号会被转换为 `-`。
- `test_init_uses_normalized_directory_name`：验证命令使用规范化后的目录名。
- `test_init_rejects_names_without_letters_or_numbers`：验证全特殊符号名称会报错。
- `test_init_rejects_existing_directory`：验证已有目录不会被覆盖。
