"""Command line interface for Leet-Chaser."""

from pathlib import Path

import typer
from rich.console import Console

from leet_chaser.case_file import CaseFileError, read_case_file

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
    try:
        test_cases = read_case_file(cases)
    except CaseFileError as error:
        raise typer.BadParameter(str(error), param_hint="cases") from error

    console.print(f"Solution: {solution}")
    console.print(f"Cases: {cases}")
    console.print(f"Loaded {len(test_cases)} test case(s).")


def main() -> None:
    """Start the Leet-Chaser command line application.

    Args:
        None.

    Returns:
        None.
    """
    app()
