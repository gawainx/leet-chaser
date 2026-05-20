"""Fetch public LeetCode problem data for init templates."""

from __future__ import annotations

import ast
import html
import json
import re
import socket
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from leet_chaser.case_templates import (
    NORMAL_CASE_CONFIG_COMMENTS,
    OPERATIONS_CASE_CONFIG_COMMENTS,
)

CASE_MODE_NORMAL = "normal"
CASE_MODE_OPERATIONS = "operations"
LEETCODE_CN_GRAPHQL_URL = "https://leetcode.cn/graphql"
LEETCODE_GLOBAL_GRAPHQL_URL = "https://leetcode.com/graphql"
GRAPHQL_URL = LEETCODE_GLOBAL_GRAPHQL_URL
REQUEST_TIMEOUT_SECONDS = 10
REQUEST_ATTEMPTS = 3


@dataclass(frozen=True)
class LeetCodeGraphQLEndpoint:
    """GraphQL endpoint configuration.

    Attributes:
        name: Human-readable endpoint name for diagnostics.
        url: GraphQL endpoint URL.
        referer: Referer header accepted by the endpoint.
    """

    name: str
    url: str
    referer: str


LEETCODE_CN_ENDPOINT = LeetCodeGraphQLEndpoint(
    name="leetcode.cn",
    url=LEETCODE_CN_GRAPHQL_URL,
    referer="https://leetcode.cn/problemset/",
)
LEETCODE_GLOBAL_ENDPOINT = LeetCodeGraphQLEndpoint(
    name="leetcode.com",
    url=LEETCODE_GLOBAL_GRAPHQL_URL,
    referer="https://leetcode.com/problemset/",
)


class LeetCodeClientError(ValueError):
    """Raised when public LeetCode problem data cannot be fetched or parsed."""


@dataclass(frozen=True)
class LeetCodeQuestionMetadata:
    """Public LeetCode question data needed by init.

    Attributes:
        question_number: Public LeetCode frontend question number.
        title: Human-readable question title.
        title_slug: LeetCode question slug.
        entrypoint: Python solution method name.
        case_mode: Generated case file mode.
        class_name: Class name used by operations mode questions.
        python_code: Python3 code snippet for ``solution.py``.
        content_html: HTML problem statement containing examples.
        parameter_names: Solution parameter names in positional order.
    """

    question_number: int
    title: str
    title_slug: str
    entrypoint: str
    python_code: str
    content_html: str
    parameter_names: list[str]
    case_mode: str = CASE_MODE_NORMAL
    class_name: str | None = None


@dataclass(frozen=True)
class RemoteInitFiles:
    """Files generated from a public LeetCode question.

    Attributes:
        directory_name: Default problem workspace directory name.
        solution_text: Contents written to ``solution.py``.
        case_text: Contents written to ``cases.toml``.
    """

    directory_name: str
    solution_text: str
    case_text: str


def fetch_question_metadata(question_number: int) -> LeetCodeQuestionMetadata:
    """Fetch public metadata for a LeetCode question number.

    Args:
        question_number: Public LeetCode frontend question number.

    Returns:
        Structured metadata for init file generation.

    Raises:
        LeetCodeClientError: If the question cannot be fetched or parsed.
    """
    title_slug = fetch_title_slug(question_number)
    question_data = fetch_question_data(title_slug)
    python_code = parse_python_code(question_data)
    try:
        entrypoint = parse_entrypoint_from_python_code(python_code)
        case_mode = CASE_MODE_NORMAL
        class_name = None
        parameter_names = parse_parameter_names(question_data, entrypoint)
    except LeetCodeClientError:
        class_name = parse_class_name_from_python_code(python_code)
        entrypoint = class_name
        case_mode = CASE_MODE_OPERATIONS
        parameter_names = []
    return LeetCodeQuestionMetadata(
        question_number=question_number,
        title=parse_required_string(question_data, "title"),
        title_slug=parse_required_string(question_data, "titleSlug"),
        entrypoint=entrypoint,
        case_mode=case_mode,
        class_name=class_name,
        python_code=python_code,
        content_html=parse_required_string(question_data, "content"),
        parameter_names=parameter_names,
    )


