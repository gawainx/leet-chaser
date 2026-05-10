"""Smoke tests for the package bootstrap."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from leet_chaser import __version__
from leet_chaser.case_file import Case, read_case_file
from leet_chaser.cli import app

runner = CliRunner()


def test_version_is_defined() -> None:
    """Verify the package exposes a version string.

    Args:
        None.

    Returns:
        None.
    """
    assert __version__ == "0.1.0"


def test_cli_app_is_available() -> None:
    """Verify the Typer application can be imported.

    Args:
        None.

    Returns:
        None.
    """
    assert app.info.help == "Run LeetCode solutions against local test cases."


def test_init_creates_solution_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify init creates editable solution and case files.

    Args:
        tmp_path: Temporary directory provided by pytest.
        monkeypatch: Pytest helper used to run the command from tmp_path.

    Returns:
        None.
    """
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["init", "two-sum"], catch_exceptions=False, env={})

    project_dir = tmp_path / "two-sum"
    assert result.exit_code == 0
    assert (project_dir / "solution.py").read_text(encoding="utf-8") == ""
    assert read_case_file(project_dir / "cases.toml") == [
        Case(input=[[2, 7, 11, 15], 9], output=[0, 1]),
        Case(input=[["flower", "flow", "flight"]], output="fl"),
    ]


def test_init_rejects_existing_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify init does not overwrite an existing solution workspace.

    Args:
        tmp_path: Temporary directory provided by pytest.
        monkeypatch: Pytest helper used to run the command from tmp_path.

    Returns:
        None.
    """
    project_dir = tmp_path / "two-sum"
    project_dir.mkdir()
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["init", "two-sum"], env={})

    assert result.exit_code != 0
    assert "directory already exists" in result.output
