# Init_Question_Number_Template_20260514

## 核心功能（WHAT）

为 `leet-chaser init` 增加 `--question-number/-q` 参数。用户执行 `leet-chaser init --question-number 1` 或 `leet-chaser init -q 1` 时，命令从公开 LeetCode 题目信息中拉取题目标题、Python3 代码模板和题面示例，并生成本地题目目录、`solution.py` 和 `cases.toml`。

### 需求背景（WHY）

当前 `init` 已支持手动传入目录名，并通过 `-t/--type` 生成基础 case 模板。用户在按 LeetCode 题号刷题时，仍需要手动查题、复制 Python 模板、复制示例输入输出，再整理成 TOML。这个流程重复且容易写错入口函数名、参数结构或示例值。

用户明确不希望管理 OAuth、cookie 或登录态，所以第一版只依赖公开可访问题目信息，不处理账号相关能力。

### 需求目标（GOAL）

- 支持 `leet-chaser init --question-number/-q <number>`。
- 根据题号解析公开题目的标题和 Python3 入口函数名，目录名默认使用 `lt{题号三位}.{入口名}`，例如 `lt001.twoSum`。
- 从题目信息中提取 Python3 code snippet，写入 `solution.py`。
- 从题面示例提取输入输出，写入 `cases.toml`。
- 保持现有 `leet-chaser init <name>` 和 `-t/--type` 行为不变。
- 网络、题号不存在、付费题或数据格式无法解析时，给出清晰错误，不创建半成品目录。

### 范围边界

In Scope:

- 免费公开题目。
- Python3 模板。
- 题面 examples 转换为 TOML cases。
- 目录创建、文件写入和已有目录保护沿用当前 `init` 规则。
- 单元测试通过 mock 网络响应覆盖成功和失败路径。

Out of Scope:

- OAuth、cookie、登录态和用户私有信息。
- 付费题内容拉取。
- 隐藏测试集或完整 LeetCode judge case 拉取。
- 多语言模板选择。
- 自动识别并补全 `input_types`、`output_type` 的高级类型元数据。
- 在线提交或运行 LeetCode 官方 judge。

## 实现流程（HOW）

当前 `src/leet_chaser/cli.py` 中 `init(name, case_type)` 负责目录名规范化、目录创建和写入固定模板。新功能推荐把远程题目逻辑拆出独立模块，避免 CLI 文件继续膨胀。

推荐新增 `src/leet_chaser/leetcode_client.py`：

- `fetch_question_metadata(question_number: int) -> LeetCodeQuestionMetadata`：根据题号拉取公开题目信息。
- `LeetCodeQuestionMetadata`：记录题号、标题、slug、Python3 snippet、入口函数名、示例输入输出原文。
- `build_remote_init_files(metadata: LeetCodeQuestionMetadata) -> RemoteInitFiles`：把元数据转换为目录名、`solution.py` 内容和 `cases.toml` 内容。

CLI 层调整：

- `init` 增加 `question_number: int | None = typer.Option(None, "--question-number", "-q", min=1, help=...)`。
- 当传入 `question_number` 时，`name` 变为可选参数；目录名优先使用 `lt{题号三位}.{入口名}`。题号不足三位时左侧补零，超过三位时保留完整数字，例如 `lt001.twoSum`、`lt1234.someMethod`。如果用户同时传入 `name`，使用用户提供的目录名。
- 当未传入 `question_number` 时，保持当前 `name` 必填语义。由于 Typer 对可选 positional 的交互需要谨慎处理，第一版可将签名调整为 `name: str | None = typer.Argument(None)`，并在函数体里手动校验：未传 `name` 且未传 `question_number` 时抛出参数错误。
- `case_type` 与 `question_number` 同时传入时，第一版推荐直接报错，因为远程示例已经生成具体 case，`-t` 的固定模板会产生语义冲突。

数据源决策：

- 不接入 OAuth。
- 使用公开网页背后的题目元数据接口或公开题库映射。实现时封装在 client 内，调用点只依赖本地数据结构。
- 给网络请求设置超时，并把 HTTP 错误、题号不存在、缺少 Python3 snippet、示例无法解析转为面向 CLI 的错误信息。

示例解析策略：

- 先支持 LeetCode 常见格式：`Input: ...`、`Output: ...`、多参数形式如 `nums = [2,7,11,15], target = 9`。
- 将 `null` 转为 TOML 可表达的 `"null"` 或 Python 值转换后的字符串占位，具体规则与现有高级类型文档保持一致。
- 无法可靠解析的示例不静默丢弃；如果没有任何可用 case，命令失败并说明原因。

## 测试用例

编译检查:

- `uv run pytest tests/test_package.py -q`

手工检查:

- `leet-chaser init --question-number 1` 创建 `lt001.twoSum/`。
- `leet-chaser init -q 1 custom-two-sum` 创建 `custom-two-sum/`。
- `leet-chaser init -q 1 -t matrix` 报参数冲突错误。

回归检查:

- 现有 `leet-chaser init two-sum` 行为不变。
- 现有 `leet-chaser init reverse-list -t linklist` 行为不变。
- 已存在目录时不覆盖。
- 网络失败、题号不存在、缺少 Python3 模板时不创建目录。