def fetch_title_slug(question_number: int) -> str:
    """Fetch a LeetCode title slug from a public frontend question number.

    Args:
        question_number: Public LeetCode frontend question number.

    Returns:
        Matching title slug.

    Raises:
        LeetCodeClientError: If no exact public question match is found.
    """
    try:
        return fetch_title_slug_from_cn(question_number)
    except LeetCodeClientError as cn_error:
        try:
            return fetch_title_slug_from_global(question_number)
        except LeetCodeClientError as global_error:
            raise LeetCodeClientError(
                f"question {question_number} lookup failed on leetcode.cn and leetcode.com; "
                f"leetcode.cn detail: {cn_error}; leetcode.com detail: {global_error}"
            ) from global_error


def fetch_title_slug_from_cn(question_number: int) -> str:
    """Fetch a title slug from LeetCode CN's problemset list.

    Args:
        question_number: Public LeetCode frontend question number.

    Returns:
        Matching title slug.

    Raises:
        LeetCodeClientError: If no exact public question match is found.
    """
    query = """
query problemsetQuestionList($categorySlug: String, $limit: Int, $skip: Int) {
  problemsetQuestionListV2(categorySlug: $categorySlug, limit: $limit, skip: $skip) {
    questions {
      questionFrontendId
      titleSlug
      paidOnly
    }
  }
}
"""
    payload = {
        "query": query,
        "variables": {
            "categorySlug": "",
            "limit": 1,
            "skip": question_number - 1,
        },
    }
    data = post_graphql(
        payload,
        operation="lookup question number",
        endpoint=LEETCODE_CN_ENDPOINT,
    )
    questions = (
        data.get("data", {})
        .get("problemsetQuestionListV2", {})
        .get("questions", [])
    )
    for question in questions:
        if str(question.get("questionFrontendId")) == str(question_number):
            if question.get("paidOnly") is True:
                raise LeetCodeClientError(
                    f"question {question_number} is paid-only and cannot be fetched without login"
                )
            title_slug = question.get("titleSlug")
            if isinstance(title_slug, str) and title_slug:
                return title_slug
    raise LeetCodeClientError(
        f"question {question_number} was not found in the public leetcode.cn problemset; "
        "it may not exist or may not be publicly listed"
    )


def fetch_title_slug_from_global(question_number: int) -> str:
    """Fetch a title slug from LeetCode global's problemset search.

    Args:
        question_number: Public LeetCode frontend question number.

    Returns:
        Matching title slug.

    Raises:
        LeetCodeClientError: If no exact public question match is found.
    """
    query = """
query problemsetQuestionList($categorySlug: String, $filters: QuestionListFilterInput, $limit: Int, $skip: Int) {
  problemsetQuestionList: questionList(categorySlug: $categorySlug, filters: $filters, limit: $limit, skip: $skip) {
    data {
      frontendQuestionId: questionFrontendId
      titleSlug
      paidOnly: isPaidOnly
    }
  }
}
"""
    payload = {
        "query": query,
        "variables": {
            "categorySlug": "",
            "filters": {"searchKeywords": str(question_number)},
            "limit": 50,
            "skip": 0,
        },
    }
    data = post_graphql(payload, operation="lookup question number")
    questions = (
        data.get("data", {})
        .get("problemsetQuestionList", {})
        .get("data", [])
    )
    for question in questions:
        if str(question.get("frontendQuestionId")) == str(question_number):
            if question.get("paidOnly") is True:
                raise LeetCodeClientError(
                    f"question {question_number} is paid-only and cannot be fetched without login"
                )
            title_slug = question.get("titleSlug")
            if isinstance(title_slug, str) and title_slug:
                return title_slug
    raise LeetCodeClientError(
        f"question {question_number} was not found in the public problemset; "
        "it may not exist or may not be publicly listed"
    )


