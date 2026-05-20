# LeetCode CN Init 兼容修复

## 需求内容

用户执行 `leet-chaser init --question-number/-q <number>` 时，希望题号初始化优先访问 `leetcode.cn`，避免在网络正常但访问 `leetcode.com` 不稳定时频繁出现 request timeout。

本次修复目标是保持原有公开题目初始化能力不变：继续按题号生成 Python3 `solution.py`、从题面示例生成 `cases.toml`，并保留付费题、题号不存在、缺少 Python3 snippet、样例无法解析等错误提示。

## 设计

远程拉取顺序改为优先 `leetcode.cn`，失败后回退 `leetcode.com`。这样中国网络下的默认路径更稳定，同时保留原先国际站路径作为兼容兜底。

中国站题号查 slug 使用 `problemsetQuestionListV2`，通过 `limit = 1` 和 `skip = question_number - 1` 取候选题目，再校验 `questionFrontendId` 必须等于用户输入题号。这样不依赖中国站搜索过滤字段，避免 schema 差异导致查询失败。

题目详情继续使用 `question(titleSlug:)`，并读取英文 `content`、`metaData` 和 Python3 `codeSnippets`。使用英文 `content` 是为了复用现有示例解析逻辑，避免中文“输入/输出”标签带来额外解析分支。

GraphQL 请求增加短重试。只对 timeout 和 URL reachability 类错误重试；HTTP 400、GraphQL schema error、非法 JSON 等确定性错误不重试，直接进入回退或报错。

## 实现方法

`leet_chaser.leetcode_client` 中新增：

- `LeetCodeGraphQLEndpoint`：描述 endpoint 名称、URL 和 referer。
- `LEETCODE_CN_ENDPOINT`：`https://leetcode.cn/graphql`。
- `LEETCODE_GLOBAL_ENDPOINT`：`https://leetcode.com/graphql`。
- `fetch_title_slug_from_cn(question_number)`：使用中国站 `problemsetQuestionListV2` 查询题号。
- `fetch_title_slug_from_global(question_number)`：保留原国际站 `questionList` 查询。
- `fetch_question_data_from_endpoint(title_slug, endpoint)`：按 endpoint 拉取题目详情。
- `post_graphql_once(...)`：执行单次 GraphQL 请求。
- `is_retryable_client_error(error)`：判断是否需要 retry。

既有 `fetch_title_slug(question_number)` 现在先调用中国站实现，失败后调用国际站实现。既有 `fetch_question_data(title_slug)` 同样先用中国站详情接口，失败后回退国际站详情接口。

测试补充：

- 中国站 `problemsetQuestionListV2` 字段解析。
- 中国站题号查询失败后回退国际站。
- 中国站详情查询失败后回退国际站。
- timeout 前两次失败、第三次成功的 retry 路径。

验证命令：

- `uv run pytest tests/test_package.py -q`
- `uv run pytest -q`
- `uv run --project /Users/yat/code/leet-chaser leet-chaser init --question-number 1`
