# Init Command

## 需求内容

Leet-Chaser 需要提供 `leet-chaser init <name>` 命令，方便用户快速创建一个新的题目目录。命令在执行目录下创建 `<name>` 子文件夹，并放入可直接编辑的 `solution.py` 和 `cases.toml`。

`init` 支持 `-t/--type` 参数，用于生成链表、二叉树或矩阵题目的 TOML 模板，避免用户在面试刷题时忘记写 `input_types` 或写错二维数组。

`init` 支持 `--question-number/-q` 参数，用于按公开 LeetCode 题号拉取 Python3 代码模板和题面示例，不需要登录、OAuth 或 cookie。题号初始化默认创建 `lt{题号三位}.{入口名}` 目录，例如 `leet-chaser init -q 1` 创建 `lt001.twoSum/`。LRU Cache 这类设计题会自动生成 `mode = "operations"` 的操作序列 case。

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

传入 `--question-number/-q` 时，命令会先拉取题目元数据，再提取 Python3 snippet 的入口方法或操作类名和题面 examples。目录名默认使用 `lt{题号三位}.{入口名}`；如果是 operations 题，入口名使用类名，例如 `lt146.LRUCache`。如果用户同时传入自定义 `name`，则使用自定义目录名。`--question-number` 与 `-t/--type` 不能同时使用，因为远程题目会生成具体 case，固定类型模板会产生语义冲突。

题号初始化只支持公开免费题目和题面示例，不承诺隐藏测试集、付费题、多语言模板或自动高级类型识别。网络失败、题号不存在、缺少 Python3 模板或示例无法解析时，命令会报错并且不创建目录。

题号初始化会输出操作进度：开始拉取题号、已获取题目标题和 slug、开始生成本地文件、写入完成。进度输出只在 `--question-number/-q` 路径启用，普通本地模板 init 保持原输出。

题号初始化生成的 `cases.toml` 会使用更适合阅读的数组格式：一维数组保持单行，二维或更深层数组按嵌套层级换行。这样数组题的样例不会被展开成每个元素一行，矩阵题仍保留行结构。operations 题会尽量保留 LeetCode 原始的 `operations/input/output` 三数组。

所有 init 生成的 `cases.toml` 都会在文件顶部写入可取消注释的配置提示。普通模式模板会提示 `input_types`、`output_type`、`inplace_write`、`inplace_index` 和 `unordered_output`，并列出当前支持的高级类型。operations 模式模板会提示 `operations`、`input`、`output` 必须等长，且第一项操作必须等于 `class_name`。这些提示全部是 TOML 注释，默认不改变样例的运行行为。

远程错误提示按失败阶段输出：题号查 slug 阶段使用 `lookup question number failed`，题目详情阶段使用 `fetch question detail failed`。HTTP 400/GraphQL error 会提示公开 GraphQL 查询或 schema 可能变化；网络错误会提示接口不可达；付费题和公开题库查不到会单独说明，方便后续定位是题目公开性问题、接口变化还是本地网络问题。

## 实现方法

在 `leet_chaser.cli` 中新增：

- `CASE_TEMPLATE_BY_TYPE`：保存默认、链表、二叉树和矩阵 TOML 样例。
- `CASE_TYPE_ALIASES`：保存 `-t/--type` 模糊匹配映射。
- `SOLUTION_TEMPLATE`：保存空 solution 文件内容。
- `normalize_project_name(name)`：将 CLI 输入的名称转换成目录名。
- `resolve_init_case_type(raw_case_type)`：将用户输入的模板类型归一为内部类型名。
- `init(name, case_type)`：创建 `<name>` 目录，并写入 `solution.py` 和匹配的 `cases.toml`。

在 `leet_chaser.leetcode_client` 中新增：

- `fetch_question_metadata(question_number)`：根据题号拉取公开 LeetCode 题目元数据。
- `fetch_title_slug(question_number)`：从题号查询题目 slug，并拒绝付费题。
- `fetch_question_data(title_slug)`：通过题目 slug 拉取标题、题面、Python3 snippets 和 metadata。
- `build_remote_init_files(metadata)`：生成默认目录名、`solution.py` 和 `cases.toml`。
- `parse_examples(content_html, parameter_names)`：从题面 examples 中提取输入输出 case。
- `parse_class_name_from_python_code(python_code)`：从设计题 Python3 snippet 中提取顶层类名。
- `parse_operations_example(raw_input, raw_output)`：解析 LeetCode 设计题的操作名数组、参数数组和输出数组。
- `leet_chaser.case_templates.NORMAL_CASE_CONFIG_COMMENTS`：普通模式 `cases.toml` 的可取消注释配置提示。
- `leet_chaser.case_templates.OPERATIONS_CASE_CONFIG_COMMENTS`：operations 模式 `cases.toml` 的可取消注释配置提示。

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
- `test_init_creates_remote_question_workspace`：验证 `-q` 会生成 `lt001.twoSum`、Python 模板和可解析 case。
- `test_init_creates_remote_operations_question_workspace`：验证 `-q` 会生成 `lt146.LRUCache` 和 operations mode case。
- `test_init_creates_remote_question_workspace`：同时验证远程 init 会输出题号拉取、题目详情、文件生成和写入进度。
- `test_init_remote_question_accepts_custom_directory_name`：验证自定义目录名会覆盖默认远程目录名。
- `test_init_remote_question_rejects_case_type`：验证 `-q` 与 `-t` 同时使用会报错且不创建目录。
- `test_post_graphql_reports_http_query_errors`：验证 HTTP 查询失败会包含阶段、状态码和接口变更提示。
- `test_post_graphql_reports_network_unreachable`：验证接口不可达会提示网络、DNS、代理或 LeetCode 可用性。
- `test_post_graphql_reports_graphql_schema_errors`：验证 GraphQL schema 错误会包含接口变更提示和原始 message。
- `test_remote_case_toml_keeps_one_dimensional_arrays_on_one_line`：验证远程 init 生成的 TOML 中一维数组保持单行。
- `test_remote_case_toml_formats_two_dimensional_arrays_across_lines`：验证二维数组按行换行。
- `test_remote_case_toml_formats_operations_mode`：验证远程 init 可生成 operations mode TOML。
- `test_build_remote_init_files_detects_operations_mode`：验证类模板 metadata 可生成 operations mode 文件。
- 本地和远程 init 模板测试同时验证生成文本包含关键注释字段，且注释不会影响 `read_case_file` 解析。