def fetch_question_data(title_slug: str) -> dict[str, Any]:
    """Fetch public question data by LeetCode title slug.

    Args:
        title_slug: LeetCode question slug.

    Returns:
        Raw question data.

    Raises:
        LeetCodeClientError: If the question data is unavailable.
    """
    try:
        return fetch_question_data_from_endpoint(title_slug, LEETCODE_CN_ENDPOINT)
    except LeetCodeClientError as cn_error:
        try:
            return fetch_question_data_from_endpoint(title_slug, LEETCODE_GLOBAL_ENDPOINT)
        except LeetCodeClientError as global_error:
            raise LeetCodeClientError(
                f"question data for {title_slug} failed on leetcode.cn and leetcode.com; "
                f"leetcode.cn detail: {cn_error}; leetcode.com detail: {global_error}"
            ) from global_error


def fetch_question_data_from_endpoint(
    title_slug: str,
    endpoint: LeetCodeGraphQLEndpoint,
) -> dict[str, Any]:
    """Fetch public question data by title slug from a GraphQL endpoint.

    Args:
        title_slug: LeetCode question slug.
        endpoint: GraphQL endpoint configuration.

    Returns:
        Raw question data.

    Raises:
        LeetCodeClientError: If the question data is unavailable.
    """
    query = """
query questionData($titleSlug: String!) {
  question(titleSlug: $titleSlug) {
    questionFrontendId
    title
    titleSlug
    content
    metaData
    codeSnippets {
      lang
      langSlug
      code
    }
  }
}
"""
    data = post_graphql(
        {"query": query, "variables": {"titleSlug": title_slug}},
        operation="fetch question detail",
        endpoint=endpoint,
    )
    question = data.get("data", {}).get("question")
    if not isinstance(question, dict):
        raise LeetCodeClientError(
            f"question data for {title_slug} was not returned; "
            "the question may not be public or LeetCode may have changed the question detail API"
        )
    return question


def post_graphql(
    payload: dict[str, Any],
    operation: str = "query LeetCode",
    endpoint: LeetCodeGraphQLEndpoint = LEETCODE_GLOBAL_ENDPOINT,
) -> dict[str, Any]:
    """Post a JSON GraphQL request to LeetCode.

    Args:
        payload: GraphQL query and variables.
        operation: Human-readable operation name for error messages.
        endpoint: GraphQL endpoint configuration.

    Returns:
        Parsed JSON response.

    Raises:
        LeetCodeClientError: If the request or response fails.
    """
    last_error: LeetCodeClientError | None = None
    for attempt in range(1, REQUEST_ATTEMPTS + 1):
        try:
            return post_graphql_once(payload, operation=operation, endpoint=endpoint)
        except LeetCodeClientError as error:
            last_error = error
            if not is_retryable_client_error(error) or attempt == REQUEST_ATTEMPTS:
                break
    if last_error is None:
        raise LeetCodeClientError(f"{operation} failed: no request attempt was made")
    raise last_error


