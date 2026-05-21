# Ctrl+C Traceback Output

## 需求内容

刷题时遇到二分查找等死循环场景，用户按 `Ctrl+C` 后需要看到 `KeyboardInterrupt` 的异常堆栈，方便确认卡住的调用路径。当前命令入口直接交给 Typer app，Typer 会处理键盘中断并隐藏 Python traceback。

## 设计

命令行入口继续调用 Typer app，保留 Typer/Click 的正常命令解析、错误处理和上下文生命周期。入口只在运行期间临时安装 `SIGINT` handler，在用户按 `Ctrl+C` 时直接打印信号打断位置的当前 Python frame 栈。

查证结果是 Typer 当前 `_main()` 会把 `KeyboardInterrupt` 转换成 `click.exceptions.Exit(130)`，外层无法再拿到原始用户代码栈。SIGINT handler 在 Typer 转换异常前运行，可以用标准库 `traceback.format_stack(frame)` 打印被中断的调用栈，然后继续抛出 `KeyboardInterrupt`，让 Typer/Click 按原有退出流程返回 130。

## 实现方法

- `pyproject.toml` 的 `leet-chaser` console script 从 `leet_chaser.cli:app` 改为 `leet_chaser.cli:main`。
- `src/leet_chaser/cli.py` 增加 `print_sigint_stack()`，收到 SIGINT 时打印 `Traceback (most recent call last):`、当前 frame 栈和 `KeyboardInterrupt`。
- `src/leet_chaser/cli.py` 的 `main()` 临时安装该 SIGINT handler，正常调用 `app()`，结束时恢复原 handler。
- `tests/test_package.py` 增加 `test_print_sigint_stack_prints_without_frame` 和 `test_print_sigint_stack_prints_supplied_frame`，验证 handler 输出 fallback 文本和被中断函数名。

验证命令：

```bash
uv run pytest -q
conda run -n dev python -m pytest tests/test_package.py::test_print_sigint_stack_prints_supplied_frame -q
/opt/miniconda3/envs/dev/bin/leet-chaser run lt034.searchRange
```
