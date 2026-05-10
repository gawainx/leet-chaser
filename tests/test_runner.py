"""Tests for LeetCode-style solution execution."""

from pathlib import Path

import pytest

from leet_chaser.runner import FailedCaseResult, ProblemRunError, run_problem


def write_problem(problem_dir: Path, solution: str, cases: str) -> None:
    """Write a temporary problem workspace.

    Args:
        problem_dir: Directory that will receive solution and case files.
        solution: Python source written to ``solution.py``.
        cases: TOML source written to ``cases.toml``.

    Returns:
        None.
    """
    problem_dir.mkdir()
    (problem_dir / "solution.py").write_text(solution, encoding="utf-8")
    (problem_dir / "cases.toml").write_text(cases, encoding="utf-8")


def test_run_problem_reads_solution_and_cases_from_directory(tmp_path: Path) -> None:
    """Verify a problem directory is executed successfully.

    Args:
        tmp_path: Temporary directory provided by pytest.

    Returns:
        None.
    """
    problem_dir = tmp_path / "two-sum"
    write_problem(
        problem_dir,
        """
class Solution:
    def twoSum(self, nums, target):
        seen = {}
        for index, num in enumerate(nums):
            rest = target - num
            if rest in seen:
                return [seen[rest], index]
            seen[num] = index
        return []
""",
        """
entrypoint = "twoSum"

[[cases]]
input = [[2, 7, 11, 15], 9]
output = [0, 1]
""",
    )

    result = run_problem(problem_dir)

    assert result.total_count == 1
    assert not result.has_failures
    assert result.passed[0].actual == [0, 1]


def test_run_problem_creates_fresh_solution_instance_per_case(tmp_path: Path) -> None:
    """Verify instance variables do not leak between test cases.

    Args:
        tmp_path: Temporary directory provided by pytest.

    Returns:
        None.
    """
    problem_dir = tmp_path / "fresh-instance"
    write_problem(
        problem_dir,
        """
class Solution:
    def countCalls(self):
        if not hasattr(self, "calls"):
            self.calls = 0
        self.calls += 1
        return self.calls
""",
        """
entrypoint = "countCalls"

[[cases]]
input = []
output = 1

[[cases]]
input = []
output = 1
""",
    )

    result = run_problem(problem_dir)

    assert [case.actual for case in result.passed] == [1, 1]
    assert not result.has_failures


def test_run_problem_preserves_class_and_module_state_during_one_run(tmp_path: Path) -> None:
    """Verify class variables and module globals persist across cases.

    Args:
        tmp_path: Temporary directory provided by pytest.

    Returns:
        None.
    """
    problem_dir = tmp_path / "shared-state"
    write_problem(
        problem_dir,
        """
module_calls = 0


class Solution:
    class_calls = 0

    def countSharedState(self):
        global module_calls
        module_calls += 1
        Solution.class_calls += 1
        return [module_calls, Solution.class_calls]
""",
        """
entrypoint = "countSharedState"

[[cases]]
input = []
output = [1, 1]

[[cases]]
input = []
output = [2, 2]
""",
    )

    result = run_problem(problem_dir)

    assert [case.actual for case in result.passed] == [[1, 1], [2, 2]]
    assert not result.has_failures


def test_run_problem_collects_all_failures_and_errors(tmp_path: Path) -> None:
    """Verify failures and exceptions do not stop later cases.

    Args:
        tmp_path: Temporary directory provided by pytest.

    Returns:
        None.
    """
    problem_dir = tmp_path / "failures"
    write_problem(
        problem_dir,
        """
class Solution:
    def classify(self, value):
        if value == "boom":
            raise RuntimeError("broken case")
        return value
""",
        """
entrypoint = "classify"

[[cases]]
input = ["wrong"]
output = "expected"

[[cases]]
input = ["boom"]
output = "safe"

[[cases]]
input = ["ok"]
output = "ok"

[[cases]]
input = ["later-wrong"]
output = "later-expected"
""",
    )

    result = run_problem(problem_dir)

    assert result.passed[0].index == 3
    assert result.failed == [
        FailedCaseResult(index=1, expected="expected", actual="wrong"),
        FailedCaseResult(index=4, expected="later-expected", actual="later-wrong"),
    ]
    assert len(result.errors) == 1
    assert result.errors[0].index == 2
    assert result.errors[0].error_type == "RuntimeError"
    assert result.errors[0].error_message == "broken case"


def test_run_problem_requires_solution_class(tmp_path: Path) -> None:
    """Verify a missing Solution class is a run error.

    Args:
        tmp_path: Temporary directory provided by pytest.

    Returns:
        None.
    """
    problem_dir = tmp_path / "missing-solution"
    write_problem(
        problem_dir,
        """
def twoSum(nums, target):
    return []
""",
        """
entrypoint = "twoSum"

[[cases]]
input = [[1, 2], 3]
output = [0, 1]
""",
    )

    with pytest.raises(ProblemRunError, match="Solution class"):
        run_problem(problem_dir)


def test_run_problem_requires_entrypoint_method(tmp_path: Path) -> None:
    """Verify a missing entrypoint is a run error.

    Args:
        tmp_path: Temporary directory provided by pytest.

    Returns:
        None.
    """
    problem_dir = tmp_path / "missing-entrypoint"
    write_problem(
        problem_dir,
        """
class Solution:
    def other(self):
        return None
""",
        """
entrypoint = "twoSum"

[[cases]]
input = [[1, 2], 3]
output = [0, 1]
""",
    )

    with pytest.raises(ProblemRunError, match="twoSum"):
        run_problem(problem_dir)


def test_run_problem_wraps_import_errors(tmp_path: Path) -> None:
    """Verify solution import failures are reported as run errors.

    Args:
        tmp_path: Temporary directory provided by pytest.

    Returns:
        None.
    """
    problem_dir = tmp_path / "import-error"
    write_problem(
        problem_dir,
        """
raise RuntimeError("import exploded")
""",
        """
entrypoint = "twoSum"

[[cases]]
input = [[1, 2], 3]
output = [0, 1]
""",
    )

    with pytest.raises(ProblemRunError, match="failed to import solution.py"):
        run_problem(problem_dir)