def post_graphql_once(
    payload: dict[str, Any],
    operation: str,
    endpoint: LeetCodeGraphQLEndpoint,
) -> dict[str, Any]:
    """Post a single JSON GraphQL request to LeetCode.

    Args:
        payload: GraphQL query and variables.
        operation: Human-readable operation name for error messages.
        endpoint: GraphQL endpoint configuration.

    Returns:
        Parsed JSON response.

    Raises:
        LeetCodeClientError: If the request or response fails.
    """
    body = json.dumps(payload).encode("utf-8")
    request = Request(
        endpoint.url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "leet-chaser",
            "Referer": endpoint.referer,
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            raw_response = response.read().decode("utf-8")
    except HTTPError as error:
        detail = read_http_error_body(error)
        raise LeetCodeClientError(
            f"{operation} failed on {endpoint.name}: LeetCode returned HTTP {error.code}; "
            "this usually means the public GraphQL query is invalid or LeetCode changed its API"
            f"{detail}"
        ) from error
    except URLError as error:
        raise LeetCodeClientError(
            f"{operation} failed on {endpoint.name}: could not reach LeetCode; check network access, DNS, "
            f"proxy, or LeetCode availability; detail: {error.reason}"
        ) from error
    except (TimeoutError, socket.timeout) as error:
        raise LeetCodeClientError(
            f"{operation} failed on {endpoint.name}: LeetCode request timed out after "
            f"{REQUEST_TIMEOUT_SECONDS} seconds"
        ) from error

    try:
        data = json.loads(raw_response)
    except json.JSONDecodeError as error:
        raise LeetCodeClientError(
            f"{operation} failed on {endpoint.name}: LeetCode returned invalid JSON; "
            "the public endpoint response format may have changed"
        ) from error

    if data.get("errors"):
        raise LeetCodeClientError(
            f"{operation} failed on {endpoint.name}: LeetCode returned a GraphQL error; "
            "this usually means the public GraphQL schema or required arguments changed; "
            f"detail: {format_graphql_errors(data.get('errors'))}"
        )
    if not isinstance(data, dict):
        raise LeetCodeClientError(
            f"{operation} failed on {endpoint.name}: LeetCode returned an invalid response shape"
        )
    return data


def is_retryable_client_error(error: LeetCodeClientError) -> bool:
    """Return whether a client error should be retried.

    Args:
        error: Request error raised by ``post_graphql_once``.

    Returns:
        True when the error is likely transient.
    """
    message = str(error)
    return "timed out" in message or "could not reach LeetCode" in message


def read_http_error_body(error: HTTPError) -> str:
    """Read a short HTTP error response body for diagnostics.

    Args:
        error: HTTP error raised by ``urlopen``.

    Returns:
        A formatted detail suffix, or an empty string when the body is unavailable.
    """
    try:
        raw_body = error.read().decode("utf-8", errors="replace").strip()
    except (OSError, ValueError):
        return ""
    if not raw_body:
        return ""
    return f"; detail: {raw_body[:500]}"


def format_graphql_errors(errors: Any) -> str:
    """Format GraphQL errors into a compact diagnostic string.

    Args:
        errors: Raw GraphQL ``errors`` payload.

    Returns:
        Human-readable error messages.
    """
    if not isinstance(errors, list):
        return str(errors)
    messages = [
        error.get("message")
        for error in errors
        if isinstance(error, dict) and isinstance(error.get("message"), str)
    ]
    if not messages:
        return str(errors)
    return " | ".join(messages)


def build_remote_init_files(metadata: LeetCodeQuestionMetadata) -> RemoteInitFiles:
    """Build init file contents from public LeetCode metadata.

    Args:
        metadata: Public LeetCode question metadata.

    Returns:
        Directory name and file text for init.

    Raises:
        LeetCodeClientError: If no runnable examples can be generated.
    """
    cases = parse_examples(
        metadata.content_html,
        metadata.parameter_names,
        case_mode=metadata.case_mode,
    )
    if not cases:
        raise LeetCodeClientError(
            f"could not parse examples for question {metadata.question_number}"
        )

    question_prefix = f"lt{metadata.question_number:03d}"
    return RemoteInitFiles(
        directory_name=f"{question_prefix}.{metadata.entrypoint}",
        solution_text=metadata.python_code.rstrip() + "\n",
        case_text=format_remote_case_toml(
            metadata.entrypoint,
            cases,
            case_mode=metadata.case_mode,
            class_name=metadata.class_name,
        ),
    )


def format_remote_case_toml(
    entrypoint: str,
    cases: list[dict[str, Any]],
    case_mode: str = CASE_MODE_NORMAL,
    class_name: str | None = None,
) -> str:
    """Format remote init cases into readable TOML.

    Args:
        entrypoint: Solution method name used by the case file.
        cases: Case dictionaries containing ``input`` and ``output`` values.
        case_mode: Generated case file mode.
        class_name: Class name used by operations mode questions.

    Returns:
        TOML text where one-dimensional arrays stay on one line.
    """
    if case_mode == CASE_MODE_OPERATIONS:
        if class_name is None:
            raise LeetCodeClientError("operations mode requires class_name")
        lines = OPERATIONS_CASE_CONFIG_COMMENTS.splitlines() + [
            f"mode = {format_toml_value(CASE_MODE_OPERATIONS)}",
            f"class_name = {format_toml_value(class_name)}",
            "",
        ]
        for index, test_case in enumerate(cases):
            if index > 0:
                lines.append("")
            lines.append("[[cases]]")
            lines.append(f"operations = {format_toml_value(test_case['operations'])}")
            lines.append(f"input = {format_toml_value(test_case['input'])}")
            lines.append(f"output = {format_toml_value(test_case['output'])}")
        return "\n".join(lines) + "\n"

    lines = NORMAL_CASE_CONFIG_COMMENTS.splitlines() + [
        f"entrypoint = {format_toml_value(entrypoint)}",
        "",
    ]
    for index, test_case in enumerate(cases):
        if index > 0:
            lines.append("")
        lines.append("[[cases]]")
        lines.append(f"input = {format_toml_value(test_case['input'])}")
        lines.append(f"output = {format_toml_value(test_case['output'])}")
    return "\n".join(lines) + "\n"


def format_toml_value(value: Any, indent: int = 0) -> str:
    """Format a Python value as a readable TOML literal.

    Args:
        value: Python value parsed from a LeetCode example.
        indent: Current indentation depth.

    Returns:
        TOML literal text.

    Raises:
        LeetCodeClientError: If the value type cannot be represented.
    """
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int | float):
        return repr(value)
    if isinstance(value, list):
        return format_toml_array(value, indent)
    raise LeetCodeClientError(f"cannot format value as TOML: {type(value).__name__}")


