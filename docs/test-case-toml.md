# TOML Test Case Read And Write

## 需求内容

Leet-Chaser 需要支持读取和写入本地测试用例文件。测试用例文件使用 TOML 格式，用户可以手动编写和修改。

测试用例文件包含一个顶层 `entrypoint` 字段，并使用 `[[cases]]` 表示每个 case：

- `entrypoint`：顶层字段，指定 solution 的入口函数名。
- `input`：传给 LeetCode solution 方法的位置参数数组。
- `output`：期望返回值。

示例：

```toml
entrypoint = "twoSum"

[[cases]]
input = [[2, 7, 11, 15], 9]
output = [0, 1]

[[cases]]
input = [["flower", "flow", "flight"]]
output = "fl"
```

## 设计

继续使用 TOML。TOML 适合用户手写，支持注释，基础类型和数组表达清楚，可以覆盖 LeetCode 常见的数字、字符串、布尔值、数组、嵌套数组和表结构。

`input` 固定设计为参数数组。这样单参数题目写成 `input = [value]`，多参数题目写成 `input = [arg1, arg2]`，后续执行 solution 时可以直接使用 `solution_method(*case.input)`。

`entrypoint` 固定为顶层字符串，表示当前 case 文件要运行的 solution 方法名。本次只完成 TOML 读写与校验，不实现根据入口函数执行 solution 的逻辑。

不使用旧的 `[[mappings]]` 命名，因为测试文件表达的是测试用例，不是源到目标的映射关系。

## 实现方法

新增 `leet_chaser.case_file` 模块：

- `Case`：不可变 dataclass，保存 `input` 和 `output`。
- `CaseFile`：不可变 dataclass，保存 `entrypoint` 和用例列表。
- `read_case_file(path)`：从 TOML 文件读取入口函数和用例。
- `write_case_file(path, case_file)`：将入口函数和用例写入 TOML 文件。
- `parse_case_data(data)`：校验并解析已加载的 TOML 数据。
- `CaseFileError`：用例文件结构不合法时抛出。

读取使用 Python 3.12 内置 `tomllib`。写入使用 `tomli-w`，保持实现简单，避免手写 TOML 序列化逻辑。

CLI 的 `run` 命令已经接入读取逻辑，会在执行前加载 case 文件，并在文件结构不合法时给出参数错误。
