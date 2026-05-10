"""Read and write Leet-Chaser TOML case files."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import tomllib

import tomli_w


@dataclass(frozen=True)
class Case:
    """A single LeetCode test case.

    Attributes:
        input: Positional arguments passed to a solution method.
        output: Expected result returned by the solution method.
    """

    input: list[Any]
    output: Any


class CaseFileError(ValueError):
    """Raised when a case file has an invalid structure."""


def read_case_file(path: Path) -> list[Case]:
    """Read test cases from a TOML file.

    Args:
        path: Path to a TOML case file containing a top-level ``cases`` array.

    Returns:
        A list of parsed test cases.

    Raises:
        CaseFileError: If the TOML document does not match the expected shape.
    """
    with path.open("rb") as file:
        data = tomllib.load(file)
    return parse_case_data(data)


def write_case_file(path: Path, cases: list[Case]) -> None:
    """Write test cases to a TOML file.

    Args:
        path: Destination path for the TOML case file.
        cases: Test cases to serialize.

    Returns:
        None.
    """
    data = {
        "cases": [
            {
                "input": test_case.input,
                "output": test_case.output,
            }
            for test_case in cases
        ]
    }
    path.write_text(tomli_w.dumps(data), encoding="utf-8")


def parse_case_data(data: dict[str, Any]) -> list[Case]:
    """Parse raw TOML data into test cases.

    Args:
        data: Loaded TOML data.

    Returns:
        A list of validated test cases.

    Raises:
        CaseFileError: If required fields are missing or have invalid types.
    """
    raw_cases = data.get("cases")
    if not isinstance(raw_cases, list):
        raise CaseFileError("case file must contain a top-level [[cases]] array")

    return [_parse_case(raw_case, index) for index, raw_case in enumerate(raw_cases, start=1)]


def _parse_case(raw_case: Any, index: int) -> Case:
    """Parse one raw case table.

    Args:
        raw_case: Raw case object loaded from TOML.
        index: One-based case index used in error messages.

    Returns:
        A validated test case.

    Raises:
        CaseFileError: If the case is not a table or lacks required fields.
    """
    if not isinstance(raw_case, dict):
        raise CaseFileError(f"cases[{index}] must be a table")

    if "input" not in raw_case:
        raise CaseFileError(f"cases[{index}] must define input")
    if "output" not in raw_case:
        raise CaseFileError(f"cases[{index}] must define output")

    input_value = raw_case["input"]
    if not isinstance(input_value, list):
        raise CaseFileError(f"cases[{index}].input must be an array of arguments")

    return Case(input=input_value, output=raw_case["output"])
