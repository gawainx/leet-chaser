"""Smoke tests for the package bootstrap."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from leet_chaser import __version__
from leet_chaser.case_file import Case, CaseFile, read_case_file
from leet_chaser.cli import app, normalize_project_name, resolve_init_case_type
from leet_chaser.tree_types import binary_tree_to_array

runner = CliRunner()


def test_version_is_defined() -> None:
    """Verify the package exposes a version string.

    Args:
        None.

    Returns:
        None.
    """
    assert __version__ == "0.1.4"


def test_cli_app_is_available() -> None:
    """Verify the Typer application can be imported.

    Args:
        None.

    Returns:
        None.
    """
    assert app.info.help == "Run LeetCode solutions against local test cases."


def test_init_creates_solution_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify init creates editable solution and case files.

    Args:
        tmp_path: Temporary directory provided by pytest.
        monkeypatch: Pytest helper used to run the command from tmp_path.

    Returns:
        None.
    """
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["init", "two-sum"], catch_exceptions=False, env={})

    project_dir = tmp_path / "two-sum"
    assert result.exit_code == 0
    assert (project_dir / "solution.py").read_text(encoding="utf-8") == ""
    assert read_case_file(project_dir / "cases.toml") == CaseFile(
        entrypoint="twoSum",
        cases=[
            Case(input=[[2, 7, 11, 15], 9], output=[0, 1]),
            Case(input=[["flower", "flow", "flight"]], output="fl"),
        ],
    )
    assert "Created two-sum" in result.output


def test_init_creates_linked_list_case_template(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify init can create a linked-list case template.

    Args:
        tmp_path: Temporary directory provided by pytest.
        monkeypatch: Pytest helper used to run the command from tmp_path.

    Returns:
        None.
    """
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        ["init", "reverse-list", "-t", "linklist"],
        catch_exceptions=False,
        env={},
    )

    project_dir = tmp_path / "reverse-list"
    parsed_case_file = read_case_file(project_dir / "cases.toml")
    assert result.exit_code == 0
    assert parsed_case_file.entrypoint == "reverseList"
    assert parsed_case_file.input_types == ["linked_list"]
    assert parsed_case_file.output_type == "linked_list"
    assert len(parsed_case_file.cases) == 2


def test_init_creates_binary_tree_case_template(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify init can create a binary-tree case template from a fuzzy alias.

    Args:
        tmp_path: Temporary directory provided by pytest.
        monkeypatch: Pytest helper used to run the command from tmp_path.

    Returns:
        None.
    """
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        ["init", "validate-bst", "--type", "bitree"],
        catch_exceptions=False,
        env={},
    )

    project_dir = tmp_path / "validate-bst"
    parsed_case_file = read_case_file(project_dir / "cases.toml")
    assert result.exit_code == 0
    assert parsed_case_file.entrypoint == "isValidBST"
    assert parsed_case_file.input_types == ["binary_tree"]
    assert parsed_case_file.output_type == "raw"
    assert binary_tree_to_array(parsed_case_file.cases[1].input[0]) == [
        5,
        1,
        4,
        "null",
        "null",
        3,
        6,
    ]


def test_init_rejects_unknown_case_template_type(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify unknown init template types fail before writing a workspace.

    Args:
        tmp_path: Temporary directory provided by pytest.
        monkeypatch: Pytest helper used to run the command from tmp_path.

    Returns:
        None.
    """
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["init", "heap-problem", "-t", "heap"], env={})

    assert result.exit_code != 0
    assert "type must be one of" in result.output
    assert not (tmp_path / "heap-problem").exists()


def test_resolve_init_case_type_accepts_fuzzy_aliases() -> None:
    """Verify init type matching ignores separators and common spelling variants.

    Args:
        None.

    Returns:
        None.
    """
    assert resolve_init_case_type(None) == "raw"
    assert resolve_init_case_type("linked-list") == "linked_list"
    assert resolve_init_case_type("ListNode") == "linked_list"
    assert resolve_init_case_type("binary_tree") == "binary_tree"
    assert resolve_init_case_type("tree") == "binary_tree"


def test_normalize_project_name_replaces_special_symbols() -> None:
    """Verify special symbols become single dash separators.

    Args:
        None.

    Returns:
        None.
    """
    assert normalize_project_name("Two Sum!! 001") == "Two-Sum-001"


def test_init_uses_normalized_directory_name(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify init creates the normalized directory name.

    Args:
        tmp_path: Temporary directory provided by pytest.
        monkeypatch: Pytest helper used to run the command from tmp_path.

    Returns:
        None.
    """
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["init", "Two Sum!! 001"], catch_exceptions=False, env={})

    assert result.exit_code == 0
    assert (tmp_path / "Two-Sum-001").is_dir()
    assert "Created Two-Sum-001" in result.output