def format_toml_array(values: list[Any], indent: int = 0) -> str:
    """Format a TOML array with compact one-dimensional lists.

    Args:
        values: Array values to format.
        indent: Current indentation depth.

    Returns:
        TOML array text.
    """
    if not any(isinstance(value, list) for value in values):
        return "[" + ", ".join(format_toml_value(value, indent) for value in values) + "]"
    child_indent = " " * (indent + 4)
    current_indent = " " * indent
    lines = ["["]
    for value in values:
        lines.append(f"{child_indent}{format_toml_value(value, indent + 4)},")
    lines.append(f"{current_indent}]")
    return "\n".join(lines)


def parse_python_code(question_data: dict[str, Any]) -> str:
    """Parse the Python3 snippet from raw question data.

    Args:
        question_data: Raw question data from LeetCode.

    Returns:
        Python3 code snippet text.

    Raises:
        LeetCodeClientError: If no Python3 snippet is available.
    """
    snippets = question_data.get("codeSnippets")
    if not isinstance(snippets, list):
        raise LeetCodeClientError("question data does not include code snippets")
    for snippet in snippets:
        if not isinstance(snippet, dict):
            continue
        if snippet.get("langSlug") == "python3":
            code = snippet.get("code")
            if isinstance(code, str) and code.strip():
                return code
    raise LeetCodeClientError("question does not include a Python3 code snippet")


def parse_entrypoint_from_python_code(python_code: str) -> str:
    """Parse the LeetCode solution method name from Python code.

    Args:
        python_code: Python3 code snippet.

    Returns:
        Solution method name.

    Raises:
        LeetCodeClientError: If no method definition is found.
    """
    solution_match = re.search(r"^class\s+Solution\s*[:(]", python_code, re.MULTILINE)
    if solution_match is None:
        raise LeetCodeClientError("could not find a Solution method in the Python3 snippet")
    solution_body = python_code[solution_match.end():]
    next_class_match = re.search(r"^class\s+[A-Za-z_][A-Za-z0-9_]*\s*[:(]", solution_body, re.MULTILINE)
    if next_class_match is not None:
        solution_body = solution_body[: next_class_match.start()]
    match = re.search(r"^\s{4}def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", solution_body, re.MULTILINE)
    if match is None:
        raise LeetCodeClientError("could not find a Solution method in the Python3 snippet")
    return match.group(1)


