"""Tests for TOML case file read and write behavior."""

from pathlib import Path

import pytest

from leet_chaser.case_file import Case, CaseFile, CaseFileError, read_case_file, write_case_file
from leet_chaser.linked_types import (
    DoublyListNode,
    ListNode,
    circular_linked_list_to_data,
    doubly_linked_list_to_array,
    linked_list_to_array,
)


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
entrypoint = "twoSum"

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

    parsed_case_file = read_case_file(case_file)

    assert parsed_case_file == CaseFile(
        entrypoint="twoSum",
        cases=[
            Case(input=[[2, 7, 11, 15], 9], output=[0, 1]),
            Case(input=[["flower", "flow", "flight"]], output="fl"),
            Case(input=[121], output=True),
            Case(input=[[[1, 2], [3, 4]], 2], output=[[1, 2], [3, 4]]),
        ],
    )


def test_write_case_file_round_trips_cases(tmp_path: Path) -> None:
    """Verify test cases can be written and read back.

    Args:
        tmp_path: Temporary directory provided by pytest.

    Returns:
        None.
    """
    case_file = tmp_path / "cases.toml"
    source_case_file = CaseFile(
        entrypoint="lengthOfLongestSubstring",
        cases=[
            Case(input=["abc"], output=3),
            Case(input=[["a", "b"], {"left": 1, "right": 2}], output=False),
        ],
    )

    write_case_file(case_file, source_case_file)

    assert read_case_file(case_file) == source_case_file


def test_read_case_file_parses_linked_list_type_metadata(tmp_path: Path) -> None:
    """Verify advanced linked-list type metadata converts input and output values.

    Args:
        tmp_path: Temporary directory provided by pytest.

    Returns:
        None.
    """
    case_file = tmp_path / "cases.toml"
    case_file.write_text(
        """
entrypoint = "mergeTwoLists"
input_types = ["linked_list", "raw"]
output_type = "linked_list"

[[cases]]
input = [[1, 2, 4], 7]
output = [1, 2, 4, 7]
""",
        encoding="utf-8",
    )

    parsed_case_file = read_case_file(case_file)
    parsed_case = parsed_case_file.cases[0]

    assert parsed_case_file.input_types == ["linked_list", "raw"]
    assert parsed_case_file.output_type == "linked_list"
    assert isinstance(parsed_case.input[0], ListNode)
    assert parsed_case.input[1] == 7
    assert linked_list_to_array(parsed_case.input[0]) == [1, 2, 4]
    assert linked_list_to_array(parsed_case.output) == [1, 2, 4, 7]


def test_read_case_file_parses_doubly_linked_list_type_metadata(tmp_path: Path) -> None:
    """Verify doubly linked list metadata creates nodes with backward links.

    Args:
        tmp_path: Temporary directory provided by pytest.

    Returns:
        None.
    """
    case_file = tmp_path / "cases.toml"
    case_file.write_text(
        """
entrypoint = "copy"
input_types = ["doubly_linked_list"]
output_type = "doubly_linked_list"

[[cases]]
input = [[1, 2, 3]]
output = [1, 2, 3]
""",
        encoding="utf-8",
    )

    parsed_case = read_case_file(case_file).cases[0]
    head = parsed_case.input[0]

    assert isinstance(head, DoublyListNode)
    assert doubly_linked_list_to_array(head) == [1, 2, 3]
    assert head.next.prev is head


def test_read_case_file_parses_circular_linked_list_type_metadata(tmp_path: Path) -> None:
    """Verify circular linked list metadata uses values and pos.

    Args:
        tmp_path: Temporary directory provided by pytest.

    Returns:
        None.
    """
    case_file = tmp_path / "cases.toml"
    case_file.write_text(
        """
entrypoint = "detectCycle"
input_types = ["circular_linked_list"]
output_type = "circular_linked_list"

[[cases]]
input = [{ values = [3, 2, 0, -4], pos = 1 }]
output = { values = [3, 2, 0, -4], pos = 1 }
""",
        encoding="utf-8",
    )

    parsed_case = read_case_file(case_file).cases[0]

    assert circular_linked_list_to_data(parsed_case.input[0]) == {
        "values": [3, 2, 0, -4],
        "pos": 1,
    }
    assert circular_linked_list_to_data(parsed_case.output) == {
        "values": [3, 2, 0, -4],
        "pos": 1,
    }


