# Init_Question_Number_Template_20260514

## Related Design Doc

- `docs/design-docs/Init_Question_Number_Template_20260514.md`

## Stage #1: 远程题目元数据解析

### Task #1: 新增 LeetCode 公开题目 client

**Status:** Finished

**Files:** Create `src/leet_chaser/leetcode_client.py`; Modify `pyproject.toml` if an HTTP dependency is needed; Verify `tests/test_package.py` or new dedicated test file.

- Function: 根据 `question_number` 获取公开题目的标题、slug、Python3 code snippet、入口函数名和示例文本。
- Implementation Notes: 已新增 `leetcode_client.py`，通过公开 GraphQL 查询题号 slug 与题目详情；不处理 OAuth、cookie 或登录态；网络、HTTP、GraphQL、付费题、缺少 Python3 snippet 都转换为 `LeetCodeClientError`；请求设置 10 秒超时。
- Expected Verification Result: mock CLI 流程可返回结构化元数据并生成文件；错误路径在 CLI 层转为参数错误。

### Task #2: 生成远程 init 文件内容

**Status:** Finished

**Files:** Modify `src/leet_chaser/leetcode_client.py`; Verify parser tests.

- Function: 将题目元数据转换为目录名、`solution.py` 内容和 `cases.toml` 内容。
- Implementation Notes: 已实现 `build_remote_init_files`、`parse_examples` 和 LeetCode literal 解析；目录名使用 `lt{题号三位}.{入口名}`；`solution.py` 使用 Python3 snippet；`cases.toml` 从题面 examples 生成，无法解析出任何 case 时失败。
- Expected Verification Result: Two Sum mock 数据生成 `lt001.twoSum`、有效 Python 模板和可被现有 case loader 解析的 TOML。

## Stage #2: CLI 集成

### Task #3: 扩展 init 参数

**Status:** Finished

**Files:** Modify `src/leet_chaser/cli.py`; Verify `tests/test_package.py`.

- Function: 支持 `leet-chaser init --question-number 1` 和 `leet-chaser init -q 1`。
- Implementation Notes: `name` 已调整为可选；未传 `name` 且未传 `question_number` 时提示缺少参数；同时传入 `question_number` 和 `-t/--type` 时报参数冲突；用户同时传入 `name` 和 `question_number` 时用用户目录名覆盖默认 `lt{题号三位}.{入口名}` 目录名。
- Expected Verification Result: `tests/test_package.py` 验证新入口创建题号目录；旧入口和 `-t/--type` 测试保持通过。

### Task #4: 保持目录写入原子性

**Status:** Finished

**Files:** Modify `src/leet_chaser/cli.py`; Verify `tests/test_package.py`.

- Function: 远程拉取、解析和文件内容构建全部成功后再创建目录。
- Implementation Notes: 远程拉取与 case 文本构建在 `project_dir.mkdir()` 前完成；沿用已有目录保护；网络失败、解析失败、参数错误时不创建半成品目录。
- Expected Verification Result: `-q` 与 `-t` 冲突路径已覆盖不创建目录；已有目录仍沿用旧测试覆盖。

## Stage #3: 文档、回归和收尾

### Task #5: 更新用户文档

**Status:** Finished

**Files:** Modify `README.md`, `docs/init-command.md`, `docs/PROGRESS.md`.

- Function: 记录 `--question-number/-q` 用法、无登录限制和第一版能力边界。
- Implementation Notes: README、`docs/init-command.md` 和 `docs/PROGRESS.md` 已记录 `--question-number/-q` 用法、目录命名规则、无登录限制和第一版边界。
- Expected Verification Result: 文档包含示例命令和失败场景说明。

### Task #6: 整体验证与提交

**Status:** Finished

**Files:** Verify full test suite; Modify this plan with implementation notes.

- Function: 运行回归测试，更新计划任务状态和实现记录，并按仓库提交规范提交。
- Implementation Notes: 已运行局部和全量测试；提交信息使用 Conventional Commit，例如 `feat: add question number init workflow`。
- Expected Verification Result: `uv run pytest -q` 已通过；工作区只包含本需求相关改动。
