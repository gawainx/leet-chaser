"""Tests for single-case solution debugging."""

from pathlib import Path
from typing import Any, Callable

import pytest

from leet_chaser.debugger import ProblemDebugError, debug_problem


def write_debug_problem(problem_dir: Path, solution: str, debug_case: str) -> None:
    """Write a temporary problem workspace with a debug case.

    Args:
        problem_dir: Directory that will receive solution and debug case files.
        solution: Python source written to ``solution.py``.
        debug_case: TOML source written to ``debug.toml``.

    Returns:
        None.
    """
    problem_dir.mkdir()
    (problem_dir / "solution.py").write_text(solution, encoding="utf-8")
    (problem_dir / "debug.toml").write_text(debug_case, encoding="utf-8")


def test_debug_problem_uses_default_debug_toml(tmp_path: Path) -> None:
    """Verify debug executes the default single-case TOML file.

    Args:
        tmp_path: Temporary directory provided by pytest.

    Returns:
        None.
    """
    problem_dir = tmp_path / "two-sum"
    write_debug_problem(
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

    result = debug_problem(problem_dir)

    assert result.case_path == problem_dir / "debug.toml"
    assert result.entrypoint == "twoSum"
    assert result.actual == [0, 1]
    assert result.passed


def test_debug_problem_passes_traces_to_snoop(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify requested trace expressions are passed to snoop.

    Args:
        tmp_path: Temporary directory provided by pytest.
        monkeypatch: Pytest helper used to replace the snoop decorator.

    Returns:
        None.
    """
    received_watch: tuple[str, ...] | None = None

    def fake_snoop(*, watch: tuple[str, ...]) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Capture the requested watch expressions and return an identity decorator.

        Args:
            watch: Expressions passed by ``debug_problem``.

        Returns:
            Decorator that leaves the wrapped function unchanged.
        """
        nonlocal received_watch
        received_watch = watch

        def decorate(function: Callable[..., Any]) -> Callable[..., Any]:
            """Return the wrapped function without adding trace behavior.

            Args:
                function: Callable selected for debugging.

            Returns:
                The same callable.
            """
            return function

        return decorate

    problem_dir = tmp_path / "echo"
    custom_case = tmp_path / "case.toml"
    problem_dir.mkdir()
    (problem_dir / "solution.py").write_text(
        """
class Solution:
    def echo(self, value):
        return value
""",
        encoding="utf-8",
    )
    custom_case.write_text(
        """
entrypoint = "echo"

[[cases]]
input = ["ok"]
output = "ok"
""",
        encoding="utf-8",
    )
    monkeypatch.setattr("leet_chaser.debugger.snoop.snoop", fake_snoop)

    result = debug_problem(problem_dir, case_path=custom_case, traces=("value", "self.answer"))

    assert result.case_path == custom_case
    assert result.traces == ("value", "self.answer")
    assert received_watch == ("value", "self.answer")


def test_debug_problem_requires_single_case(tmp_path: Path) -> None:
    """Verify debug rejects TOML files containing multiple cases.

    Args:
        tmp_path: Temporary directory provided by pytest.

    Returns:
        None.
    """
    problem_dir = tmp_path / "multi-case"
    write_debug_problem(
        problem_dir,
        """
class Solution:
    def echo(self, value):
        return value
""",
        """
entrypoint = "echo"

[[cases]]
input = ["first"]
output = "first"

[[cases]]
input = ["second"]
output = "second"
""",
    )

    with pytest.raises(ProblemDebugError, match="exactly one"):
        debug_problem(problem_dir)


def test_debug_problem_normalizes_linked_list_output(tmp_path: Path) -> None:
    """Verify debug pass/fail checks normalize linked-list outputs.

    Args:
        tmp_path: Temporary directory provided by pytest.

    Returns:
        None.
    """
    problem_dir = tmp_path / "reverse-list"
    write_debug_problem(
        problem_dir,
        """
class Solution:
    def reverseList(self, head):
        previous = None
        current = head
        while current is not None:
            next_node = current.next
            current.next = previous
            previous = current
            current = next_node
        return previous
""",
        """
entrypoint = "reverseList"
input_types = ["linked_list"]
output_type = "linked_list"

[[cases]]
input = [[1, 2, 3]]
output = [3, 2, 1]
""",
    )

    result = debug_problem(problem_dir)

    assert result.passed


def test_debug_problem_compares_inplace_input_after_solution_call(tmp_path: Path) -> None:
    """Verify debug cases can compare mutated input arguments.

    Args:
        tmp_path: Temporary directory provided by pytest.

    Returns:
        None.
    """
    problem_dir = tmp_path / "move-zeroes"
    write_debug_problem(
        problem_dir,
        """
class Solution:
    def moveZeroes(self, nums):
        nums.sort(key=lambda value: value == 0)
        return ["ignored"]
""",
        """
entrypoint = "moveZeroes"
inplace_write = true
inplace_index = 0

[[cases]]
input = [[0, 1, 0, 3, 12]]
output = [1, 3, 12, 0, 0]
""",
    )

    result = debug_problem(problem_dir)

    assert result.passed
    assert result.actual == [1, 3, 12, 0, 0]
    assert "return value was ignored" in result.warnings[0].message
