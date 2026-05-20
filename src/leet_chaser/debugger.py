"""Debug LeetCode-style Python solutions against one local test case."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import snoop

from leet_chaser.case_file import read_case_file
from leet_chaser.runner import (
    CaseWarning,
    ProblemRunError,
    load_solution_module,
    normalize_case_value,
    resolve_solution_method,
    resolve_entry_file,
    select_actual_result,
)


class ProblemDebugError(ValueError):
    """Raised when a problem workspace cannot be debugged."""


@dataclass(frozen=True)
class ProblemDebugResult:
    """Result summary for one debug case execution.

    Attributes:
        solution_path: Path to the executed ``solution.py`` file.
        case_path: Path to the parsed debug TOML file.
        entrypoint: Solution method name configured by the debug case file.
        input: Positional arguments passed to the solution method.
        expected: Expected value configured in the debug case file.
        actual: Actual value returned by the solution method.
        output_type: Expected parsing type for output comparison.
        traces: Watched snoop expressions requested by the user.
        warnings: Non-fatal warnings emitted while executing the case.
    """

    solution_path: Path
    case_path: Path
    entrypoint: str
    input: list[Any]
    expected: Any
    actual: Any
    output_type: str
    traces: tuple[str, ...]
    warnings: list[CaseWarning]

    @property
    def passed(self) -> bool:
        """Return whether the debugged case matched the expected output.

        Args:
            None.

        Returns:
            True when the actual value equals the expected value.
        """
        return normalize_case_value(self.actual, self.output_type) == normalize_case_value(
            self.expected,
            self.output_type,
        )


def debug_problem(
    problem_dir: Path,
    case_path: Path | None = None,
    traces: tuple[str, ...] = (),
    entry_file: Path = Path("solution.py"),
) -> ProblemDebugResult:
    """Run one debug TOML case with line tracing enabled on the entrypoint.

    Args:
        problem_dir: Directory containing ``solution.py``.
        case_path: TOML file containing exactly one debug case.
        traces: Additional expressions or variable names to watch with snoop.
        entry_file: Python entry file to load, relative to ``problem_dir`` unless absolute.

    Returns:
        Structured result summary for the debugged case.

    Raises:
        ProblemRunError: If the workspace or solution shape is invalid.
        ProblemDebugError: If the debug case file is missing or has multiple cases.
    """
    solution_path = resolve_entry_file(problem_dir, entry_file)
    resolved_case_path = case_path or problem_dir / "debug.toml"

    if not problem_dir.is_dir():
        raise ProblemRunError(f"problem directory does not exist: {problem_dir}")
    if not solution_path.is_file():
        raise ProblemRunError(f"solution file does not exist: {solution_path}")
    if not resolved_case_path.is_file():
        raise ProblemDebugError(f"debug case file does not exist: {resolved_case_path}")

    case_file = read_case_file(resolved_case_path)
    if len(case_file.cases) != 1:
        raise ProblemDebugError("debug case file must contain exactly one [[cases]] entry")

    module = load_solution_module(solution_path)
    solution_class, method_name = resolve_solution_method(module, case_file.entrypoint)
    test_case = case_file.cases[0]
    solution = solution_class()
    method = getattr(solution, method_name)
    traced_method = snoop.snoop(watch=traces)(method)
    returned_value = traced_method(*test_case.input)
    actual, warning = select_actual_result(test_case, case_file, returned_value)
    warnings = [CaseWarning(index=1, message=warning)] if warning is not None else []

    return ProblemDebugResult(
        solution_path=solution_path,
        case_path=resolved_case_path,
        entrypoint=case_file.entrypoint,
        input=test_case.input,
        expected=test_case.output,
        actual=actual,
        output_type=test_case.output_type,
        traces=traces,
        warnings=warnings,
    )
