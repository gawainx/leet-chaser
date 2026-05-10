---
name: leet-chaser-release-publisher
description: Use when working in the Leet-Chaser repository and the user asks to "提交并发布版本", "提交并发布新版本", "发布版本", "发版", or "release version". Automates patch/minor/major version bumping, validation, release commit creation, lightweight git tagging, pushing master and the release tag, and then instructs the user to approve the GitHub Actions PyPI deployment.
---

# Leet-Chaser Release Publisher

## Scope

Use only for the Leet-Chaser repository. Do not rely on an absolute local path because the repository may live in different directories on different machines.

Before making release changes, verify repository identity with all of these checks:

```shell
git remote get-url origin
```

- The `origin` URL must point to `gawainx/leet-chaser` using either HTTPS or SSH.
- `pyproject.toml` must define `[project].name = "leet-chaser"`.
- `src/leet_chaser/__init__.py` must exist.
- `.github/workflows/publish.yml` must exist.

Stop if any identity check fails.

Default to a patch release unless the user explicitly says `minor`, `major`, or `patch`.

Do not update `docs/PROGRESS.md` for release-only work.

## Release Workflow

1. Inspect state:

```shell
git status --short --branch
git branch --show-current
```

Stop if the current branch is not `master`.

If the worktree has changes unrelated to version release files, show the changed paths and ask the user to confirm including them in the release commit.

2. Read versions:

- `pyproject.toml`: `[project].version`
- `src/leet_chaser/__init__.py`: `__version__`
- `tests/test_package.py`: expected `__version__`

Stop if these versions are inconsistent.

3. Compute the next version:

- patch: `MAJOR.MINOR.PATCH + 1`
- minor: `MAJOR.MINOR+1.0`
- major: `MAJOR+1.0.0`

Create the tag name as `vX.Y.Z`.

4. Update version references:

- `pyproject.toml`
- `src/leet_chaser/__init__.py`
- `tests/test_package.py`

5. Validate:

```shell
uv run pytest
uv build
```

If `twine` is available in the project environment, also run:

```shell
uv run twine check dist/*
```

Stop before commit/tag/push if validation fails.

6. Commit with a valid Conventional Commit message:

```shell
git add pyproject.toml src/leet_chaser/__init__.py tests/test_package.py
git commit -m "chore: release version X.Y.Z"
```

The commit message must satisfy the repository commit firewall: allowed type, at least 10 description characters, concrete version detail, and no amend.

7. Create a lightweight tag:

```shell
git tag vX.Y.Z
```

Stop if the tag already exists.

8. Push automatically:

```shell
git push origin master
git push origin vX.Y.Z
```

If the branch push succeeds but tag push fails, report the partial state and give the exact recovery command.

9. Tell the user to approve the deployment:

- Actions: `https://github.com/gawainx/leet-chaser/actions`
- PyPI: `https://pypi.org/project/leet-chaser/`

Explain that `Publish Python package` will wait for `pypi` environment approval, and the user should open the run, click `Review pending deployments`, then approve `pypi`.

## Success Response

Include:

- old version -> new version
- commit hash and message
- tag
- validation results
- push result
- GitHub approval reminder and links
