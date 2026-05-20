# LeetCode CN Init 实现计划

> **给 Claude：** 必需工作流：使用 superpowers:executing-plans 逐任务实现此计划。

**目标：** 让 `leet-chaser init --question-number` 优先使用 `leetcode.cn` 拉取题目数据，并在短暂网络波动时自动重试。

**相关设计文档：** `docs/design-docs/LeetCode_CN_Init_20260520.md`

**架构：** 在 `leetcode_client.py` 中保留现有解析与文件生成流程，新增 GraphQL endpoint 配置、轻量重试和中国站 schema 适配。题号查 slug 优先走 `leetcode.cn` 的 `problemsetQuestionListV2`，详情查询优先走中国站 `question` 接口；中国站失败时回退原 `leetcode.com` 查询。

**技术栈：** Python 3.12、标准库 `urllib.request`、pytest、Typer CLI。

**范围 / 非范围：** 本次只处理公开题目初始化的远程请求稳定性和中国站兼容；不新增登录态、cookie、代理配置或 UI 测试。

---

## Phase #1: 远程请求适配

### Task #1: GraphQL endpoint 与 retry

**状态：** Finished

**文件：**
- 修改：`src/leet_chaser/leetcode_client.py`
- 验证：`tests/test_package.py`

- 功能：让 GraphQL 请求可指定 endpoint，并对 timeout / URL error 做有限重试。
- 实现说明：保留 `post_graphql(payload, operation=...)` 默认签名兼容现有测试；新增 endpoint 参数和 3 次尝试，错误信息包含 endpoint 名称。
- 预期验证结果：mock timeout 前两次失败第三次成功；持续失败时仍抛出 `LeetCodeClientError`。
- 完成时间：2026-05-20

### Task #2: 中国站题号与详情查询

**状态：** Finished

**文件：**
- 修改：`src/leet_chaser/leetcode_client.py`
- 验证：`tests/test_package.py`

- 功能：优先从 `leetcode.cn` 查询题号 slug 和题目详情，失败后回退 `leetcode.com`。
- 实现说明：中国站题号查询使用 `problemsetQuestionListV2(limit: 1, skip: question_number - 1)` 并校验 `questionFrontendId`；详情查询使用中国站 `question(titleSlug:)`，读取英文 `content` 保持现有 example 解析稳定。
- 预期验证结果：单元测试覆盖中国站成功、失败回退国际站、付费题提示。
- 完成时间：2026-05-20

## Phase #2: 文档和验证

### Task #3: 文档更新与回归

**状态：** Finished

**文件：**
- 创建：`docs/design-docs/LeetCode_CN_Init_20260520.md`
- 修改：`docs/init-command.md`
- 修改：`docs/PROGRESS.md`
- 验证：`uv run pytest tests/test_package.py -q`，`uv run pytest -q`

- 功能：记录中国站优先、国际站回退和 retry 行为。
- 实现说明：文档只描述用户可感知行为，不承诺登录态或非公开题支持。
- 预期验证结果：相关测试和全量测试通过。
- 完成时间：2026-05-20