def test_read_case_file_parses_inplace_write_metadata(tmp_path: Path) -> None:
    """Verify inplace write metadata is parsed from top-level TOML fields.

    Args:
        tmp_path: Temporary directory provided by pytest.

    Returns:
        None.
    """
    case_file = tmp_path / "cases.toml"
    case_file.write_text(
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

    parsed_case_file = read_case_file(case_file)

    assert parsed_case_file.inplace_write is True
    assert parsed_case_file.inplace_index == 0


def test_read_case_file_requires_entrypoint(tmp_path: Path) -> None:
    """Verify files without an entrypoint fail with a clear error.

    Args:
        tmp_path: Temporary directory provided by pytest.

    Returns:
        None.
    """
    case_file = tmp_path / "cases.toml"
    case_file.write_text(
        """
[[cases]]
input = [121]
output = true
""",
        encoding="utf-8",
    )

    with pytest.raises(CaseFileError, match="non-empty entrypoint string"):
        read_case_file(case_file)


def test_read_case_file_rejects_blank_entrypoint(tmp_path: Path) -> None:
    """Verify a blank entrypoint is rejected.

    Args:
        tmp_path: Temporary directory provided by pytest.

    Returns:
        None.
    """
    case_file = tmp_path / "cases.toml"
    case_file.write_text(
        """
entrypoint = "   "

[[cases]]
input = [121]
output = true
""",
        encoding="utf-8",
    )

    with pytest.raises(CaseFileError, match="non-empty entrypoint string"):
        read_case_file(case_file)


def test_read_case_file_rejects_missing_cases_array(tmp_path: Path) -> None:
    """Verify files without [[cases]] fail with a clear error.

    Args:
        tmp_path: Temporary directory provided by pytest.

    Returns:
        None.
    """
    case_file = tmp_path / "cases.toml"
    case_file.write_text('entrypoint = "twoSum"\n', encoding="utf-8")

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
entrypoint = "twoSum"

[[cases]]
input = "abc"
output = 3
""",
        encoding="utf-8",
    )

    with pytest.raises(CaseFileError, match=r"cases\[1\]\.input must be an array"):
        read_case_file(case_file)


def test_read_case_file_rejects_unknown_case_type(tmp_path: Path) -> None:
    """Verify unsupported advanced type names fail clearly.

    Args:
        tmp_path: Temporary directory provided by pytest.

    Returns:
        None.
    """
    case_file = tmp_path / "cases.toml"
    case_file.write_text(
        """
entrypoint = "twoSum"
input_types = ["tree"]

[[cases]]
input = [[1, 2]]
output = true
""",
        encoding="utf-8",
    )

    with pytest.raises(CaseFileError, match=r"input_types\[0\] must be one of"):
        read_case_file(case_file)


def test_read_case_file_rejects_input_type_count_mismatch(tmp_path: Path) -> None:
    """Verify input_types length must match each case input argument count.

    Args:
        tmp_path: Temporary directory provided by pytest.

    Returns:
        None.
    """
    case_file = tmp_path / "cases.toml"
    case_file.write_text(
        """
entrypoint = "twoSum"
input_types = ["linked_list"]

[[cases]]
input = [[1, 2], 3]
output = true
""",
        encoding="utf-8",
    )

    with pytest.raises(CaseFileError, match="input_types length"):
        read_case_file(case_file)


def test_read_case_file_rejects_circular_pos_out_of_range(tmp_path: Path) -> None:
    """Verify circular linked list positions must reference existing nodes.

    Args:
        tmp_path: Temporary directory provided by pytest.

    Returns:
        None.
    """
    case_file = tmp_path / "cases.toml"
    case_file.write_text(
        """
entrypoint = "hasCycle"
input_types = ["circular_linked_list"]

[[cases]]
input = [{ values = [1, 2], pos = 2 }]
output = false
""",
        encoding="utf-8",
    )

    with pytest.raises(CaseFileError, match=r"pos must be -1"):
        read_case_file(case_file)


def test_read_case_file_requires_inplace_index_when_enabled(tmp_path: Path) -> None:
    """Verify inplace write mode requires a selected input index.

    Args:
        tmp_path: Temporary directory provided by pytest.

    Returns:
        None.
    """
    case_file = tmp_path / "cases.toml"
    case_file.write_text(
        """
entrypoint = "moveZeroes"
inplace_write = true

[[cases]]
input = [[0]]
output = [0]
""",
        encoding="utf-8",
    )

    with pytest.raises(CaseFileError, match="inplace_index is required"):
        read_case_file(case_file)


def test_read_case_file_rejects_inplace_index_without_inplace_write(tmp_path: Path) -> None:
    """Verify inplace index cannot be configured without inplace write mode.

    Args:
        tmp_path: Temporary directory provided by pytest.

    Returns:
        None.
    """
    case_file = tmp_path / "cases.toml"
    case_file.write_text(
        """
entrypoint = "moveZeroes"
inplace_index = 0

[[cases]]
input = [[0]]
output = [0]
""",
        encoding="utf-8",
    )

    with pytest.raises(CaseFileError, match="requires inplace_write"):
        read_case_file(case_file)


def test_read_case_file_rejects_out_of_range_inplace_index(tmp_path: Path) -> None:
    """Verify inplace index must exist in every case input.

    Args:
        tmp_path: Temporary directory provided by pytest.

    Returns:
        None.
    """
    case_file = tmp_path / "cases.toml"
    case_file.write_text(
        """
entrypoint = "moveZeroes"
inplace_write = true
inplace_index = 1

[[cases]]
input = [[0]]
output = [0]
""",
        encoding="utf-8",
    )

    with pytest.raises(CaseFileError, match="out of range"):
        read_case_file(case_file)
