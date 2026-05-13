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
        FailedCaseResult(index=1, input=["wrong"], expected="expected", actual="wrong"),
        FailedCaseResult(index=4, input=["later-wrong"], expected="later-expected", actual="later-wrong"),
    ]
    assert len(result.errors) == 1
    assert result.errors[0].index == 2
    assert result.errors[0].error_type == "RuntimeError"
    assert result.errors[0].error_message == "broken case"
    assert "Traceback (most recent call last):" in result.errors[0].traceback
    assert 'raise RuntimeError("broken case")' in result.errors[0].traceback


def test_run_problem_normalizes_linked_list_output(tmp_path: Path) -> None:
    """Verify linked-list outputs compare as arrays.

    Args:
        tmp_path: Temporary directory provided by pytest.

    Returns:
        None.
    """
    problem_dir = tmp_path / "reverse-list"
    write_problem(
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

    result = run_problem(problem_dir)

    assert not result.has_failures
    assert result.passed[0].expected == [3, 2, 1]
    assert result.passed[0].actual == [3, 2, 1]


def test_run_problem_normalizes_circular_linked_list_output(tmp_path: Path) -> None:
    """Verify circular linked-list outputs compare by values and cycle position.

    Args:
        tmp_path: Temporary directory provided by pytest.

    Returns:
        None.
    """
    problem_dir = tmp_path / "identity-cycle"
    write_problem(
        problem_dir,
        """
class Solution:
    def identity(self, head):
        return head
""",
        """
entrypoint = "identity"
input_types = ["circular_linked_list"]
output_type = "circular_linked_list"

[[cases]]
input = [{ values = [3, 2, 0, -4], pos = 1 }]
output = { values = [3, 2, 0, -4], pos = 1 }
""",
    )

    result = run_problem(problem_dir)

    assert not result.has_failures
    assert result.passed[0].actual == {"values": [3, 2, 0, -4], "pos": 1}


def test_run_problem_passes_binary_tree_to_solution(tmp_path: Path) -> None:
    """Verify binary tree inputs are passed as TreeNode roots.

    Args:
        tmp_path: Temporary directory provided by pytest.

    Returns:
        None.
    """
    problem_dir = tmp_path / "validate-bst"
    write_problem(
        problem_dir,
        """
class Solution:
    def isValidBST(self, root):
        def walk(node, lower, upper):
            if node is None:
                return True
            if not lower < node.val < upper:
                return False
            return walk(node.left, lower, node.val) and walk(node.right, node.val, upper)

        return walk(root, float("-inf"), float("inf"))
""",
        """
entrypoint = "isValidBST"
input_types = ["binary_tree"]

[[cases]]
input = [[2, 1, 3]]
output = true

[[cases]]
input = [[5, 1, 4, "null", "null", 3, 6]]
output = false
""",
    )

    result = run_problem(problem_dir)

    assert not result.has_failures
    assert [case.actual for case in result.passed] == [True, False]


def test_run_problem_handles_binary_tree_level_order_solution(tmp_path: Path) -> None:
    """Verify level-order traversal can consume a binary tree input.

    Args:
        tmp_path: Temporary directory provided by pytest.

    Returns:
        None.
    """
    problem_dir = tmp_path / "level-order"
    write_problem(
        problem_dir,
        """
class Solution:
    def levelOrder(self, root):
        if root is None:
            return []
        levels = []
        queue = [(root, 0)]
        for node, depth in queue:
            if depth == len(levels):
                levels.append([])
            levels[depth].append(node.val)
            if node.left is not None:
                queue.append((node.left, depth + 1))
            if node.right is not None:
                queue.append((node.right, depth + 1))
        return levels
""",
        """
entrypoint = "levelOrder"
input_types = ["binary_tree"]

[[cases]]
input = [[3, 9, 20, "null", "null", 15, 7]]
output = [[3], [9, 20], [15, 7]]

[[cases]]
input = [[]]
output = []
""",
    )

    result = run_problem(problem_dir)

    assert not result.has_failures


def test_run_problem_normalizes_binary_tree_output(tmp_path: Path) -> None:
    """Verify binary tree outputs compare as trimmed level-order arrays.

    Args:
        tmp_path: Temporary directory provided by pytest.

    Returns:
        None.
    """
    problem_dir = tmp_path / "invert-tree"
    write_problem(
        problem_dir,
        """
class Solution:
    def invertTree(self, root):
        if root is None:
            return None
        root.left, root.right = self.invertTree(root.right), self.invertTree(root.left)
        return root
""",
        """
entrypoint = "invertTree"
input_types = ["binary_tree"]
output_type = "binary_tree"

[[cases]]
input = [[4, 2, 7, 1, 3, 6, 9]]
output = [4, 7, 2, 9, 6, 3, 1, "null", "null"]
""",
    )

    result = run_problem(problem_dir)

    assert not result.has_failures
    assert result.passed[0].expected == [4, 7, 2, 9, 6, 3, 1]
    assert result.passed[0].actual == [4, 7, 2, 9, 6, 3, 1]


def test_run_problem_compares_inplace_input_after_solution_call(tmp_path: Path) -> None:
    """Verify inplace write cases compare the mutated input argument.

    Args:
        tmp_path: Temporary directory provided by pytest.

    Returns:
        None.
    """
    problem_dir = tmp_path / "move-zeroes"
    write_problem(
        problem_dir,
        """
class Solution:
    def moveZeroes(self, nums):
        insert_at = 0
        for value in nums:
            if value != 0:
                nums[insert_at] = value
                insert_at += 1
        for index in range(insert_at, len(nums)):
            nums[index] = 0
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

    result = run_problem(problem_dir)

    assert not result.has_failures
    assert result.passed[0].actual == [1, 3, 12, 0, 0]


def test_run_problem_warns_when_inplace_case_returns_value(tmp_path: Path) -> None:
    """Verify non-None return values are ignored and reported for inplace cases.

    Args:
        tmp_path: Temporary directory provided by pytest.

    Returns:
        None.
    """
    problem_dir = tmp_path / "move-zeroes-return"
    write_problem(
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

    result = run_problem(problem_dir)

    assert not result.has_failures
    assert result.passed[0].actual == [1, 3, 12, 0, 0]
    assert result.warnings[0].index == 1
    assert "return value was ignored" in result.warnings[0].message


def test_run_problem_compares_unordered_three_sum_output(tmp_path: Path) -> None:
    """Verify unordered output ignores outer and inner list order.

    Args:
        tmp_path: Temporary directory provided by pytest.

    Returns:
        None.
    """
    problem_dir = tmp_path / "three-sum"
    write_problem(
        problem_dir,
        """
class Solution:
    def threeSum(self, nums):
        return [[1, 0, -1], [2, -1, -1]]
""",
        """
entrypoint = "threeSum"
unordered_output = true

[[cases]]
input = [[-1, 0, 1, 2, -1, -4]]
output = [[-1, -1, 2], [-1, 0, 1]]
""",
    )

    result = run_problem(problem_dir)

    assert not result.has_failures


def test_run_problem_detects_missing_unordered_output_item(tmp_path: Path) -> None:
    """Verify unordered output still fails when a result item is missing.

    Args:
        tmp_path: Temporary directory provided by pytest.

    Returns:
        None.
    """
    problem_dir = tmp_path / "three-sum-missing"
    write_problem(
        problem_dir,
        """
class Solution:
    def threeSum(self, nums):
        return [[-1, 0, 1]]
""",
        """
entrypoint = "threeSum"
unordered_output = true

[[cases]]
input = [[-1, 0, 1, 2, -1, -4]]
output = [[-1, -1, 2], [-1, 0, 1]]
""",
    )

    result = run_problem(problem_dir)

    assert result.has_failures
    assert result.failed[0].expected == [[-1, -1, 2], [-1, 0, 1]]
    assert result.failed[0].actual == [[-1, 0, 1]]


def test_run_problem_keeps_ordered_output_strict_by_default(tmp_path: Path) -> None:
    """Verify list output order still matters without unordered metadata.

    Args:
        tmp_path: Temporary directory provided by pytest.

    Returns:
        None.
    """
    problem_dir = tmp_path / "ordered-default"
    write_problem(
        problem_dir,
        """
class Solution:
    def values(self):
        return [2, 1]
""",
        """
entrypoint = "values"

[[cases]]
input = []
output = [1, 2]
""",
    )

    result = run_problem(problem_dir)

    assert result.has_failures


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
