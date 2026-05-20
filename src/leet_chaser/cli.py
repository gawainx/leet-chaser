"""Command line interface for Leet-Chaser."""

import re
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from leet_chaser.case_templates import NORMAL_CASE_CONFIG_COMMENTS
from leet_chaser.case_file import CaseFileError
from leet_chaser.debugger import ProblemDebugError, ProblemDebugResult, debug_problem
from leet_chaser.leetcode_client import (
    LeetCodeClientError,
    build_remote_init_files,
    fetch_question_metadata,
)
from leet_chaser.runner import ErrorCaseResult, ProblemRunError, ProblemRunResult, run_problem

app = typer.Typer(help="Run LeetCode solutions against local test cases.")
console = Console()

CASE_TEMPLATE_BY_TYPE = {
    "raw": NORMAL_CASE_CONFIG_COMMENTS
    + """entrypoint = "twoSum"

[[cases]]
input = [[2, 7, 11, 15], 9]
output = [0, 1]

[[cases]]
input = [["flower", "flow", "flight"]]
output = "fl"
""",
    "linked_list": NORMAL_CASE_CONFIG_COMMENTS
    + """entrypoint = "reverseList"
input_types = ["linked_list"]
output_type = "linked_list"

[[cases]]
input = [[1, 2, 3, 4, 5]]
output = [5, 4, 3, 2, 1]

[[cases]]
input = [[]]
output = []
""",
    "binary_tree": NORMAL_CASE_CONFIG_COMMENTS
    + """entrypoint = "isValidBST"
input_types = ["binary_tree"]

[[cases]]
input = [[2, 1, 3]]
output = true

[[cases]]
input = [[5, 1, 4, "null", "null", 3, 6]]
output = false

[[cases]]
input = [[]]
output = true
""",
    "matrix": NORMAL_CASE_CONFIG_COMMENTS
    + """entrypoint = "searchMatrix"

[[cases]]
input = [[[1, 3, 5, 7], [10, 11, 16, 20], [23, 30, 34, 60]], 3]
output = true

[[cases]]
input = [[[1, 3, 5, 7], [10, 11, 16, 20], [23, 30, 34, 60]], 13]
output = false
""",
}
CASE_TYPE_ALIASES = {
    "array": "raw",
    "default": "raw",
    "raw": "raw",
    "linked": "linked_list",
    "linkedlist": "linked_list",
    "linkednode": "linked_list",
    "linklist": "linked_list",
    "list": "linked_list",
    "listnode": "linked_list",
    "binarytree": "binary_tree",
    "binarytreenode": "binary_tree",
    "bitree": "binary_tree",
    "tree": "binary_tree",
    "treenode": "binary_tree",
    "2darray": "matrix",
    "grid": "matrix",
    "matrix": "matrix",
    "twodarray": "matrix",
    "twodimensionalarray": "matrix",
}

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


def resolve_init_case_type(raw_case_type: str | None) -> str:
    """Resolve an init template type from a fuzzy command-line value.

    Args:
        raw_case_type: Optional user-provided type name from ``-t/--type``.

    Returns:
        Internal case template type name.

    Raises:
        typer.BadParameter: If the type name cannot be resolved.
    """
    if raw_case_type is None:
        return "raw"

    normalized_type = re.sub(r"[^0-9A-Za-z]+", "", raw_case_type).lower()
    case_type = CASE_TYPE_ALIASES.get(normalized_type)
    if case_type is None:
        raise typer.BadParameter(
            "type must be one of: linklist, linked_list, bitree, binary_tree, tree, matrix",
            param_hint="type",
        )
    return case_type


@app.command()
def init(
    name: str | None = typer.Argument(
        None,
        help="Name of the child directory to create. Optional when --question-number is used.",
    ),
    case_type: str | None = typer.Option(
        None,
        "--type",
        "-t",
        help="Case template type. Supports fuzzy values like linklist, bitree, tree, or matrix.",
    ),
    question_number: int | None = typer.Option(
        None,
        "--question-number",
        "-q",
        min=1,
        help="Public LeetCode question number used to fetch a Python3 template and examples.",
    ),
) -> None:
    """Create a solution workspace in the current directory.

    Args:
        name: Optional name of the child directory to create.
        case_type: Optional fuzzy case template type for advanced input metadata.
        question_number: Optional public LeetCode question number for remote templates.

    Returns:
        None.
    """
    if question_number is not None and case_type is not None:
        raise typer.BadParameter(
            "type cannot be used with question-number",
            param_hint="type",
        )
    if question_number is None and name is None:
        raise typer.BadParameter(
            "name is required unless question-number is provided",
            param_hint="name",
        )

    if question_number is not None:
        try:
            console.print(f"Fetching LeetCode question {question_number}...")
            metadata = fetch_question_metadata(question_number)
            console.print(
                f"Fetched question {question_number}: {metadata.title} "
                f"({metadata.title_slug})"
            )
            console.print(f"Generating local files for {metadata.entrypoint}...")
            init_files = build_remote_init_files(metadata)
        except LeetCodeClientError as error:
            raise typer.BadParameter(str(error), param_hint="question-number") from error
        project_name = normalize_project_name(name) if name is not None else init_files.directory_name
        solution_text = init_files.solution_text
        case_text = init_files.case_text
    else:
        project_name = normalize_project_name(name or "")
        resolved_case_type = resolve_init_case_type(case_type)
        solution_text = SOLUTION_TEMPLATE
        case_text = CASE_TEMPLATE_BY_TYPE[resolved_case_type]

    project_dir = Path.cwd() / project_name
    try:
        project_dir.mkdir()
    except FileExistsError as error:
        raise typer.BadParameter(
            f"directory already exists: {project_dir}",
            param_hint="name",
        ) from error

    (project_dir / "solution.py").write_text(solution_text, encoding="utf-8")
    (project_dir / "cases.toml").write_text(case_text, encoding="utf-8")

    if question_number is not None:
        console.print("Wrote solution.py and cases.toml")
    console.print(f"Created [bold green]{project_name}[/bold green]")


