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
from leet_chaser.tree_types import TREE_TYPE_NAMES, build_binary_tree

RAW_TYPE_NAME = "raw"
CASE_TYPE_NAMES = LINKED_TYPE_NAMES | TREE_TYPE_NAMES | frozenset({RAW_TYPE_NAME})
CASE_MODE_NORMAL = "normal"
CASE_MODE_OPERATIONS = "operations"
CASE_MODE_NAMES = frozenset({CASE_MODE_NORMAL, CASE_MODE_OPERATIONS})


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
class OperationCase:
    """A single operation-sequence test case.

    Attributes:
        operations: Constructor and method names in call order.
        input: Positional argument arrays aligned to ``operations``.
        output: Expected return values aligned to ``operations``.
    """

    operations: list[str]
    input: list[list[Any]]
    output: list[Any]


@dataclass(frozen=True)
class CaseFile:
    """A parsed Leet-Chaser case file.

    Attributes:
        entrypoint: Name of the solution method used by the case file.
        cases: Test cases for the entrypoint.
        input_types: Expected parsing types for input arguments.
        output_type: Expected parsing type for output values.
        inplace_write: Whether comparisons should use a mutated input argument.
        inplace_index: Zero-based input argument index used for inplace comparison.
        unordered_output: Whether list output comparisons should ignore element order.
        mode: Case execution mode.
        class_name: Class name used by operations mode.
        operation_cases: Operation-sequence cases used by operations mode.
    """

    entrypoint: str
    cases: list[Case]
    input_types: list[str] | None = None
    output_type: str = RAW_TYPE_NAME
    inplace_write: bool = False
    inplace_index: int | None = None
    unordered_output: bool = False
    mode: str = CASE_MODE_NORMAL
    class_name: str | None = None
    operation_cases: list[OperationCase] | None = None


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
    mode = _parse_case_mode(case_file.mode)
    if mode == CASE_MODE_OPERATIONS:
        class_name = _parse_class_name(case_file.class_name)
        operation_cases = case_file.operation_cases or []
        data = {
            "mode": CASE_MODE_OPERATIONS,
            "class_name": class_name,
            "cases": [
                {
                    "operations": test_case.operations,
                    "input": test_case.input,
                    "output": test_case.output,
                }
                for test_case in operation_cases
            ],
        }
        path.write_text(tomli_w.dumps(data), encoding="utf-8")
        return

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
    if case_file.inplace_write:
        data["inplace_write"] = case_file.inplace_write
        data["inplace_index"] = case_file.inplace_index
    if case_file.unordered_output:
        data["unordered_output"] = case_file.unordered_output
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
    mode = _parse_case_mode(data.get("mode"))
    if mode == CASE_MODE_OPERATIONS:
        class_name = _parse_class_name(data.get("class_name"))
        raw_cases = data.get("cases")
        if not isinstance(raw_cases, list):
            raise CaseFileError("case file must contain a top-level [[cases]] array")
        operation_cases = [
            _parse_operation_case(raw_case, index, class_name)
            for index, raw_case in enumerate(raw_cases, start=1)
        ]
        return CaseFile(
            entrypoint="",
            cases=[],
            mode=CASE_MODE_OPERATIONS,
            class_name=class_name,
            operation_cases=operation_cases,
        )

    entrypoint = _parse_entrypoint(data.get("entrypoint"))
    input_types = _parse_input_types(data.get("input_types"))
    output_type = _parse_case_type(data.get("output_type"), "output_type")
    inplace_write = _parse_inplace_write(data.get("inplace_write"))
    inplace_index = _parse_inplace_index(data.get("inplace_index"), inplace_write)
    unordered_output = _parse_unordered_output(data.get("unordered_output"))

    raw_cases = data.get("cases")
    if not isinstance(raw_cases, list):
        raise CaseFileError("case file must contain a top-level [[cases]] array")

    cases = [
        _parse_case(raw_case, index, input_types, output_type)
        for index, raw_case in enumerate(raw_cases, start=1)
    ]
    _validate_inplace_index(cases, inplace_index)
    return CaseFile(
        entrypoint=entrypoint,
        cases=cases,
        input_types=input_types,
        output_type=output_type,
        inplace_write=inplace_write,
        inplace_index=inplace_index,
        unordered_output=unordered_output,
        mode=CASE_MODE_NORMAL,
    )


