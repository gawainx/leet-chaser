"""Smoke tests for the package bootstrap."""

from leet_chaser import __version__
from leet_chaser.cli import app


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
