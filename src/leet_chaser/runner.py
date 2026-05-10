"""Run LeetCode-style Python solutions against local test cases."""

from dataclasses import dataclass
from importlib import util
from pathlib import Path
from types import ModuleType
from typing import Any

from leet_chaser.case_file import Case, read_case_file


class ProblemRunError(ValueError):
    """Raised when a problem workspace cannot be executed."""


@dataclass(frozen=True)
class PassedCaseResult:
    """A test case that returned the expected value.

    Attributes:
        index: One-based case index from the case file.
        expected: Expected value configured in ``cases.toml``.
        actual: Actual value returned by the solution method.
    """

    index: int
    expected: Any
    actual: Any


@dataclass(frozen=True)
class FailedCaseResult:
    """A test case that returned an unexpected value.

    Attributes:
        index: One-based case index from the case file.
        expected: Expected value configured in ``cases.toml``.
        actual: Actual value returned by the solution method.
    """

    index: int
    expected: Any
    actual: Any


@dataclass(frozen=True)
class ErrorCaseResult:
    """A test case that raised an exception while running.

    Attributes:
        index: One-based case index from the case file.
        expected: Expected value configured in ``cases.toml``.
        error_type: Exception class name raised by the case.
        error_message: String representation of the raised exception.
    """

    index: int
    expected: Any
    error_type: str
    error_message: str


CaseResult = PassedCaseResult | FailedCaseResult | ErrorCaseResult


@dataclass(frozen=True)
class ProblemRunResult:
    """Result summary for one problem directory run.

    Attributes:
        solution_path: Path to the executed ``solution.py`` file.
        cases_path: Path to the parsed ``cases.toml`` file.
        entrypoint: Solution method name configured by the case file.
        passed: Cases that returned the expected value.
        failed: Cases that returned a different value.
        errors: Cases that raised exceptions while executing.
    """

    solution_path: Path
    cases_path: Path
    entrypoint: str
    passed: list[PassedCaseResult]
    failed: list[FailedCaseResult]
    errors: list[ErrorCaseResult]

    @property
    def total_count(self) -> int:
        """Return the total number of executed cases.

        Args:
            None.

        Returns:
            Count of passed, failed, and errored cases.
        """
        return len(self.passed) + len(self.failed) + len(self.errors)

    @property
    def has_failures(self) -> bool:
        """Return whether any case failed or errored.

        Args:
            None.

        Returns:
            True when at least one case did not pass.
        """
        return bool(self.failed or self.errors)


def run_problem(problem_dir: Path) -> ProblemRunResult:
    """Run every case in a LeetCode-style problem directory.

    Args:
        problem_dir: Directory containing ``solution.py`` and ``cases.toml``.

    Returns:
        Structured result summary for all executed cases.

    Raises:
        ProblemRunError: If the workspace or solution shape is invalid.
    """
    solution_path = problem_dir / "solution.py"
    cases_path = problem_dir / "cases.toml"
    if not problem_dir.is_dir():
        raise ProblemRunError(f"problem directory does not exist: {problem_dir}")
    if not solution_path.is_file():
        raise ProblemRunError(f"solution file does not exist: {solution_path}")
    if not cases_path.is_file():
        raise ProblemRunError(f"case file does not exist: {cases_path}")

    case_file = read_case_file(cases_path)
    module = load_solution_module(solution_path)
    solution_class, method_name = resolve_solution_method(module, case_file.entrypoint)
    passed, failed, errors = run_cases(solution_class, method_name, case_file.cases)
    return ProblemRunResult(
        solution_path=solution_path,
        cases_path=cases_path,
        entrypoint=case_file.entrypoint,
        passed=passed,
        failed=failed,
        errors=errors,
    )


def load_solution_module(solution_path: Path) -> ModuleType:
    """Load a Python solution file as a module.

    Args:
        solution_path: Path to a Python file containing a ``Solution`` class.

    Returns:
        Loaded Python module object.

    Raises:
        ProblemRunError: If the module cannot be imported.
    """
    spec = util.spec_from_file_location("leet_chaser_user_solution", solution_path)
    if spec is None or spec.loader is None:
        raise ProblemRunError(f"cannot load solution file: {solution_path}")

    module = util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as error:
        raise ProblemRunError(f"failed to import solution.py: {type(error).__name__}: {error}") from error
    return module


def resolve_solution_method(module: ModuleType, entrypoint: str) -> tuple[type[Any], str]:
    """Resolve the configured entrypoint on the module's ``Solution`` class.

    Args:
        module: Loaded solution module.
        entrypoint: Method name configured in the case file.

    Returns:
        The ``Solution`` class and validated method name.

    Raises:
        ProblemRunError: If ``Solution`` or the entrypoint method is missing.
    """
    solution_class = getattr(module, "Solution", None)
    if not isinstance(solution_class, type):
        raise ProblemRunError("solution.py must define a Solution class")

    method = getattr(solution_class, entrypoint, None)
    if method is None or not callable(method):
        raise ProblemRunError(f"Solution must define callable entrypoint: {entrypoint}")

    return solution_class, entrypoint


def run_cases(
    solution_class: type[Any],
    entrypoint: str,
    cases: list[Case],
) -> tuple[list[PassedCaseResult], list[FailedCaseResult], list[ErrorCaseResult]]:
    """Run all cases against fresh ``Solution`` instances.

    Args:
        solution_class: Class to instantiate once per case.
        entrypoint: Method name to call on each instance.
        cases: Test cases loaded from ``cases.toml``.

    Returns:
        Passed, failed, and errored case result lists.
    """
    passed: list[PassedCaseResult] = []
    failed: list[FailedCaseResult] = []
    errors: list[ErrorCaseResult] = []

    for index, test_case in enumerate(cases, start=1):
        try:
            solution = solution_class()
            method = getattr(solution, entrypoint)
            actual = method(*test_case.input)
        except Exception as error:
            errors.append(
                ErrorCaseResult(
                    index=index,
                    expected=test_case.output,
                    error_type=type(error).__name__,
                    error_message=str(error),
                )
            )
            continue

        if actual == test_case.output:
            passed.append(PassedCaseResult(index=index, expected=test_case.output, actual=actual))
        else:
            failed.append(FailedCaseResult(index=index, expected=test_case.output, actual=actual))

    return passed, failed, errors
