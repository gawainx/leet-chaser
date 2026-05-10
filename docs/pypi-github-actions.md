# PyPI GitHub Actions 发布配置

## 需求内容

将 Leet-Chaser 的 PyPI 发布流程接入 GitHub Actions。日常提交和 Pull Request 运行测试与构建；推送版本标签时自动构建发行包，并通过 PyPI Trusted Publishing 发布到 `https://pypi.org/project/leet-chaser/`。

## 设计

项目使用两个 workflow：

- `.github/workflows/ci.yml`：在 `master` 分支 push 和 Pull Request 时运行 `uv run pytest` 与 `uv build`。
- `.github/workflows/publish.yml`：在推送 `v*` 标签时运行测试、校验标签版本、构建发行包，并使用 PyPI Trusted Publishing 发布到 PyPI。

发布流程不保存 PyPI API token。`publish` job 只授予 `id-token: write` 权限，由 GitHub Actions OIDC 和 PyPI Trusted Publisher 交换短期发布凭据。

## 实现方法

### GitHub 配置

在 GitHub 仓库中创建发布环境：

1. 打开 `https://github.com/gawainx/leet-chaser/settings/environments`。
2. 点击 `New environment`。
3. 环境名填写 `pypi`。
4. 推荐开启 `Required reviewers`，让正式发布需要人工确认。

### PyPI 配置

在 PyPI 项目中添加 GitHub Actions Trusted Publisher：

1. 打开 `https://pypi.org/manage/project/leet-chaser/settings/publishing/`。
2. 找到 `Add a new pending publisher` 或 GitHub Actions publisher 配置入口。
3. 按下面内容填写：

```text
Owner: gawainx
Repository name: leet-chaser
Workflow name: publish.yml
Environment name: pypi
```

### 发布步骤

发布新版本前，先更新 `pyproject.toml` 里的版本号，例如：

```toml
version = "0.1.1"
```

提交版本变更后，推送分支和标签：

```shell
git tag v0.1.1
git push origin master
git push origin v0.1.1
```

`publish.yml` 会校验 tag 与 `pyproject.toml` 版本一致。比如 `version = "0.1.1"` 时，只允许 `v0.1.1` 标签发布。

### 验证方式

- 日常验证：GitHub Actions 的 `CI` workflow 通过。
- 发布验证：GitHub Actions 的 `Publish Python package` workflow 通过。
- PyPI 验证：打开 `https://pypi.org/project/leet-chaser/`，确认新版本已出现。
