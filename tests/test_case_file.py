"""Tests for TOML case file read and write behavior."""

from pathlib import Path

import pytest

from leet_chaser.case_file import Case, CaseFileError, read_case_file, write_case_file


def test_read_case_file_supports_common_leetcode_values(tmp_path: Path) -> None:
    """Verify TOML cases can express varied LeetCode inputs and outputs.

    Args:
        tmp_path: Temporary directory provided by pytest.

    Returns:
        None.
    """
    case_file = tmp_path / "cases.toml"
    case_file.write_text(
        """
[[cases]]
input = [[2, 7, 11, 15], 9]
output = [0, 1]

[[cases]]
input = [["flower", "flow", "flight"]]
output = "fl"

[[cases]]
input = [121]
output = true

[[cases]]
input = [[[1, 2], [3, 4]], 2]
output = [[1, 2], [3, 4]]
""",
        encoding="utf-8",
    )

    cases = read_case_file(case_file)

    assert cases == [
        Case(input=[[2, 7, 11, 15], 9], output=[0, 1]),
        Case(input=[["flower", "flow", "flight"]], output="fl"),
        Case(input=[121], output=True),
        Case(input=[[[1, 2], [3, 4]], 2], output=[[1, 2], [3, 4]]),
    ]


def test_write_case_file_round_trips_cases(tmp_path: Path) -> None:
    """Verify test cases can be written and read back.

    Args:
        tmp_path: Temporary directory provided by pytest.

    Returns:
        None.
    """
    case_file = tmp_path / "cases.toml"
    cases = [
        Case(input=["abc"], output=3),
        Case(input=[["a", "b"], {"left": 1, "right": 2}], output=False),
    ]

    write_case_file(case_file, cases)

    assert read_case_file(case_file) == cases


def test_read_case_file_rejects_missing_cases_array(tmp_path: Path) -> None:
    """Verify files without [[cases]] fail with a clear error.

    Args:
        tmp_path: Temporary directory provided by pytest.

    Returns:
        None.
    """
    case_file = tmp_path / "cases.toml"
    case_file.write_text("title = 'invalid'\n", encoding="utf-8")

    with pytest.raises(CaseFileError, match=r"top-level \[\[cases\]\] array"):
        read_case_file(case_file)


def test_read_case_file_requires_input_to_be_argument_array(tmp_path: Path) -> None:
    """Verify each input is an array of positional arguments.

    Args:
        tmp_path: Temporary directory provided by pytest.

    Returns:
        None.
    """
    case_file = tmp_path / "cases.toml"
    case_file.write_text(
        """
[[cases]]
input = "abc"
output = 3
""",
        encoding="utf-8",
    )

    with pytest.raises(CaseFileError, match=r"cases\[1\]\.input must be an array"):
        read_case_file(case_file)
