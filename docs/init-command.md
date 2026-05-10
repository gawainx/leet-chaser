# Init Command

## 需求内容

Leet-Chaser 需要提供 `leet-chaser init <name>` 命令，方便用户快速创建一个新的题目目录。命令在执行目录下创建 `<name>` 子文件夹，并放入可直接编辑的 `solution.py` 和 `cases.toml`。

## 设计

`init` 是独立 CLI 子命令，目录位置固定使用当前工作目录，避免用户需要额外传入路径参数。命令只创建新目录，不覆盖已有目录，防止误删用户已经写好的 solution 或测试用例。

`solution.py` 保持空文件，用户可以按题目需要自由粘贴 LeetCode 模板。`cases.toml` 使用仓库当前支持的 `[[cases]]` 格式，包含数组参数、字符串参数和返回值示例，方便用户直接修改。

## 实现方法

在 `leet_chaser.cli` 中新增：

- `CASE_TEMPLATE`：保存可被 `read_case_file` 读取的 TOML 样例。
- `SOLUTION_TEMPLATE`：保存空 solution 文件内容。
- `init(name)`：创建 `<name>` 目录，并写入 `solution.py` 和 `cases.toml`。

测试覆盖：

- `test_init_creates_solution_workspace`：验证命令会创建目录、空 solution 文件和可解析的 case 文件。
- `test_init_rejects_existing_directory`：验证已有目录不会被覆盖。
