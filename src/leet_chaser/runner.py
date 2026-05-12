"""Run LeetCode-style Python solutions against local test cases."""

from dataclasses import dataclass
from importlib import util
from pathlib import Path
from types import ModuleType
from typing import Any

from leet_chaser.case_file import Case, CaseFile, read_case_file
from leet_chaser.linked_types import LINKED_TYPE_NAMES, normalize_linked_value


class ProblemRunError(ValueError):
    """Raised when a problem workspace cannot be executed."""


@dataclass(frozen=True)
class PassedCaseResult:
    """A test case that returned the expected value.

    Attributes:
        index: One-based case index from the case file.
        input: Positional arguments passed to the solution method.
        expected: Expected value configured in ``cases.toml``.
        actual: Actual value returned by the solution method.
    """

    index: int
    input: list[Any]
    expected: Any
    actual: Any


@dataclass(frozen=True)
class FailedCaseResult:
    """A test case that returned an unexpected value.

    Attributes:
        index: One-based case index from the case file.
        input: Positional arguments passed to the solution method.
        expected: Expected value configured in ``cases.toml``.
        actual: Actual value returned by the solution method.
    """

    index: int
    input: list[Any]
    expected: Any
    actual: Any


@dataclass(frozen=True)
class ErrorCaseResult:
    """A test case that raised an exception while running.

    Attributes:
        index: One-based case index from the case file.
        input: Positional arguments passed to the solution method.
        expected: Expected value configured in ``cases.toml``.
        error_type: Exception class name raised by the case.
        error_message: String representation of the raised exception.
    """

    index: int
    input: list[Any]
    expected: Any
    error_type: str
    error_message: str


CaseResult = PassedCaseResult | FailedCaseResult | ErrorCaseResult


@dataclass(frozen=True)
class CaseWarning:
    """A non-fatal warning produced while running a case.

    Attributes:
        index: One-based case index from the case file.
        message: Human-readable warning message.
    """

    index: int
    message: str


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
        warnings: Non-fatal warnings emitted while executing cases.
    """

    solution_path: Path
    cases_path: Path
    entrypoint: str
    passed: list[PassedCaseResult]
    failed: list[FailedCaseResult]
    errors: list[ErrorCaseResult]
    warnings: list[CaseWarning]

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
    passed, failed, errors, warnings = run_cases(solution_class, method_name, case_file)
    return ProblemRunResult(
        solution_path=solution_path,
        cases_path=cases_path,
        entrypoint=case_file.entrypoint,
        passed=passed,
        failed=failed,
        errors=errors,
        warnings=warnings,
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
    case_file: CaseFile,
) -> tuple[list[PassedCaseResult], list[FailedCaseResult], list[ErrorCaseResult], list[CaseWarning]]:
    """Run all cases against fresh ``Solution`` instances.

    Args:
        solution_class: Class to instantiate once per case.
        entrypoint: Method name to call on each instance.
        case_file: Test cases and comparison metadata loaded from ``cases.toml``.

    Returns:
        Passed, failed, errored, and warning result lists.
    """
    passed: list[PassedCaseResult] = []
    failed: list[FailedCaseResult] = []
    errors: list[ErrorCaseResult] = []
    warnings: list[CaseWarning] = []

    for index, test_case in enumerate(case_file.cases, start=1):
        try:
            solution = solution_class()
            method = getattr(solution, entrypoint)
            returned_value = method(*test_case.input)
            actual, warning = select_actual_result(test_case, case_file, returned_value)
        except Exception as error:
            errors.append(
                ErrorCaseResult(
                    index=index,
                    input=test_case.input,
                    expected=test_case.output,
                    error_type=type(error).__name__,
                    error_message=str(error),
                )
            )
            continue

        if warning is not None:
            warnings.append(CaseWarning(index=index, message=warning))
        expected = normalize_case_value(test_case.output, test_case.output_type)
        actual_result = normalize_case_value(actual, test_case.output_type)

        if compare_case_values(actual_result, expected, case_file):
            passed.append(
                PassedCaseResult(
                    index=index,
                    input=test_case.input,
                    expected=expected,
                    actual=actual_result,
                )
            )
        else:
            failed.append(
                FailedCaseResult(
                    index=index,
                    input=test_case.input,
                    expected=expected,
                    actual=actual_result,
                )
            )

    return passed, failed, errors, warnings


def select_actual_result(test_case: Case, case_file: CaseFile, returned_value: Any) -> tuple[Any, str | None]:
    """Select the value used for case comparison.

    Args:
        test_case: Case whose inputs may have been mutated by the solution.
        case_file: Parsed case file containing inplace comparison metadata.
        returned_value: Value returned by the solution method.

    Returns:
        Actual comparison value and an optional warning message.
    """
    if not case_file.inplace_write:
        return returned_value, None

    inplace_index = case_file.inplace_index
    if inplace_index is None:
        return returned_value, None

    actual = test_case.input[inplace_index]
    if returned_value is None:
        return actual, None
    return actual, (
        "inplace_write is true, so the solution return value was ignored "
        f"and input[{inplace_index}] was compared"
    )


def normalize_case_value(value: Any, value_type: str) -> Any:
    """Normalize a case value before comparison and display.

    Args:
        value: Raw value returned by a solution or parsed from TOML.
        value_type: Type metadata attached to the case output.

    Returns:
        Comparable value for the selected type.
    """
    if value_type in LINKED_TYPE_NAMES:
        return normalize_linked_value(value, value_type)
    return value


def compare_case_values(actual: Any, expected: Any, case_file: CaseFile) -> bool:
    """Compare normalized actual and expected values for one case.

    Args:
        actual: Normalized value returned by the solution.
        expected: Normalized value configured in ``cases.toml``.
        case_file: Case file metadata that selects comparison behavior.

    Returns:
        True when the values match under the selected comparison mode.
    """
    if not case_file.unordered_output:
        return actual == expected
    return unordered_case_key(actual) == unordered_case_key(expected)


def unordered_case_key(value: Any) -> Any:
    """Build a recursively order-insensitive comparison key.

    Args:
        value: Value to convert into a comparable key.

    Returns:
        A stable key where list element order does not affect equality.
    """
    if isinstance(value, list):
        unordered_items = (unordered_case_key(item) for item in value)
        return ("list", tuple(sorted(unordered_items, key=repr)))
    if isinstance(value, dict):
        return (
            "dict",
            tuple(
                sorted(
                    (
                        (unordered_case_key(key), unordered_case_key(item))
                        for key, item in value.items()
                    ),
                    key=repr,
                )
            ),
        )
    return ("value", value)