@app.command()
def run(
    problem_dir: Path,
    entry_file: Path = typer.Option(
        Path("solution.py"),
        "--entry",
        "-e",
        help="Python entry file. Defaults to <problem-dir>/solution.py.",
    ),
) -> None:
    """Run a problem directory against its TOML case file.

    Args:
        problem_dir: Directory containing ``solution.py`` and ``cases.toml``.
        entry_file: Python entry file to load.

    Returns:
        None.
    """
    try:
        result = run_problem(problem_dir, entry_file=entry_file)
    except CaseFileError as error:
        raise typer.BadParameter(str(error), param_hint="problem_dir") from error
    except ProblemRunError as error:
        raise typer.BadParameter(str(error), param_hint="problem_dir") from error

    console.print(f"Solution: {result.solution_path}")
    console.print(f"Cases: {result.cases_path}")
    if result.entrypoint:
        console.print(f"Entrypoint: {result.entrypoint}")
    else:
        console.print("Mode: operations")

    print_warnings(result.warnings)
    for test_case in result.passed:
        console.print(f"[green]PASS[/green] case {test_case.index}")
    if result.failed:
        console.print(build_failure_table(result))
    print_error_tracebacks(result.errors)

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
    entry_file: Path = typer.Option(
        Path("solution.py"),
        "--entry",
        "-e",
        help="Python entry file. Defaults to <problem-dir>/solution.py.",
    ),
) -> None:
    """Debug one problem case with line tracing enabled on the entrypoint.

    Args:
        problem_dir: Directory containing ``solution.py``.
        case_path: TOML file containing exactly one debug case.
        traces: Variable names or expressions to watch with snoop.
        entry_file: Python entry file to load.

    Returns:
        None.
    """
    try:
        result = debug_problem(problem_dir, case_path=case_path, traces=tuple(traces or ()), entry_file=entry_file)
    except CaseFileError as error:
        raise typer.BadParameter(str(error), param_hint="case") from error
    except ProblemDebugError as error:
        raise typer.BadParameter(str(error), param_hint="case") from error
    except ProblemRunError as error:
        raise typer.BadParameter(str(error), param_hint="problem_dir") from error

    print_warnings(result.warnings)
    console.print(build_debug_summary(result))
    if not result.passed:
        raise typer.Exit(code=1)


def print_warnings(warnings: list[Any]) -> None:
    """Print non-fatal case warnings with Rich styling.

    Args:
        warnings: Warning objects with ``index`` and ``message`` attributes.

    Returns:
        None.
    """
    for warning in warnings:
        console.print(f"[yellow]WARNING[/yellow] case {warning.index}: {warning.message}")


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
    """Build a table for failed cases.

    Args:
        result: Structured run result containing failed cases.

    Returns:
        Rich table with case index, input, expected output, and actual output.
    """
    table = Table(title="Failed Cases")
    table.add_column("Case", justify="right")
    table.add_column("Step", justify="right")
    table.add_column("Operation")
    table.add_column("Input")
    table.add_column("Expected")
    table.add_column("Actual")

    for test_case in result.failed:
        table.add_row(
            str(test_case.index),
            "" if test_case.step is None else str(test_case.step),
            test_case.operation or "",
            format_value(test_case.input),
            format_value(test_case.expected),
            format_value(test_case.actual),
        )
    return table


def print_error_tracebacks(errors: list[ErrorCaseResult]) -> None:
    """Print full tracebacks for errored cases grouped by case.

    Args:
        errors: Case execution errors collected by the runner.

    Returns:
        None.
    """
    for test_case in errors:
        step_text = (
            ""
            if test_case.step is None
            else f" step {test_case.step} {test_case.operation or ''}"
        )
        console.print(
            f"[red]ERROR[/red] case {test_case.index}{step_text}: "
            f"{test_case.error_type}: {test_case.error_message}"
        )
        console.print(f"Input: {format_value(test_case.input)}")
        console.print(f"Expected: {format_value(test_case.expected)}")
        console.print(test_case.traceback.rstrip())


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
