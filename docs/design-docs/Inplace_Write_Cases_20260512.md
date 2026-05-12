# Inplace_Write_Cases_20260512

## 核心功能（WHAT）

为 `cases.toml` 和 `debug.toml` 增加顶级原地写入配置，让数组原地修改类题目可以按被修改后的输入参数进行比较，而不是按入口函数返回值比较。

推荐格式：

```toml
entrypoint = "moveZeroes"
inplace_write = true
inplace_index = 0

[[cases]]
input = [[0, 1, 0, 3, 12]]
output = [1, 3, 12, 0, 0]
```

### 需求背景（WHY）

LeetCode 上部分数组题要求方法原地修改输入数组，例如“移动零”。这类题的 Python 方法通常返回 `None`，真正的结果保存在输入参数本身。当前 Leet-Chaser 只比较函数返回值和 `output`，会把正确的原地实现误判为失败。

### 需求目标（GOAL）

- 用户可以在 TOML 顶层声明当前题目使用原地写入比较。
- 用户可以通过 0-based 参数下标指定被比较的输入参数。
- `run` 和 `debug` 使用相同的原地比较逻辑。
- `inplace_write = true` 时忽略返回值，并在返回值不是 `None` 时通过 Rich 输出 warning。
- 未声明原地写入配置的旧 case 行为保持不变。

### 范围边界

In Scope:

- 新增顶级 `inplace_write` 和 `inplace_index` 字段。
- `inplace_index` 只支持 0-based 整数下标。
- `run` 在调用后取 `case.input[inplace_index]` 作为 actual。
- `debug` 在调用后取 `case.input[inplace_index]` 作为 actual。
- 返回值不是 `None` 时输出 Rich warning，但不影响比较结果。
- 原地 actual 继续复用 `output_type` 归一化和展示逻辑。
- 更新 `docs/` 使用说明和进度记录。

Out of Scope:

- 不支持 case 级覆盖原地配置。
- 不支持多个输入参数同时作为比较结果。
- 不支持按参数名选择输入。
- 不实现自定义 matcher 或无序数组比较。
- 不改变 `input_types` / `output_type` 的既有语义。

## 实现流程（HOW）

当前 `case_file.py` 会读取顶级 `entrypoint`、`input_types`、`output_type`，并把每个 `[[cases]]` 解析为 `Case`。本次会在 `CaseFile` 上新增原地写入元数据：

- `inplace_write: bool = false`
- `inplace_index: int | None = None`

解析规则：

- `inplace_write` 缺省时为 `false`。
- `inplace_write` 必须是布尔值。
- `inplace_write = true` 时必须提供 `inplace_index`。
- `inplace_index` 必须是非负整数。
- 每个 case 的 `input` 参数数量必须能覆盖 `inplace_index`。
- `inplace_write = false` 时如果提供 `inplace_index`，视为无效配置，避免静默误解。

执行策略：

- runner 调用入口方法后先保留返回值。
- 普通 case 继续使用返回值作为 actual。
- 原地 case 使用调用后的 `test_case.input[inplace_index]` 作为 actual。
- 如果原地 case 的返回值不是 `None`，记录 warning 信息，CLI 用 Rich 打印。
- warning 不进入 failed/error 计数，只作为提示信息展示。

debug 策略：

- `debug_problem` 复用同一套 actual 选择逻辑。
- `ProblemDebugResult.passed` 基于选择后的 actual 判断。
- CLI debug 输出中展示的是最终参与比较的 actual。
- 原地返回值 warning 同样通过 Rich 打印。

## 测试用例

编译检查：

- 运行 `uv run pytest`，确认全部测试通过。

手工检查：

- 用“移动零”样例运行 `leet-chaser run`，确认 `None` 返回值不导致失败。
- 手动让原地题返回非 `None`，确认 CLI 打印 warning 且比较仍通过。
- 用 `debug.toml` 运行原地 case，确认 debug 输出显示修改后的数组。

回归检查：

- 不包含 `inplace_write` 的既有 two-sum、链表 case 行为不变。
- `inplace_index` 越界、缺失或类型错误时返回清晰的 `CaseFileError`。
- `output_type` 归一化仍能作用于原地 actual。
