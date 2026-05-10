"""Command line interface for Leet-Chaser."""

import re
from pathlib import Path

import typer
from rich.console import Console

from leet_chaser.case_file import CaseFileError
from leet_chaser.runner import ProblemRunError, run_problem

app = typer.Typer(help="Run LeetCode solutions against local test cases.")
console = Console()

CASE_TEMPLATE = """entrypoint = "twoSum"

[[cases]]
input = [[2, 7, 11, 15], 9]
output = [0, 1]

[[cases]]
input = [["flower", "flow", "flight"]]
output = "fl"
"""

SOLUTION_TEMPLATE = ""


def normalize_project_name(name: str) -> str:
    """Normalize a project name into a dash-separated directory name.

    Args:
        name: Raw project name received from the command line.

    Returns:
        A directory-safe name with special symbol runs replaced by dashes.
    """
    normalized_name = re.sub(r"[^0-9A-Za-z]+", "-", name).strip("-")
    if not normalized_name:
        raise typer.BadParameter(
            "name must contain at least one letter or number",
            param_hint="name",
        )
    return normalized_name


@app.command()
def init(name: str) -> None:
    """Create a solution workspace in the current directory.

    Args:
        name: Name of the child directory to create.

    Returns:
        None.
    """
    project_name = normalize_project_name(name)
    project_dir = Path.cwd() / project_name
    try:
        project_dir.mkdir()
    except FileExistsError as error:
        raise typer.BadParameter(
            f"directory already exists: {project_dir}",
            param_hint="name",
        ) from error

    (project_dir / "solution.py").write_text(SOLUTION_TEMPLATE, encoding="utf-8")
    (project_dir / "cases.toml").write_text(CASE_TEMPLATE, encoding="utf-8")

    console.print(f"Created [bold green]{project_name}[/bold green]")


@app.command()
def run(problem_dir: Path) -> None:
    """Run a problem directory against its TOML case file.

    Args:
        problem_dir: Directory containing ``solution.py`` and ``cases.toml``.

    Returns:
        None.
    """
    try:
        result = run_problem(problem_dir)
    except CaseFileError as error:
        raise typer.BadParameter(str(error), param_hint="problem_dir") from error
    except ProblemRunError as error:
        raise typer.BadParameter(str(error), param_hint="problem_dir") from error

    console.print(f"Solution: {result.solution_path}")
    console.print(f"Cases: {result.cases_path}")
    console.print(f"Entrypoint: {result.entrypoint}")

    for test_case in result.passed:
        console.print(f"[green]PASS[/green] case {test_case.index}")
    for test_case in result.failed:
        console.print(
            f"[red]FAIL[/red] case {test_case.index}: "
            f"expected={test_case.expected!r}, actual={test_case.actual!r}"
        )
    for test_case in result.errors:
        console.print(
            f"[red]ERROR[/red] case {test_case.index}: "
            f"expected={test_case.expected!r}, "
            f"{test_case.error_type}: {test_case.error_message}"
        )

    console.print(
        f"Summary: {len(result.passed)}/{result.total_count} passed, "
        f"{len(result.failed)} failed, {len(result.errors)} error(s)."
    )
    if result.has_failures:
        raise typer.Exit(code=1)


def main() -> None:
    """Start the Leet-Chaser command line application.

    Args:
        None.

    Returns:
        None.
    """
    app()
