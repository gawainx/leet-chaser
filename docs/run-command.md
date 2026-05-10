# Run Command

## 需求内容

Leet-Chaser 需要实现核心运行逻辑 `run`。用户传入题目文件夹后，命令自动读取该文件夹下的 `solution.py` 和 `cases.toml`，再根据 `cases.toml` 中的 `entrypoint` 配置调用 `Solution` 类上的同名方法。

每个 `[[cases]]` 表示一个测试用例。`input` 是传给入口方法的位置参数数组，`output` 是期望返回值。命令需要执行所有用例，收集所有失败结果，并在最后统一展示通过和失败情况。

运行行为需要尽可能对齐 LeetCode Python 平台，避免 `Solution` 实例生命周期、类变量和模块全局变量的差异导致本地结果与平台结果不一致。

## 设计

`run` 的 CLI 入参改为题目文件夹：

```shell
leet-chaser run <problem_dir>
```

命令固定读取：

- `<problem_dir>/solution.py`
- `<problem_dir>/cases.toml`

Python solution 的支持范围先保持为标准 LeetCode 形式：

```python
class Solution:
    def entrypoint(self, ...):
        ...
```

本期不支持顶层函数入口。这样可以保持执行模型清晰，也更贴近 LeetCode 的默认 Python 模板。

生命周期设计按同一次运行加载一次 `solution.py` 模块、每个 case 创建一个新的 `Solution()` 实例处理。这样模块级全局变量和类变量会在同一次 `run` 的多个 case 之间保留，实例变量会按 case 隔离，和 LeetCode 官方说明中的同一程序实例、多 case 调用模型保持一致。

单个 case 的调用方式为：

```python
instance = Solution()
result = getattr(instance, entrypoint)(*case.input)
```

结果比较先使用 Python 的 `==` 精确比较 `actual` 和 `output`。如果题目存在多个合法答案，本期由用户在 `cases.toml` 中写入和当前实现一致的期望值，后续再扩展 matcher 或 validator。

失败处理采用跑完所有用例再汇总的方式：

- 返回值和期望值不相等时，记录该 case 的 expected 和 actual。
- case 调用过程中抛异常时，记录该 case 的异常类型和异常信息。
- `solution.py` 导入失败、`Solution` 不存在、`entrypoint` 不存在时属于整体运行错误，命令无法进入 case 循环。

退出码规则：

- 所有 case 通过时退出码为 `0`。
- 存在任一 case 失败或异常时退出码非 `0`。
- 整体运行错误时退出码非 `0`。

## 实现方法

新增核心运行模块，并引入必要的类和函数封装。模块内部需要把 CLI、solution 加载、case 执行和结果汇总拆开，保持代码仓符合 Python 模块化设计规范，提高核心逻辑的可读性、可测试性和后续扩展空间：

- `run_problem(problem_dir)`：读取题目目录中的 `solution.py` 和 `cases.toml`，执行全部 case，并返回运行结果。
- `load_solution_module(solution_path)`：从指定 Python 文件加载 solution 模块。
- `resolve_solution_method(module, entrypoint)`：校验 `Solution` 类和入口方法是否存在。
- `run_cases(solution_class, entrypoint, cases)`：逐个 case 新建 `Solution()` 实例并调用入口方法。

运行结果使用结构化数据表达，便于 CLI 输出和单元测试断言：

- 通过 case 记录 case index、expected 和 actual。
- 失败 case 记录 case index、expected、actual。
- 异常 case 记录 case index、expected、异常类型和异常信息。

CLI `run` 命令只负责参数处理、调用核心运行逻辑、打印汇总结果和设置退出码。核心逻辑不直接依赖 Rich 输出，方便测试。

测试覆盖：

- 传入题目目录后会自动读取 `solution.py` 和 `cases.toml`。
- 每个 case 都会创建新的 `Solution()` 实例，实例变量不会跨 case 污染。
- 模块全局变量和类变量会在同一次 run 的多个 case 间保留。
- 多个失败 case 会全部执行并统一收集。
- case 抛异常时不会阻断后续 case。
- 缺少 `Solution`、缺少入口方法、solution 导入失败会返回整体运行错误。
- CLI 在全部通过时返回 `0`，存在失败或整体运行错误时返回非 `0`。