def test_init_rejects_names_without_letters_or_numbers(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify init rejects names that normalize to an empty value.

    Args:
        tmp_path: Temporary directory provided by pytest.
        monkeypatch: Pytest helper used to run the command from tmp_path.

    Returns:
        None.
    """
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["init", "!!!"], env={})

    assert result.exit_code != 0
    assert "name must contain at least one letter or number" in result.output


def test_init_rejects_existing_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify init does not overwrite an existing solution workspace.

    Args:
        tmp_path: Temporary directory provided by pytest.
        monkeypatch: Pytest helper used to run the command from tmp_path.

    Returns:
        None.
    """
    project_dir = tmp_path / "two-sum"
    project_dir.mkdir()
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["init", "two-sum"], env={})

    assert result.exit_code != 0
    assert "directory already exists" in result.output


def test_run_command_executes_problem_directory(tmp_path: Path) -> None:
    """Verify run accepts a problem directory and reports passing cases.

    Args:
        tmp_path: Temporary directory provided by pytest.

    Returns:
        None.
    """
    problem_dir = tmp_path / "two-sum"
    problem_dir.mkdir()
    (problem_dir / "solution.py").write_text(
        """
class Solution:
    def twoSum(self, nums, target):
        return [0, 1]
""",
        encoding="utf-8",
    )
    (problem_dir / "cases.toml").write_text(
        """
entrypoint = "twoSum"

[[cases]]
input = [[2, 7], 9]
output = [0, 1]
""",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["run", str(problem_dir)], catch_exceptions=False, env={})

    assert result.exit_code == 0
    assert "PASS case 1" in result.output
    assert "Summary: 1/1 passed, 0 failed, 0 error(s)." in result.output


def test_reverse_linked_list_example_runs_successfully() -> None:
    """Verify the LeetCode 206 linked-list example stays runnable.

    Args:
        None.

    Returns:
        None.
    """
    example_dir = Path("examples/reverse-linked-list")

    result = runner.invoke(app, ["run", str(example_dir)], catch_exceptions=False, env={})

    assert result.exit_code == 0
    assert "Summary: 3/3 passed, 0 failed, 0 error(s)." in result.output


def test_validate_binary_search_tree_example_runs_successfully() -> None:
    """Verify the LeetCode 98 binary-tree example stays runnable.

    Args:
        None.

    Returns:
        None.
    """
    example_dir = Path("examples/validate-binary-search-tree")

    result = runner.invoke(app, ["run", str(example_dir)], catch_exceptions=False, env={})

    assert result.exit_code == 0
    assert "Summary: 3/3 passed, 0 failed, 0 error(s)." in result.output


def test_run_command_returns_nonzero_after_collecting_failures(tmp_path: Path) -> None:
    """Verify run prints a table for failed cases before returning a non-zero code.

    Args:
        tmp_path: Temporary directory provided by pytest.

    Returns:
        None.
    """
    problem_dir = tmp_path / "failures"
    problem_dir.mkdir()
    (problem_dir / "solution.py").write_text(
        """
class Solution:
    def echo(self, value):
        return value
""",
        encoding="utf-8",
    )
    (problem_dir / "cases.toml").write_text(
        """
entrypoint = "echo"

[[cases]]
input = ["first"]
output = "expected-first"

[[cases]]
input = ["second"]
output = "expected-second"
""",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["run", str(problem_dir)], env={})

    assert result.exit_code == 1
    assert "Failed Cases" in result.output
    assert "Input" in result.output
    assert "Expected" in result.output
    assert "Actual" in result.output
    assert "['first']" in result.output
    assert "'expected-first'" in result.output
    assert "'first'" in result.output
    assert "['second']" in result.output
    assert "'expected-second'" in result.output
    assert "'second'" in result.output
    assert "Summary: 0/2 passed, 2 failed, 0 error(s)." in result.output


def test_run_command_prints_case_tracebacks_after_normal_case_output(tmp_path: Path) -> None:
    """Verify errored cases are printed with full tracebacks after normal results.

    Args:
        tmp_path: Temporary directory provided by pytest.

    Returns:
        None.
    """
    problem_dir = tmp_path / "mixed-errors"
    problem_dir.mkdir()
    (problem_dir / "solution.py").write_text(
        """
class Solution:
    def classify(self, value):
        if value == "boom":
            raise RuntimeError("broken case")
        if value == "crash":
            raise ValueError("second error")
        return value
""",
        encoding="utf-8",
    )
    (problem_dir / "cases.toml").write_text(
        """
entrypoint = "classify"

[[cases]]
input = ["ok"]
output = "ok"

[[cases]]
input = ["wrong"]
output = "expected"

[[cases]]
input = ["boom"]
output = "safe"

[[cases]]
input = ["crash"]
output = "safe"
""",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["run", str(problem_dir)], env={})

    assert result.exit_code == 1
    pass_index = result.output.index("PASS case 1")
    table_index = result.output.index("Failed Cases")
    first_error_index = result.output.index("ERROR case 3: RuntimeError: broken case")
    second_error_index = result.output.index("ERROR case 4: ValueError: second error")
    summary_index = result.output.index("Summary: 1/4 passed, 1 failed, 2 error(s).")
    assert pass_index < table_index < first_error_index < second_error_index < summary_index
    assert "Traceback (most recent call last):" in result.output
    assert 'raise RuntimeError("broken case")' in result.output
    assert 'raise ValueError("second error")' in result.output
    assert "Input: ['boom']" in result.output
    assert "Expected: 'safe'" in result.output