def parse_class_name_from_python_code(python_code: str) -> str:
    """Parse the top-level class name from a Python operations snippet.

    Args:
        python_code: Python3 code snippet.

    Returns:
        Top-level class name.

    Raises:
        LeetCodeClientError: If no class definition is found.
    """
    match = re.search(r"^class\s+([A-Za-z_][A-Za-z0-9_]*)\s*[:(]", python_code, re.MULTILINE)
    if match is None:
        raise LeetCodeClientError("could not find a class in the Python3 snippet")
    return match.group(1)


def parse_parameter_names(question_data: dict[str, Any], entrypoint: str) -> list[str]:
    """Parse positional parameter names for the solution method.

    Args:
        question_data: Raw question data from LeetCode.
        entrypoint: Parsed Python solution method name.

    Returns:
        Parameter names in call order, excluding ``self``.
    """
    metadata = question_data.get("metaData")
    if isinstance(metadata, str) and metadata.strip():
        try:
            parsed_metadata = json.loads(metadata)
        except json.JSONDecodeError:
            parsed_metadata = None
        if isinstance(parsed_metadata, dict):
            params = parsed_metadata.get("params")
            if isinstance(params, list):
                names = [
                    param.get("name")
                    for param in params
                    if isinstance(param, dict) and isinstance(param.get("name"), str)
                ]
                if names:
                    return names

    python_code = parse_python_code(question_data)
    method_match = re.search(
        rf"^\s{{4}}def\s+{re.escape(entrypoint)}\s*\(([^)]*)\)",
        python_code,
        re.MULTILINE,
    )
    if method_match is None:
        return []
    raw_params = [parameter.strip() for parameter in method_match.group(1).split(",")]
    return [parameter.split(":", 1)[0].strip() for parameter in raw_params if parameter != "self"]


def parse_required_string(question_data: dict[str, Any], key: str) -> str:
    """Parse a required string field from question data.

    Args:
        question_data: Raw question data.
        key: Required field name.

    Returns:
        String field value.

    Raises:
        LeetCodeClientError: If the field is missing or empty.
    """
    value = question_data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise LeetCodeClientError(f"question data is missing {key}")
    return value


def parse_examples(
    content_html: str,
    parameter_names: list[str],
    case_mode: str = CASE_MODE_NORMAL,
) -> list[dict[str, Any]]:
    """Parse LeetCode statement examples into TOML case dictionaries.

    Args:
        content_html: LeetCode problem statement HTML.
        parameter_names: Solution parameter names in positional order.
        case_mode: Generated case file mode.

    Returns:
        Case dictionaries compatible with ``tomli_w``.
    """
    text = html_to_text(content_html)
    pattern = re.compile(
        r"Input:?\s*(?P<input>.*?)\s*Output:?\s*(?P<output>.*?)(?:\s*Explanation:?|\s*Example\s+\d+:?|\s*Constraints:?|\Z)",
        re.DOTALL,
    )
    cases: list[dict[str, Any]] = []
    for match in pattern.finditer(text):
        try:
            if case_mode == CASE_MODE_OPERATIONS:
                case = parse_operations_example(
                    match.group("input").strip(),
                    match.group("output").strip(),
                )
            else:
                case_input = parse_example_input(match.group("input").strip(), parameter_names)
                case_output = parse_leetcode_value(match.group("output").strip())
                case = {"input": case_input, "output": case_output}
        except LeetCodeClientError:
            continue
        cases.append(case)
    return cases


