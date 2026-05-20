# Debug Command

## 需求内容

Leet-Chaser 需要新增 `debug` 命令，用于针对一个单独的本地 case 调试入口文件里的入口函数。命令默认调试 `solution.py`，也可以通过 `--entry/-e` 指定其他入口文件。命令形式为：

```shell
leet-chaser debug <problem-dir> --case/-c <toml-path> --trace/-t <arg-name>
leet-chaser debug <problem-dir> --entry/-e <entry-file>
```

`--case` 和 `-c` 功能一致，表示单独 debug case 的 TOML 文件路径，默认值为 `<problem-dir>/debug.toml`。debug 场景不从 `cases.toml` 里按 index 选择用例，而是要求用户把当前要排查的最小复现用例写成独立 TOML 文件，便于反复修改和运行。

`--trace` 和 `-t` 功能一致，表示需要额外关注的变量名或表达式，可重复传入。没有指定 `--trace` 时，命令默认打印入口函数逐行执行过程和局部变量变化。

`--entry` 和 `-e` 功能一致，表示要加载的入口文件，默认值为 `solution.py`。用户传入的入口参数不强制写 `.py` 后缀；如果路径没有后缀，程序会自动补全 `.py`，因此 `-e slv` 会加载 `<problem-dir>/slv.py`。

推荐的 `debug.toml` 格式复用现有 case 文件结构，但只包含一个 `[[cases]]`：

```toml
entrypoint = "twoSum"

[[cases]]
input = [[2, 7, 11, 15], 9]
output = [0, 1]
```

## 设计

调试能力选择基于 `snoop` 实现。它可以通过装饰器包装目标函数，输出逐行执行过程、局部变量变化和指定 `watch` 表达式，正好匹配本期需求。项目不自研 `sys.settrace` 追踪器，避免重复实现行号、源码展示、变量变更检测和表达式 watch 这些通用能力。

`debug` 命令复用当前 `run` 命令的 solution 加载模型：

- `<problem-dir>/solution.py` 或 `--entry/-e` 指定的入口文件提供 LeetCode 风格的 `Solution` 类。
- debug TOML 里的 `entrypoint` 指向 `Solution` 上的入口方法。
- debug TOML 必须只包含一个 `[[cases]]`，命令只执行这一条 case。
- 每次 debug 创建一个新的 `Solution()` 实例，再调用入口方法。

默认只追踪入口函数本身，不深入追踪 helper 函数。这样输出更贴近刷题时最常见的排查路径，也避免递归、循环和 helper 调用导致日志过量。后续如有需要，可以再扩展 `--depth` 映射到 `snoop.snoop(depth=...)`。

## 实现方法

新增 `leet_chaser.debugger` 模块承载核心逻辑：

- `ProblemDebugError`：表示 debug case 文件缺失、case 数量不合法等 debug 专属错误。
- `ProblemDebugResult`：记录 solution 路径、case 路径、入口函数、输入、预期输出、实际输出和 trace 表达式。
- `debug_problem(problem_dir, case_path=None, traces=(), entry_file=Path("solution.py"))`：读取 debug TOML，加载入口文件，使用 `snoop.snoop(watch=traces)` 包装入口方法并执行单个 case。

CLI 新增 `debug` 命令：

- `leet-chaser debug <problem-dir>` 默认读取 `<problem-dir>/debug.toml`。
- `leet-chaser debug <problem-dir> -c custom.toml` 使用指定 debug TOML。
- `leet-chaser debug <problem-dir> -t seen -t rest` 把 `seen` 和 `rest` 传给 `snoop` 的 `watch`。
- `leet-chaser debug <problem-dir> -e slv` 加载 `<problem-dir>/slv.py`。

验证方式：

- 单元测试覆盖默认 `debug.toml` 执行。
- 单元测试覆盖 `--trace/-t` 表达式传递给 `snoop`。
- 单元测试覆盖 `--entry/-e` 参数省略 `.py` 后缀时自动补全。
- 单元测试覆盖 debug TOML 只能包含一个 `[[cases]]`。
- CLI 测试覆盖 debug 成功时退出码为 `0`，失败时退出码为 `1`。