def test_run_command_prints_inplace_return_warning(tmp_path: Path) -> None:
    """Verify run reports ignored return values for inplace write cases.

    Args:
        tmp_path: Temporary directory provided by pytest.

    Returns:
        None.
    """
    problem_dir = tmp_path / "move-zeroes-warning"
    problem_dir.mkdir()
    (problem_dir / "solution.py").write_text(
        """
class Solution:
    def moveZeroes(self, nums):
        nums.sort(key=lambda value: value == 0)
        return ["ignored"]
""",
        encoding="utf-8",
    )
    (problem_dir / "cases.toml").write_text(
        """
entrypoint = "moveZeroes"
inplace_write = true
inplace_index = 0

[[cases]]
input = [[0, 1, 0, 3, 12]]
output = [1, 3, 12, 0, 0]
""",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["run", str(problem_dir)], catch_exceptions=False, env={})

    assert result.exit_code == 0
    assert "WARNING case 1" in result.output
    assert "return value was ignored" in result.output
    assert "PASS case 1" in result.output


def test_debug_command_executes_default_debug_case(tmp_path: Path) -> None:
    """Verify debug accepts a problem directory and reports one passing case.

    Args:
        tmp_path: Temporary directory provided by pytest.

    Returns:
        None.
    """
    problem_dir = tmp_path / "debug-two-sum"
    problem_dir.mkdir()
    (problem_dir / "solution.py").write_text(
        """
class Solution:
    def twoSum(self, nums, target):
        return [0, 1]
""",
        encoding="utf-8",
    )
    (problem_dir / "debug.toml").write_text(
        """
entrypoint = "twoSum"

[[cases]]
input = [[2, 7], 9]
output = [0, 1]
""",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["debug", str(problem_dir), "-t", "nums"], catch_exceptions=False, env={})

    assert result.exit_code == 0
    assert "Case:" in result.output
    assert "Entrypoint: twoSum" in result.output
    assert "Trace: nums" in result.output
    assert "PASS actual=[0, 1] expected=[0, 1]" in result.output


def test_debug_command_prints_inplace_return_warning(tmp_path: Path) -> None:
    """Verify debug reports ignored return values for inplace write cases.

    Args:
        tmp_path: Temporary directory provided by pytest.

    Returns:
        None.
    """
    problem_dir = tmp_path / "debug-move-zeroes-warning"
    problem_dir.mkdir()
    (problem_dir / "solution.py").write_text(
        """
class Solution:
    def moveZeroes(self, nums):
        nums.sort(key=lambda value: value == 0)
        return ["ignored"]
""",
        encoding="utf-8",
    )
    (problem_dir / "debug.toml").write_text(
        """
entrypoint = "moveZeroes"
inplace_write = true
inplace_index = 0

[[cases]]
input = [[0, 1, 0, 3, 12]]
output = [1, 3, 12, 0, 0]
""",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["debug", str(problem_dir)], catch_exceptions=False, env={})

    assert result.exit_code == 0
    assert "WARNING case 1" in result.output
    assert "return value was ignored" in result.output
    assert "PASS actual=[1, 3, 12, 0, 0] expected=[1, 3, 12, 0, 0]" in result.output


def test_debug_command_returns_nonzero_for_failed_debug_case(tmp_path: Path) -> None:
    """Verify debug returns a non-zero code when the single case fails.

    Args:
        tmp_path: Temporary directory provided by pytest.

    Returns:
        None.
    """
    problem_dir = tmp_path / "debug-failure"
    problem_dir.mkdir()
    (problem_dir / "solution.py").write_text(
        """
class Solution:
    def echo(self, value):
        return value
""",
        encoding="utf-8",
    )
    (problem_dir / "debug.toml").write_text(
        """
entrypoint = "echo"

[[cases]]
input = ["actual"]
output = "expected"
""",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["debug", str(problem_dir)], env={})

    assert result.exit_code == 1
    assert "FAIL actual='actual' expected='expected'" in result.output
