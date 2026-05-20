# Custom Entry File

## 需求内容

用户需要在 `run` 和 `debug` 命令中指定入口文件。默认入口仍然是 `solution.py`，但可以通过参数运行 `slv.py`、`slv_enhanced.py` 等不同 solution 文件。

入口参数不能要求用户手写 `.py` 后缀。用户输入 `-e slv` 时，程序内部需要自动补全并加载 `slv.py`。

## 设计

`run` 和 `debug` 共同增加 `--entry/-e` 参数，默认值为 `solution.py`。参数类型使用 `Path`，这样可以兼容简单文件名、相对路径和绝对路径。

入口路径解析统一放到 runner 层：

- 如果用户传入的路径没有后缀，自动补全为 `.py`。
- 如果用户传入的是相对路径，基于 `problem_dir` 解析。
- 如果用户传入的是绝对路径，直接使用补全后的绝对路径。

这样 `leet-chaser run two-sum -e slv` 会加载 `two-sum/slv.py`，`leet-chaser debug two-sum -e slv_enhanced` 会加载 `two-sum/slv_enhanced.py`。默认行为保持读取 `solution.py`。

## 实现方法

主要改动：

- `src/leet_chaser/runner.py`
  - `run_problem(problem_dir, entry_file=Path("solution.py"))` 接收入口文件参数。
  - 新增 `resolve_entry_file(problem_dir, entry_file)`，集中处理 `.py` 后缀补全和相对路径解析。
- `src/leet_chaser/debugger.py`
  - `debug_problem(..., entry_file=Path("solution.py"))` 复用 `resolve_entry_file`。
- `src/leet_chaser/cli.py`
  - `run` 和 `debug` 命令增加 `--entry/-e` 参数，并传给核心函数。
- 文档同步说明 `-e slv` 会加载 `slv.py`。

验证方式：

- `tests/test_runner.py` 覆盖 `run_problem(..., entry_file=Path("slv"))` 自动加载 `slv.py`。
- `tests/test_debugger.py` 覆盖 `debug_problem(..., entry_file=Path("slv"))` 自动加载 `slv.py`。
- `tests/test_package.py` 覆盖 CLI `run -e slv` 和 `debug -e slv`。
