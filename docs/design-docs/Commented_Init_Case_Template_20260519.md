# Commented Init Case Template

## 需求内容

`leet-chaser init` 新建题目时，`cases.toml` 需要展示当前支持的配置字段。字段以 TOML 注释形式出现，用户可以按题目需要取消注释启用，避免不知道如何配置高级类型、原地写入、顺序无关输出或 operations 模式。

本需求覆盖本地模板初始化和 LeetCode 题号初始化。生成后的 `cases.toml` 必须仍然可以直接被现有解析器读取和运行。

## 设计

普通 entrypoint 模式模板保留可运行字段：

- `entrypoint`
- `[[cases]]`
- `input`
- `output`

并在文件顶部增加可取消注释的配置提示：

- `input_types`
- `output_type`
- `inplace_write`
- `inplace_index`
- `unordered_output`

提示中列出当前支持的类型枚举：`raw`、`linked_list`、`doubly_linked_list`、`circular_linked_list`、`binary_tree`。

operations 模式与普通模式互斥。普通模板只用注释说明 operations 是另一种模式，不嵌入完整 operations 示例，避免用户误把两套结构混用。远程初始化识别到设计题时，生成 operations 专用模板，保留可运行字段：

- `mode = "operations"`
- `class_name`
- `[[cases]]`
- `operations`
- `input`
- `output`

operations 模板增加注释说明 `operations`、`input`、`output` 三个数组必须等长，且 `operations[0]` 必须等于 `class_name`。

## 实现方法

新增共享注释模板常量，由本地 `CASE_TEMPLATE_BY_TYPE` 和远程 `format_remote_case_toml()` 复用，保证两条 init 路径提示一致。

本地模板继续保持当前样例内容，只在样例前插入注释区。远程题号模板在格式化时插入同样的普通模式注释区；operations 远程模板插入 operations 专用注释区。

测试验证生成文本包含关键注释字段，同时继续通过 `read_case_file()` 解析，确保注释不会改变运行行为。