def _parse_case_mode(raw_mode: Any) -> str:
    """Parse and validate the top-level case execution mode.

    Args:
        raw_mode: Raw ``mode`` value loaded from TOML.

    Returns:
        The selected case execution mode.

    Raises:
        CaseFileError: If the mode is unsupported.
    """
    if raw_mode is None:
        return CASE_MODE_NORMAL
    if not isinstance(raw_mode, str):
        raise CaseFileError("mode must be a string")
    mode = raw_mode.strip()
    if mode not in CASE_MODE_NAMES:
        supported_modes = ", ".join(sorted(CASE_MODE_NAMES))
        raise CaseFileError(f"mode must be one of: {supported_modes}")
    return mode


def _parse_class_name(raw_class_name: Any) -> str:
    """Parse and validate an operations mode class name.

    Args:
        raw_class_name: Raw ``class_name`` value loaded from TOML.

    Returns:
        The stripped class name.

    Raises:
        CaseFileError: If the class name is missing or empty.
    """
    if not isinstance(raw_class_name, str) or not raw_class_name.strip():
        raise CaseFileError("operations mode must define a non-empty class_name string")
    return raw_class_name.strip()


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


def _parse_inplace_write(raw_inplace_write: Any) -> bool:
    """Parse the top-level inplace write flag.

    Args:
        raw_inplace_write: Raw ``inplace_write`` value loaded from TOML.

    Returns:
        True when cases should compare a mutated input argument.

    Raises:
        CaseFileError: If the value is not a boolean.
    """
    if raw_inplace_write is None:
        return False
    if not isinstance(raw_inplace_write, bool):
        raise CaseFileError("inplace_write must be a boolean")
    return raw_inplace_write


def _parse_unordered_output(raw_unordered_output: Any) -> bool:
    """Parse the top-level unordered output flag.

    Args:
        raw_unordered_output: Raw ``unordered_output`` value loaded from TOML.

    Returns:
        True when list output comparison should ignore element order.

    Raises:
        CaseFileError: If the value is not a boolean.
    """
    if raw_unordered_output is None:
        return False
    if not isinstance(raw_unordered_output, bool):
        raise CaseFileError("unordered_output must be a boolean")
    return raw_unordered_output


def _parse_inplace_index(raw_inplace_index: Any, inplace_write: bool) -> int | None:
    """Parse the top-level inplace input argument index.

    Args:
        raw_inplace_index: Raw ``inplace_index`` value loaded from TOML.
        inplace_write: Whether the case file uses inplace comparison.

    Returns:
        A zero-based input argument index, or ``None`` for normal return comparison.

    Raises:
        CaseFileError: If the index is missing, disabled, or invalid.
    """
    if raw_inplace_index is None:
        if inplace_write:
            raise CaseFileError("inplace_index is required when inplace_write is true")
        return None
    if not inplace_write:
        raise CaseFileError("inplace_index requires inplace_write to be true")
    if not isinstance(raw_inplace_index, int) or isinstance(raw_inplace_index, bool):
        raise CaseFileError("inplace_index must be a zero-based integer")
    if raw_inplace_index < 0:
        raise CaseFileError("inplace_index must be a zero-based integer")
    return raw_inplace_index


def _validate_inplace_index(cases: list[Case], inplace_index: int | None) -> None:
    """Validate that the inplace index exists in every case input.

    Args:
        cases: Parsed cases from the TOML file.
        inplace_index: Zero-based input argument index used for inplace comparison.

    Returns:
        None.

    Raises:
        CaseFileError: If any case does not contain the selected input argument.
    """
    if inplace_index is None:
        return
    for index, test_case in enumerate(cases, start=1):
        if inplace_index >= len(test_case.input):
            raise CaseFileError(f"inplace_index is out of range for cases[{index}].input")


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


