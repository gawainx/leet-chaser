"""Smoke tests for the package bootstrap."""

from io import BytesIO
from pathlib import Path
import tomllib
from urllib.error import HTTPError, URLError

import pytest
from typer.testing import CliRunner

from leet_chaser import __version__
from leet_chaser.case_file import CASE_MODE_OPERATIONS, Case, CaseFile, OperationCase, parse_case_data, read_case_file
from leet_chaser.cli import app, normalize_project_name, resolve_init_case_type
from leet_chaser.leetcode_client import (
    LeetCodeClientError,
    LeetCodeQuestionMetadata,
    build_remote_init_files,
    fetch_title_slug,
    format_remote_case_toml,
    parse_class_name_from_python_code,
    post_graphql,
)
from leet_chaser.tree_types import binary_tree_to_array

runner = CliRunner()


def read_case_file_text(case_text: str) -> CaseFile:
    """Parse a TOML case file from text.

    Args:
        case_text: Raw TOML case file text.

    Returns:
        Parsed case file.
    """
    return parse_case_data(tomllib.loads(case_text))


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


def test_init_creates_matrix_case_template(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify init can create a two-dimensional matrix case template.

    Args:
        tmp_path: Temporary directory provided by pytest.
        monkeypatch: Pytest helper used to run the command from tmp_path.

    Returns:
        None.
    """
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        ["init", "search-matrix", "--type", "matrix"],
        catch_exceptions=False,
        env={},
    )

    project_dir = tmp_path / "search-matrix"
    parsed_case_file = read_case_file(project_dir / "cases.toml")
    assert result.exit_code == 0
    assert parsed_case_file.entrypoint == "searchMatrix"
    assert parsed_case_file.input_types is None
    assert parsed_case_file.cases[0] == Case(
        input=[[[1, 3, 5, 7], [10, 11, 16, 20], [23, 30, 34, 60]], 3],
        output=True,
    )


def test_init_creates_remote_question_workspace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify init can create a workspace from a public LeetCode question number.

    Args:
        tmp_path: Temporary directory provided by pytest.
        monkeypatch: Pytest helper used to run the command from tmp_path.

    Returns:
        None.
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "leet_chaser.cli.fetch_question_metadata",
        lambda question_number: LeetCodeQuestionMetadata(
            question_number=question_number,
            title="Two Sum",
            title_slug="two-sum",
            entrypoint="twoSum",
            python_code=(
                "class Solution:\n"
                "    def twoSum(self, nums: List[int], target: int) -> List[int]:\n"
                "        pass\n"
            ),
            content_html=(
                "<p><strong>Example 1:</strong></p><pre>"
                "<strong>Input:</strong> nums = [2,7,11,15], target = 9<br>"
                "<strong>Output:</strong> [0,1]</pre>"
            ),
            parameter_names=["nums", "target"],
        ),
    )

    result = runner.invoke(app, ["init", "-q", "1"], catch_exceptions=False, env={})

    project_dir = tmp_path / "lt001.twoSum"
    assert result.exit_code == 0
    assert "def twoSum" in (project_dir / "solution.py").read_text(encoding="utf-8")
    assert read_case_file(project_dir / "cases.toml") == CaseFile(
        entrypoint="twoSum",
        cases=[Case(input=[[2, 7, 11, 15], 9], output=[0, 1])],
    )
    assert "Fetching LeetCode question 1" in result.output
    assert "Fetched question 1: Two Sum (two-sum)" in result.output
    assert "Generating local files for twoSum" in result.output
    assert "Wrote solution.py and cases.toml" in result.output
    assert "Created lt001.twoSum" in result.output


def test_init_creates_remote_operations_question_workspace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify init can create an operations mode workspace from LeetCode metadata.

    Args:
        tmp_path: Temporary directory provided by pytest.
        monkeypatch: Pytest helper used to run the command from tmp_path.

    Returns:
        None.
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "leet_chaser.cli.fetch_question_metadata",
        lambda question_number: LeetCodeQuestionMetadata(
            question_number=question_number,
            title="LRU Cache",
            title_slug="lru-cache",
            entrypoint="LRUCache",
            python_code="class LRUCache:\n    def __init__(self, capacity: int):\n        pass\n",
            content_html=(
                "<p><strong>Example 1:</strong></p><pre>"
                "<strong>Input</strong><br>"
                "[\"LRUCache\", \"put\", \"get\"]<br>"
                "[[2], [1, 1], [1]]<br>"
                "<strong>Output</strong><br>"
                "[null, null, 1]</pre>"
            ),
            parameter_names=[],
            case_mode="operations",
            class_name="LRUCache",
        ),
    )

    result = runner.invoke(app, ["init", "-q", "146"], catch_exceptions=False, env={})

    project_dir = tmp_path / "lt146.LRUCache"
    assert result.exit_code == 0
    assert read_case_file(project_dir / "cases.toml") == CaseFile(
        entrypoint="",
        cases=[],
        mode=CASE_MODE_OPERATIONS,
        class_name="LRUCache",
        operation_cases=[
            OperationCase(
                operations=["LRUCache", "put", "get"],
                input=[[2], [1, 1], [1]],
                output=["null", "null", 1],
            )
        ],
    )


def test_init_remote_question_accepts_custom_directory_name(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify a custom init name overrides the remote question directory name.

    Args:
        tmp_path: Temporary directory provided by pytest.
        monkeypatch: Pytest helper used to run the command from tmp_path.

    Returns:
        None.
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "leet_chaser.cli.fetch_question_metadata",
        lambda question_number: LeetCodeQuestionMetadata(
            question_number=question_number,
            title="Two Sum",
            title_slug="two-sum",
            entrypoint="twoSum",
            python_code="class Solution:\n    def twoSum(self, nums, target):\n        pass\n",
            content_html="<pre>Input: nums = [3,2,4], target = 6\nOutput: [1,2]</pre>",
            parameter_names=["nums", "target"],
        ),
    )

    result = runner.invoke(
        app,
        ["init", "custom-two-sum", "--question-number", "1"],
        catch_exceptions=False,
        env={},
    )

    assert result.exit_code == 0
    assert (tmp_path / "custom-two-sum").is_dir()
    assert not (tmp_path / "lt001.twoSum").exists()


def test_init_remote_question_rejects_case_type(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify question-number init rejects fixed case templates.

    Args:
        tmp_path: Temporary directory provided by pytest.
        monkeypatch: Pytest helper used to run the command from tmp_path.

    Returns:
        None.
    """
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["init", "-q", "1", "-t", "matrix"], env={})

    assert result.exit_code != 0
    assert "type cannot be used with question-number" in result.output
    assert not any(tmp_path.iterdir())


