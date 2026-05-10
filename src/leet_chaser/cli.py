"""Command line interface for Leet-Chaser."""

from pathlib import Path

import typer
from rich.console import Console

from leet_chaser.case_file import CaseFileError, read_case_file

app = typer.Typer(help="Run LeetCode solutions against local test cases.")
console = Console()

CASE_TEMPLATE = """[[cases]]
input = [[2, 7, 11, 15], 9]
output = [0, 1]

[[cases]]
input = [["flower", "flow", "flight"]]
output = "fl"
"""

SOLUTION_TEMPLATE = ""


@app.command()
def init(name: str) -> None:
    """Create a solution workspace in the current directory.

    Args:
        name: Name of the child directory to create.

    Returns:
        None.
    """
    project_dir = Path.cwd() / name
    try:
        project_dir.mkdir()
    except FileExistsError as error:
        raise typer.BadParameter(
            f"directory already exists: {project_dir}",
            param_hint="name",
        ) from error

    (project_dir / "solution.py").write_text(SOLUTION_TEMPLATE, encoding="utf-8")
    (project_dir / "cases.toml").write_text(CASE_TEMPLATE, encoding="utf-8")

    console.print(f"Created {project_dir}")


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
