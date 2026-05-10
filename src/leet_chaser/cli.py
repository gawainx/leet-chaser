"""Command line interface for Leet-Chaser."""

import re
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from leet_chaser.case_file import CaseFileError
from leet_chaser.debugger import ProblemDebugError, ProblemDebugResult, debug_problem
from leet_chaser.runner import ProblemRunError, ProblemRunResult, run_problem

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
    if result.has_failures:
        console.print(build_failure_table(result))

    console.print(
        f"Summary: {len(result.passed)}/{result.total_count} passed, "
        f"{len(result.failed)} failed, {len(result.errors)} error(s)."
    )
    if result.has_failures:
        raise typer.Exit(code=1)


@app.command()
def debug(
    problem_dir: Path,
    case_path: Path | None = typer.Option(
        None,
        "--case",
        "-c",
        help="Single-case TOML file. Defaults to <problem-dir>/debug.toml.",
    ),
    traces: list[str] | None = typer.Option(
        None,
        "--trace",
        "-t",
        help="Variable name or expression to watch. Can be passed multiple times.",
    ),
) -> None:
    """Debug one problem case with line tracing enabled on the entrypoint.

    Args:
        problem_dir: Directory containing ``solution.py``.
        case_path: TOML file containing exactly one debug case.
        traces: Variable names or expressions to watch with snoop.

    Returns:
        None.
    """
    try:
        result = debug_problem(problem_dir, case_path=case_path, traces=tuple(traces or ()))
    except CaseFileError as error:
        raise typer.BadParameter(str(error), param_hint="case") from error
    except ProblemDebugError as error:
        raise typer.BadParameter(str(error), param_hint="case") from error
    except ProblemRunError as error:
        raise typer.BadParameter(str(error), param_hint="problem_dir") from error

    console.print(build_debug_summary(result))
    if not result.passed:
        raise typer.Exit(code=1)


def build_debug_summary(result: ProblemDebugResult) -> str:
    """Build a compact summary for one debug result.

    Args:
        result: Structured debug result for one case.

    Returns:
        Human-readable summary string.
    """
    status = "[green]PASS[/green]" if result.passed else "[red]FAIL[/red]"
    trace_text = ", ".join(result.traces) if result.traces else "all local changes"
    return (
        f"Solution: {result.solution_path}\n"
        f"Case: {result.case_path}\n"
        f"Entrypoint: {result.entrypoint}\n"
        f"Trace: {trace_text}\n"
        f"{status} actual={format_value(result.actual)} expected={format_value(result.expected)}"
    )


def build_failure_table(result: ProblemRunResult) -> Table:
    """Build a table for failed and errored cases.

    Args:
        result: Structured run result containing failed or errored cases.

    Returns:
        Rich table with case index, input, expected output, and actual output.
    """
    table = Table(title="Failed Cases")
    table.add_column("Case", justify="right")
    table.add_column("Input")
    table.add_column("Expected")
    table.add_column("Actual")

    for test_case in result.failed:
        table.add_row(
            str(test_case.index),
            format_value(test_case.input),
            format_value(test_case.expected),
            format_value(test_case.actual),
        )
    for test_case in result.errors:
        table.add_row(
            str(test_case.index),
            format_value(test_case.input),
            format_value(test_case.expected),
            f"{test_case.error_type}: {test_case.error_message}",
        )
    return table


def format_value(value: Any) -> str:
    """Format a Python value for CLI table output.

    Args:
        value: Value to display in the run output.

    Returns:
        Repr-formatted value.
    """
    return repr(value)


def main() -> None:
    """Start the Leet-Chaser command line application.

    Args:
        None.

    Returns:
        None.
    """
    app()
