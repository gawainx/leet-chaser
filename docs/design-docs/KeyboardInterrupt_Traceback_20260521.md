# Ctrl+C Traceback Output

## 需求内容

刷题时遇到二分查找等死循环场景，用户按 `Ctrl+C` 后需要看到 `KeyboardInterrupt` 的异常堆栈，方便确认卡住的调用路径。当前命令入口直接交给 Typer app，Typer 会处理键盘中断并隐藏 Python traceback。

## 设计

命令行入口改为项目自己的 `main()`，由 `main()` 调用 Typer app，并关闭 Typer 的 standalone exception handling。这样普通参数错误仍由命令函数抛给 Typer 流程处理，`KeyboardInterrupt` 则能在最外层被项目代码捕获。

中断后使用标准库 `traceback.print_exc()` 输出完整 traceback，并以 shell 约定的 130 状态码退出。

## 实现方法

- `pyproject.toml` 的 `leet-chaser` console script 从 `leet_chaser.cli:app` 改为 `leet_chaser.cli:main`。
- `src/leet_chaser/cli.py` 的 `main()` 使用 `app(standalone_mode=False)` 执行命令，捕获 `KeyboardInterrupt` 后打印 traceback 并 `SystemExit(130)`。
- `tests/test_package.py` 增加 `test_main_prints_keyboard_interrupt_traceback`，验证 `main()` 会输出 traceback、包含 `KeyboardInterrupt`，并返回 130。

验证命令：

```bash
uv run pytest tests/test_package.py::test_main_prints_keyboard_interrupt_traceback tests/test_package.py::test_run_command_prints_immediate_case_status_before_details -q
```