def test_remote_case_toml_keeps_one_dimensional_arrays_on_one_line() -> None:
    """Verify generated remote TOML keeps flat arrays readable.

    Args:
        None.

    Returns:
        None.
    """
    case_text = format_remote_case_toml(
        "longestConsecutive",
        [
            {
                "input": [[0, 3, 7, 2, 5, 8, 4, 6, 0, 1]],
                "output": 9,
            }
        ],
    )

    assert "input = [\n    [0, 3, 7, 2, 5, 8, 4, 6, 0, 1],\n]" in case_text
    assert read_case_file_text(case_text) == CaseFile(
        entrypoint="longestConsecutive",
        cases=[Case(input=[[0, 3, 7, 2, 5, 8, 4, 6, 0, 1]], output=9)],
    )


def test_remote_case_toml_formats_two_dimensional_arrays_across_lines() -> None:
    """Verify generated remote TOML expands nested arrays.

    Args:
        None.

    Returns:
        None.
    """
    case_text = format_remote_case_toml(
        "searchMatrix",
        [
            {
                "input": [[[1, 3], [5, 7]], 3],
                "output": True,
            }
        ],
    )

    assert "        [1, 3]," in case_text
    assert "        [5, 7]," in case_text
    assert read_case_file_text(case_text) == CaseFile(
        entrypoint="searchMatrix",
        cases=[Case(input=[[[1, 3], [5, 7]], 3], output=True)],
    )