def _parse_operation_case(raw_case: Any, index: int, class_name: str) -> OperationCase:
    """Parse one operations mode case table.

    Args:
        raw_case: Raw case object loaded from TOML.
        index: One-based case index used in error messages.
        class_name: Expected constructor operation name.

    Returns:
        A validated operation-sequence case.

    Raises:
        CaseFileError: If the operation case is malformed.
    """
    if not isinstance(raw_case, dict):
        raise CaseFileError(f"cases[{index}] must be a table")

    operations = _parse_operations(raw_case.get("operations"), index)
    input_value = _parse_operation_inputs(raw_case.get("input"), index)
    output = _parse_operation_outputs(raw_case.get("output"), index)
    if len(operations) != len(input_value) or len(operations) != len(output):
        raise CaseFileError(
            f"cases[{index}] operations, input, and output must have matching lengths"
        )
    if operations[0] != class_name:
        raise CaseFileError(
            f"cases[{index}].operations[0] must match class_name {class_name!r}"
        )
    return OperationCase(operations=operations, input=input_value, output=output)


def _parse_operations(raw_operations: Any, case_index: int) -> list[str]:
    """Parse operations mode operation names.

    Args:
        raw_operations: Raw ``operations`` value loaded from TOML.
        case_index: One-based case index used in error messages.

    Returns:
        Non-empty operation name list.

    Raises:
        CaseFileError: If operations are missing or invalid.
    """
    if not isinstance(raw_operations, list) or not raw_operations:
        raise CaseFileError(f"cases[{case_index}].operations must be a non-empty array")
    operations: list[str] = []
    for operation_index, operation in enumerate(raw_operations):
        if not isinstance(operation, str) or not operation.strip():
            raise CaseFileError(
                f"cases[{case_index}].operations[{operation_index}] must be a non-empty string"
            )
        operations.append(operation.strip())
    return operations


def _parse_operation_inputs(raw_input: Any, case_index: int) -> list[list[Any]]:
    """Parse operations mode call argument arrays.

    Args:
        raw_input: Raw ``input`` value loaded from TOML.
        case_index: One-based case index used in error messages.

    Returns:
        Argument arrays aligned to operation names.

    Raises:
        CaseFileError: If inputs are missing or invalid.
    """
    if not isinstance(raw_input, list):
        raise CaseFileError(f"cases[{case_index}].input must be an array")
    inputs: list[list[Any]] = []
    for input_index, arguments in enumerate(raw_input):
        if not isinstance(arguments, list):
            raise CaseFileError(
                f"cases[{case_index}].input[{input_index}] must be an array of arguments"
            )
        inputs.append(arguments)
    return inputs


def _parse_operation_outputs(raw_output: Any, case_index: int) -> list[Any]:
    """Parse operations mode expected return values.

    Args:
        raw_output: Raw ``output`` value loaded from TOML.
        case_index: One-based case index used in error messages.

    Returns:
        Expected values aligned to operation names.

    Raises:
        CaseFileError: If outputs are missing or invalid.
    """
    if not isinstance(raw_output, list):
        raise CaseFileError(f"cases[{case_index}].output must be an array")
    return raw_output


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
    if value_type == "binary_tree":
        values = _parse_tree_values(value, field_name)
        try:
            return build_binary_tree(values)
        except ValueError as error:
            raise CaseFileError(f"{field_name} is not valid binary-tree data: {error}") from error
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


def _parse_tree_values(value: Any, field_name: str) -> list[Any]:
    """Parse a binary-tree value that must be an array.

    Args:
        value: Raw TOML value.
        field_name: Field name used in error messages.

    Returns:
        The validated level-order array value.

    Raises:
        CaseFileError: If the value is not an array.
    """
    if not isinstance(value, list):
        raise CaseFileError(f"{field_name} must be an array for binary-tree parsing")
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
