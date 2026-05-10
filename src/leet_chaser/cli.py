"""Command line interface for Leet-Chaser."""

from pathlib import Path

import typer
from rich.console import Console

app = typer.Typer(help="Run LeetCode solutions against local test cases.")
console = Console()


@app.command()
def run(solution: Path, cases: Path) -> None:
    """Run a solution file against a TOML case file.

    Args:
        solution: Path to the Python solution file.
        cases: Path to the TOML file containing test cases.

    Returns:
        None.
    """
    console.print(f"Solution: {solution}")
    console.print(f"Cases: {cases}")


def main() -> None:
    """Start the Leet-Chaser command line application.

    Args:
        None.

    Returns:
        None.
    """
    app()
