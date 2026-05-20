# Custom Entry File 实现计划

> **给 Claude：** 必需工作流：使用 superpowers:executing-plans 逐任务实现此计划。

**目标：** 让 `run` 和 `debug` 支持通过 `--entry/-e` 指定入口文件，并在用户省略 `.py` 后缀时自动补全。

**相关设计文档：** `docs/design-docs/Custom_Entry_File_20260520.md`

**架构：** CLI 只负责接收入口参数，runner 层统一解析入口路径。`run_problem` 和 `debug_problem` 复用同一套 `.py` 后缀补全和相对路径解析逻辑，保持默认 `solution.py` 行为不变。

**技术栈：** Python 3.12、Typer、pytest、uv。

**范围 / 非范围：** 本次只支持指定 Python 入口文件和自动补全 `.py` 后缀；不新增自定义类名、函数入口或 operations debug 能力。

---

## Phase #1: 核心入口解析

### Task #1: runner 支持入口文件参数

**状态：** Finished

**文件：**
- 修改：`src/leet_chaser/runner.py`
- 验证：`tests/test_runner.py`

- 功能：`run_problem` 支持接收入口文件参数，默认仍为 `solution.py`。
- 实现说明：新增 `resolve_entry_file`，当入口参数没有后缀时补全 `.py`，相对路径基于 `problem_dir` 解析。
- 预期验证结果：`run_problem(problem_dir, entry_file=Path("slv"))` 加载 `problem_dir/slv.py` 并通过 case。
- 完成时间：2026-05-20

### Task #2: debug 复用入口解析

**状态：** Finished

**文件：**
- 修改：`src/leet_chaser/debugger.py`
- 验证：`tests/test_debugger.py`

- 功能：`debug_problem` 支持接收入口文件参数，默认仍为 `solution.py`。
- 实现说明：复用 runner 的 `resolve_entry_file`，避免 run/debug 路径规则分叉。
- 预期验证结果：`debug_problem(problem_dir, entry_file=Path("slv"))` 加载 `problem_dir/slv.py` 并通过 debug case。
- 完成时间：2026-05-20

## Phase #2: CLI 与文档

### Task #3: CLI 暴露 --entry/-e

**状态：** Finished

**文件：**
- 修改：`src/leet_chaser/cli.py`
- 验证：`tests/test_package.py`

- 功能：`leet-chaser run` 和 `leet-chaser debug` 支持 `--entry/-e`。
- 实现说明：Typer 参数类型使用 `Path`，默认 `Path("solution.py")`，传给核心函数。
- 预期验证结果：CLI `run -e slv` 和 `debug -e slv` 都加载 `slv.py`。
- 完成时间：2026-05-20

### Task #4: 文档和进度记录

**状态：** Finished

**文件：**
- 修改：`README.md`
- 修改：`README_en.md`
- 修改：`docs/run-command.md`
- 修改：`docs/debug-command.md`
- 修改：`docs/PROGRESS.md`
- 创建：`docs/design-docs/Custom_Entry_File_20260520.md`
- 创建：`docs/plans/2026-05-20-custom-entry-file.md`

- 功能：记录入口参数行为、默认值和 `.py` 自动补全规则。
- 实现说明：中文和英文 README 都给出 `-e slv` 示例，设计文档记录需求、设计和实现方法。
- 预期验证结果：文档明确说明用户不需要输入 `.py` 后缀，程序会自动补全。
- 完成时间：2026-05-20
