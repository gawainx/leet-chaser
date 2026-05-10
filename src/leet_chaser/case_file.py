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


@dataclass(frozen=True)
class CaseFile:
    """A parsed Leet-Chaser case file.

    Attributes:
        entrypoint: Name of the solution method used by the case file.
        cases: Test cases for the entrypoint.
    """

    entrypoint: str
    cases: list[Case]


class CaseFileError(ValueError):
    """Raised when a case file has an invalid structure."""


def read_case_file(path: Path) -> CaseFile:
    """Read a test case file from TOML.

    Args:
        path: Path to a TOML case file containing ``entrypoint`` and ``cases``.

    Returns:
        Parsed case file data.

    Raises:
        CaseFileError: If the TOML document does not match the expected shape.
    """
    with path.open("rb") as file:
        data = tomllib.load(file)
    return parse_case_data(data)


def write_case_file(path: Path, case_file: CaseFile) -> None:
    """Write test case file data to TOML.

    Args:
        path: Destination path for the TOML case file.
        case_file: Case file data to serialize.

    Returns:
        None.
    """
    entrypoint = _parse_entrypoint(case_file.entrypoint)
    data = {
        "entrypoint": entrypoint,
        "cases": [
            {
                "input": test_case.input,
                "output": test_case.output,
            }
            for test_case in case_file.cases
        ]
    }
    path.write_text(tomli_w.dumps(data), encoding="utf-8")


def parse_case_data(data: dict[str, Any]) -> CaseFile:
    """Parse raw TOML data into a case file.

    Args:
        data: Loaded TOML data.

    Returns:
        Parsed and validated case file data.

    Raises:
        CaseFileError: If required fields are missing or have invalid types.
    """
    entrypoint = _parse_entrypoint(data.get("entrypoint"))

    raw_cases = data.get("cases")
    if not isinstance(raw_cases, list):
        raise CaseFileError("case file must contain a top-level [[cases]] array")

    cases = [_parse_case(raw_case, index) for index, raw_case in enumerate(raw_cases, start=1)]
    return CaseFile(entrypoint=entrypoint, cases=cases)


def _parse_entrypoint(raw_entrypoint: Any) -> str:
    """Parse and validate a raw entrypoint value.

    Args:
        raw_entrypoint: Raw entrypoint value loaded from TOML or supplied for writing.

    Returns:
        A stripped entrypoint string.

    Raises:
        CaseFileError: If entrypoint is not a non-empty string.
    """
    if not isinstance(raw_entrypoint, str) or not raw_entrypoint.strip():
        raise CaseFileError("case file must define a non-empty entrypoint string")
    return raw_entrypoint.strip()


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
