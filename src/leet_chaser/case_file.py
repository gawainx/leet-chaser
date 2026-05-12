"""Read and write Leet-Chaser TOML case files."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import tomllib

import tomli_w

from leet_chaser.linked_types import (
    LINKED_TYPE_NAMES,
    build_circular_linked_list,
    build_doubly_linked_list,
    build_linked_list,
)

RAW_TYPE_NAME = "raw"
CASE_TYPE_NAMES = LINKED_TYPE_NAMES | frozenset({RAW_TYPE_NAME})


@dataclass(frozen=True)
class Case:
    """A single LeetCode test case.

    Attributes:
        input: Positional arguments passed to a solution method.
        output: Expected result returned by the solution method.
        output_type: Expected parsing type for the output value.
    """

    input: list[Any]
    output: Any
    output_type: str = RAW_TYPE_NAME


@dataclass(frozen=True)
class CaseFile:
    """A parsed Leet-Chaser case file.

    Attributes:
        entrypoint: Name of the solution method used by the case file.
        cases: Test cases for the entrypoint.
        input_types: Expected parsing types for input arguments.
        output_type: Expected parsing type for output values.
    """

    entrypoint: str
    cases: list[Case]
    input_types: list[str] | None = None
    output_type: str = RAW_TYPE_NAME


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
    if case_file.input_types is not None:
        data["input_types"] = case_file.input_types
    if case_file.output_type != RAW_TYPE_NAME:
        data["output_type"] = case_file.output_type
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
    input_types = _parse_input_types(data.get("input_types"))
    output_type = _parse_case_type(data.get("output_type"), "output_type")

    raw_cases = data.get("cases")
    if not isinstance(raw_cases, list):
        raise CaseFileError("case file must contain a top-level [[cases]] array")

    cases = [
        _parse_case(raw_case, index, input_types, output_type)
        for index, raw_case in enumerate(raw_cases, start=1)
    ]
    return CaseFile(entrypoint=entrypoint, cases=cases, input_types=input_types, output_type=output_type)


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


def _parse_input_types(raw_input_types: Any) -> list[str] | None:
    """Parse and validate top-level input type metadata.

    Args:
        raw_input_types: Raw ``input_types`` value loaded from TOML.

    Returns:
        A list of type names, or ``None`` when the field is not defined.

    Raises:
        CaseFileError: If the metadata is not an array of supported type names.
    """
    if raw_input_types is None:
        return None
    if not isinstance(raw_input_types, list):
        raise CaseFileError("input_types must be an array of type names")
    return [
        _parse_case_type(raw_input_type, f"input_types[{index}]")
        for index, raw_input_type in enumerate(raw_input_types)
    ]


def _parse_case_type(raw_case_type: Any, field_name: str) -> str:
    """Parse and validate one case type name.

    Args:
        raw_case_type: Raw type name loaded from TOML.
        field_name: Field name used in error messages.

    Returns:
        Supported type name, defaulting to ``raw`` when absent.

    Raises:
        CaseFileError: If the value is not a supported type name.
    """
    if raw_case_type is None:
        return RAW_TYPE_NAME
    if not isinstance(raw_case_type, str):
        raise CaseFileError(f"{field_name} must be a type name string")
    case_type = raw_case_type.strip()
    if case_type not in CASE_TYPE_NAMES:
        supported_types = ", ".join(sorted(CASE_TYPE_NAMES))
        raise CaseFileError(f"{field_name} must be one of: {supported_types}")
    return case_type


def _parse_case(
    raw_case: Any,
    index: int,
    input_types: list[str] | None,
    output_type: str,
) -> Case:
    """Parse one raw case table.

    Args:
        raw_case: Raw case object loaded from TOML.
        index: One-based case index used in error messages.
        input_types: Type names used to parse input arguments.
        output_type: Type name used to parse output values.

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
    if input_types is not None and len(input_types) != len(input_value):
        raise CaseFileError(
            f"input_types length must match cases[{index}].input argument count"
        )

    parsed_input = (
        [
            _parse_typed_value(
                value,
                input_types[arg_index],
                f"cases[{index}].input[{arg_index}]",
            )
            for arg_index, value in enumerate(input_value)
        ]
        if input_types is not None
        else input_value
    )
    parsed_output = _parse_typed_value(raw_case["output"], output_type, f"cases[{index}].output")

    return Case(input=parsed_input, output=parsed_output, output_type=output_type)


def _parse_typed_value(value: Any, value_type: str, field_name: str) -> Any:
    """Parse one raw value according to a case type.

    Args:
        value: Raw TOML value.
        value_type: Type name selected for the value.
        field_name: Field name used in error messages.

    Returns:
        Original or converted value.

    Raises:
        CaseFileError: If the value does not match the selected type.
    """
    if value_type == RAW_TYPE_NAME:
        return value
    if value_type == "linked_list":
        return build_linked_list(_parse_array_values(value, field_name))
    if value_type == "doubly_linked_list":
        return build_doubly_linked_list(_parse_array_values(value, field_name))
    if value_type == "circular_linked_list":
        values, pos = _parse_circular_data(value, field_name)
        return build_circular_linked_list(values, pos)
    return value


def _parse_array_values(value: Any, field_name: str) -> list[Any]:
    """Parse a value that must be an array.

    Args:
        value: Raw TOML value.
        field_name: Field name used in error messages.

    Returns:
        The validated array value.

    Raises:
        CaseFileError: If the value is not an array.
    """
    if not isinstance(value, list):
        raise CaseFileError(f"{field_name} must be an array for linked-list parsing")
    return value


def _parse_circular_data(value: Any, field_name: str) -> tuple[list[Any], int]:
    """Parse circular linked-list TOML data.

    Args:
        value: Raw TOML value.
        field_name: Field name used in error messages.

    Returns:
        Values and cycle position.

    Raises:
        CaseFileError: If the table is malformed or ``pos`` is out of range.
    """
    if not isinstance(value, dict):
        raise CaseFileError(f"{field_name} must be a table with values and pos")
    values = value.get("values")
    pos = value.get("pos")
    if not isinstance(values, list):
        raise CaseFileError(f"{field_name}.values must be an array")
    if not isinstance(pos, int):
        raise CaseFileError(f"{field_name}.pos must be an integer")
    if pos < -1 or pos >= len(values):
        raise CaseFileError(f"{field_name}.pos must be -1 or a valid values index")
    if not values and pos != -1:
        raise CaseFileError(f"{field_name}.pos must be -1 for an empty list")
    return values, pos