def test_remote_case_toml_formats_operations_mode() -> None:
    """Verify generated remote TOML supports operations mode cases.

    Args:
        None.

    Returns:
        None.
    """
    case_text = format_remote_case_toml(
        "LRUCache",
        [
            {
                "operations": ["LRUCache", "put", "get"],
                "input": [[2], [1, 1], [1]],
                "output": ["null", "null", 1],
            }
        ],
        case_mode="operations",
        class_name="LRUCache",
    )

    assert 'mode = "operations"' in case_text
    assert 'class_name = "LRUCache"' in case_text
    assert "operations = [\"LRUCache\", \"put\", \"get\"]" in case_text
    assert read_case_file_text(case_text) == CaseFile(
        entrypoint="",
        cases=[],
        mode=CASE_MODE_OPERATIONS,
        class_name="LRUCache",
        operation_cases=[
            OperationCase(
                operations=["LRUCache", "put", "get"],
                input=[[2], [1, 1], [1]],
                output=["null", "null", 1],
            )
        ],
    )


def test_build_remote_init_files_detects_operations_mode() -> None:
    """Verify class-only snippets generate operations mode init files.

    Args:
        None.

    Returns:
        None.
    """
    init_files = build_remote_init_files(
        LeetCodeQuestionMetadata(
            question_number=146,
            title="LRU Cache",
            title_slug="lru-cache",
            entrypoint="LRUCache",
            python_code="class LRUCache:\n    def __init__(self, capacity: int):\n        pass\n",
            content_html=(
                "<pre>Input\n"
                "[\"LRUCache\", \"put\", \"get\"]\n"
                "[[2], [1, 1], [1]]\n"
                "Output\n"
                "[null, null, 1]</pre>"
            ),
            parameter_names=[],
            case_mode="operations",
            class_name="LRUCache",
        )
    )

    assert init_files.directory_name == "lt146.LRUCache"
    assert read_case_file_text(init_files.case_text).mode == CASE_MODE_OPERATIONS


def test_parse_class_name_from_python_code_reads_operations_class() -> None:
    """Verify operations snippets expose their top-level class name.

    Args:
        None.

    Returns:
        None.
    """
    assert parse_class_name_from_python_code("class LRUCache:\n    pass\n") == "LRUCache"


