"""Smoke tests for the package bootstrap."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from leet_chaser import __version__
from leet_chaser.case_file import Case, CaseFile, read_case_file
from leet_chaser.cli import app, normalize_project_name

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
    assert read_case_file(project_dir / "cases.toml") == CaseFile(
        entrypoint="twoSum",
        cases=[
            Case(input=[[2, 7, 11, 15], 9], output=[0, 1]),
            Case(input=[["flower", "flow", "flight"]], output="fl"),
        ],
    )
    assert "Created two-sum" in result.output


def test_normalize_project_name_replaces_special_symbols() -> None:
    """Verify special symbols become single dash separators.

    Args:
        None.

    Returns:
        None.
    """
    assert normalize_project_name("Two Sum!! 001") == "Two-Sum-001"


def test_init_uses_normalized_directory_name(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify init creates the normalized directory name.

    Args:
        tmp_path: Temporary directory provided by pytest.
        monkeypatch: Pytest helper used to run the command from tmp_path.

    Returns:
        None.
    """
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["init", "Two Sum!! 001"], catch_exceptions=False, env={})

    assert result.exit_code == 0
    assert (tmp_path / "Two-Sum-001").is_dir()
    assert "Created Two-Sum-001" in result.output


def test_init_rejects_names_without_letters_or_numbers(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify init rejects names that normalize to an empty value.

    Args:
        tmp_path: Temporary directory provided by pytest.
        monkeypatch: Pytest helper used to run the command from tmp_path.

    Returns:
        None.
    """
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["init", "!!!"], env={})

    assert result.exit_code != 0
    assert "name must contain at least one letter or number" in result.output


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