def parse_operations_example(raw_input: str, raw_output: str) -> dict[str, Any]:
    """Parse a LeetCode operations example into a case dictionary.

    Args:
        raw_input: Text between ``Input`` and ``Output``.
        raw_output: Text after ``Output``.

    Returns:
        Operation names, input argument arrays, and expected outputs.

    Raises:
        LeetCodeClientError: If the example is not a valid operations case.
    """
    input_lines = [line.strip() for line in raw_input.splitlines() if line.strip()]
    if len(input_lines) < 2:
        raise LeetCodeClientError("operations example input must contain operations and input arrays")
    operations = parse_leetcode_value(input_lines[0])
    inputs = parse_leetcode_value(input_lines[1])
    output = parse_leetcode_value(raw_output)
    if not isinstance(operations, list) or not all(isinstance(operation, str) for operation in operations):
        raise LeetCodeClientError("operations example operation names must be an array of strings")
    if not isinstance(inputs, list) or not all(isinstance(arguments, list) for arguments in inputs):
        raise LeetCodeClientError("operations example input must be an array of argument arrays")
    if not isinstance(output, list):
        raise LeetCodeClientError("operations example output must be an array")
    if len(operations) != len(inputs) or len(operations) != len(output):
        raise LeetCodeClientError("operations example arrays must have matching lengths")
    return {"operations": operations, "input": inputs, "output": output}


def html_to_text(content_html: str) -> str:
    """Convert LeetCode problem statement HTML into compact plain text.

    Args:
        content_html: Problem statement HTML.

    Returns:
        Plain text with preserved example labels.
    """
    text = re.sub(r"(?i)<br\s*/?>", "\n", content_html)
    text = re.sub(r"(?i)</p>|</pre>|</div>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    return re.sub(r"[ \t]+", " ", text)


def parse_example_input(raw_input: str, parameter_names: list[str]) -> list[Any]:
    """Parse a LeetCode example input string into positional arguments.

    Args:
        raw_input: Example input text after ``Input:``.
        parameter_names: Solution parameter names in positional order.

    Returns:
        Positional input values.

    Raises:
        LeetCodeClientError: If the input cannot be parsed.
    """
    assignments = split_top_level(raw_input)
    named_values: dict[str, Any] = {}
    positional_values: list[Any] = []
    for assignment in assignments:
        if "=" in assignment:
            name, raw_value = assignment.split("=", 1)
            named_values[name.strip()] = parse_leetcode_value(raw_value.strip())
        elif assignment.strip():
            positional_values.append(parse_leetcode_value(assignment.strip()))

    if named_values:
        if parameter_names:
            missing = [name for name in parameter_names if name not in named_values]
            if missing:
                raise LeetCodeClientError(f"example input is missing {missing[0]}")
            return [named_values[name] for name in parameter_names]
        return list(named_values.values())
    return positional_values


def split_top_level(raw_value: str) -> list[str]:
    """Split a comma-separated string while respecting brackets and quotes.

    Args:
        raw_value: Raw comma-separated value.

    Returns:
        Top-level segments.
    """
    segments: list[str] = []
    start = 0
    depth = 0
    quote: str | None = None
    for index, char in enumerate(raw_value):
        if quote is not None:
            if char == quote and raw_value[index - 1] != "\\":
                quote = None
            continue
        if char in {'"', "'"}:
            quote = char
        elif char in "[{(":
            depth += 1
        elif char in "]})":
            depth -= 1
        elif char == "," and depth == 0:
            segments.append(raw_value[start:index].strip())
            start = index + 1
    final_segment = raw_value[start:].strip()
    if final_segment:
        segments.append(final_segment)
    return segments


def parse_leetcode_value(raw_value: str) -> Any:
    """Parse a LeetCode literal into a Python value.

    Args:
        raw_value: LeetCode literal text.

    Returns:
        Parsed Python value compatible with TOML serialization.

    Raises:
        LeetCodeClientError: If the literal cannot be parsed.
    """
    normalized = raw_value.strip()
    normalized = re.sub(r"\btrue\b", "True", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\bfalse\b", "False", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"\bnull\b", '"null"', normalized, flags=re.IGNORECASE)
    try:
        return ast.literal_eval(normalized)
    except (SyntaxError, ValueError) as error:
        raise LeetCodeClientError(f"could not parse LeetCode value: {raw_value}") from error