def test_fetch_title_slug_reads_problemset_data_field(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify title slug lookup reads LeetCode's paginated data field.

    Args:
        monkeypatch: Pytest helper used to replace the GraphQL request.

    Returns:
        None.
    """

    def fake_post_graphql(payload: dict, operation: str = "query LeetCode") -> dict:
        """Return a minimal LeetCode problemset response.

        Args:
            payload: GraphQL payload produced by title slug lookup.
            operation: Human-readable operation name.

        Returns:
            Fake GraphQL response using the current ``data`` field name.
        """
        assert "data" in payload["query"]
        assert payload["variables"]["categorySlug"] == ""
        return {
            "data": {
                "problemsetQuestionList": {
                    "data": [
                        {
                            "frontendQuestionId": "128",
                            "titleSlug": "longest-consecutive-sequence",
                            "paidOnly": False,
                        }
                    ]
                }
            }
        }

    monkeypatch.setattr("leet_chaser.leetcode_client.post_graphql", fake_post_graphql)

    assert fetch_title_slug(128) == "longest-consecutive-sequence"


def test_fetch_title_slug_reports_paid_only_question(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify paid-only questions produce a public access error.

    Args:
        monkeypatch: Pytest helper used to replace the GraphQL request.

    Returns:
        None.
    """

    def fake_post_graphql(payload: dict, operation: str = "query LeetCode") -> dict:
        """Return a paid-only problemset response.

        Args:
            payload: GraphQL payload produced by title slug lookup.
            operation: Human-readable operation name.

        Returns:
            Fake GraphQL response for a paid-only question.
        """
        return {
            "data": {
                "problemsetQuestionList": {
                    "data": [
                        {
                            "frontendQuestionId": "1",
                            "titleSlug": "two-sum",
                            "paidOnly": True,
                        }
                    ]
                }
            }
        }

    monkeypatch.setattr("leet_chaser.leetcode_client.post_graphql", fake_post_graphql)

    with pytest.raises(LeetCodeClientError, match="paid-only"):
        fetch_title_slug(1)


def test_fetch_title_slug_reports_unlisted_public_problemset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify missing question numbers produce a public problemset hint.

    Args:
        monkeypatch: Pytest helper used to replace the GraphQL request.

    Returns:
        None.
    """

    def fake_post_graphql(payload: dict, operation: str = "query LeetCode") -> dict:
        """Return an empty public problemset response.

        Args:
            payload: GraphQL payload produced by title slug lookup.
            operation: Human-readable operation name.

        Returns:
            Fake GraphQL response with no matching question.
        """
        return {"data": {"problemsetQuestionList": {"data": []}}}

    monkeypatch.setattr("leet_chaser.leetcode_client.post_graphql", fake_post_graphql)

    with pytest.raises(LeetCodeClientError, match="public problemset"):
        fetch_title_slug(999999)


def test_post_graphql_reports_http_query_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify HTTP failures include query and API-change diagnostics.

    Args:
        monkeypatch: Pytest helper used to replace ``urlopen``.

    Returns:
        None.
    """

    def fake_urlopen(request, timeout: int):
        """Raise an HTTP error with a GraphQL-style response body.

        Args:
            request: Request passed to ``urlopen``.
            timeout: Request timeout in seconds.

        Raises:
            HTTPError: Always raised for this test.
        """
        raise HTTPError(
            url="https://leetcode.com/graphql",
            code=400,
            msg="Bad Request",
            hdrs={},
            fp=BytesIO(b'{"errors":[{"message":"Cannot query field"}]}'),
        )

    monkeypatch.setattr("leet_chaser.leetcode_client.urlopen", fake_urlopen)

    with pytest.raises(LeetCodeClientError) as error:
        post_graphql({"query": "query { ping }"}, operation="lookup question number")

    message = str(error.value)
    assert "lookup question number failed" in message
    assert "HTTP 400" in message
    assert "public GraphQL query is invalid" in message
    assert "Cannot query field" in message


def test_post_graphql_reports_network_unreachable(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify network failures include reachability diagnostics.

    Args:
        monkeypatch: Pytest helper used to replace ``urlopen``.

    Returns:
        None.
    """

    def fake_urlopen(request, timeout: int):
        """Raise a URL error for this test.

        Args:
            request: Request passed to ``urlopen``.
            timeout: Request timeout in seconds.

        Raises:
            URLError: Always raised for this test.
        """
        raise URLError("network unreachable")

    monkeypatch.setattr("leet_chaser.leetcode_client.urlopen", fake_urlopen)

    with pytest.raises(LeetCodeClientError) as error:
        post_graphql({"query": "query { ping }"}, operation="fetch question detail")

    message = str(error.value)
    assert "fetch question detail failed" in message
    assert "could not reach LeetCode" in message
    assert "network unreachable" in message


def test_post_graphql_reports_graphql_schema_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify GraphQL errors include schema-change diagnostics.

    Args:
        monkeypatch: Pytest helper used to replace ``urlopen``.

    Returns:
        None.
    """

    class FakeResponse:
        """Minimal context-manager response used by ``post_graphql`` tests."""

        def __enter__(self):
            """Return this fake response.

            Returns:
                The fake response object.
            """
            return self

        def __exit__(self, exc_type, exc_value, traceback) -> None:
            """Close the fake response context.

            Args:
                exc_type: Exception type.
                exc_value: Exception value.
                traceback: Exception traceback.

            Returns:
                None.
            """

        def read(self) -> bytes:
            """Return a GraphQL error payload.

            Returns:
                JSON response bytes.
            """
            return b'{"errors":[{"message":"missing categorySlug"}]}'

    def fake_urlopen(request, timeout: int):
        """Return a fake GraphQL error response.

        Args:
            request: Request passed to ``urlopen``.
            timeout: Request timeout in seconds.

        Returns:
            Fake response object.
        """
        return FakeResponse()

    monkeypatch.setattr("leet_chaser.leetcode_client.urlopen", fake_urlopen)

    with pytest.raises(LeetCodeClientError) as error:
        post_graphql({"query": "query { ping }"}, operation="lookup question number")

    message = str(error.value)
    assert "GraphQL error" in message
    assert "schema or required arguments changed" in message
    assert "missing categorySlug" in message


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
    assert resolve_init_case_type("2d-array") == "matrix"
    assert resolve_init_case_type("grid") == "matrix"


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
