"""Fetch public LeetCode problem data for init templates."""

from __future__ import annotations

import ast
import html
import json
import re
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import tomli_w

GRAPHQL_URL = "https://leetcode.com/graphql"
REQUEST_TIMEOUT_SECONDS = 10


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
    entrypoint = parse_entrypoint_from_python_code(python_code)
    return LeetCodeQuestionMetadata(
        question_number=question_number,
        title=parse_required_string(question_data, "title"),
        title_slug=parse_required_string(question_data, "titleSlug"),
        entrypoint=entrypoint,
        python_code=python_code,
        content_html=parse_required_string(question_data, "content"),
        parameter_names=parse_parameter_names(question_data, entrypoint),
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
    data = post_graphql(payload)
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
    raise LeetCodeClientError(f"question {question_number} was not found")


def fetch_question_data(title_slug: str) -> dict[str, Any]:
    """Fetch public question data by LeetCode title slug.

    Args:
        title_slug: LeetCode question slug.

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
    data = post_graphql({"query": query, "variables": {"titleSlug": title_slug}})
    question = data.get("data", {}).get("question")
    if not isinstance(question, dict):
        raise LeetCodeClientError(f"question data for {title_slug} was not found")
    return question


def post_graphql(payload: dict[str, Any]) -> dict[str, Any]:
    """Post a JSON GraphQL request to LeetCode.

    Args:
        payload: GraphQL query and variables.

    Returns:
        Parsed JSON response.

    Raises:
        LeetCodeClientError: If the request or response fails.
    """
    body = json.dumps(payload).encode("utf-8")
    request = Request(
        GRAPHQL_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "leet-chaser",
            "Referer": "https://leetcode.com/problemset/",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            raw_response = response.read().decode("utf-8")
    except HTTPError as error:
        raise LeetCodeClientError(f"LeetCode returned HTTP {error.code}") from error
    except URLError as error:
        raise LeetCodeClientError(f"could not reach LeetCode: {error.reason}") from error
    except TimeoutError as error:
        raise LeetCodeClientError("LeetCode request timed out") from error

    try:
        data = json.loads(raw_response)
    except json.JSONDecodeError as error:
        raise LeetCodeClientError("LeetCode returned invalid JSON") from error

    if data.get("errors"):
        raise LeetCodeClientError("LeetCode returned a GraphQL error")
    if not isinstance(data, dict):
        raise LeetCodeClientError("LeetCode returned an invalid response")
    return data


def build_remote_init_files(metadata: LeetCodeQuestionMetadata) -> RemoteInitFiles:
    """Build init file contents from public LeetCode metadata.

    Args:
        metadata: Public LeetCode question metadata.

    Returns:
        Directory name and file text for init.

    Raises:
        LeetCodeClientError: If no runnable examples can be generated.
    """
    cases = parse_examples(metadata.content_html, metadata.parameter_names)
    if not cases:
        raise LeetCodeClientError(
            f"could not parse examples for question {metadata.question_number}"
        )

    case_data = {"entrypoint": metadata.entrypoint, "cases": cases}
    question_prefix = f"lt{metadata.question_number:03d}"
    return RemoteInitFiles(
        directory_name=f"{question_prefix}.{metadata.entrypoint}",
        solution_text=metadata.python_code.rstrip() + "\n",
        case_text=tomli_w.dumps(case_data),
    )


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
    match = re.search(r"^\s{4}def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", python_code, re.MULTILINE)
    if match is None:
        raise LeetCodeClientError("could not find a Solution method in the Python3 snippet")
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


def parse_examples(content_html: str, parameter_names: list[str]) -> list[dict[str, Any]]:
    """Parse LeetCode statement examples into TOML case dictionaries.

    Args:
        content_html: LeetCode problem statement HTML.
        parameter_names: Solution parameter names in positional order.

    Returns:
        Case dictionaries compatible with ``tomli_w``.
    """
    text = html_to_text(content_html)
    pattern = re.compile(
        r"Input:\s*(?P<input>.*?)\s*Output:\s*(?P<output>.*?)(?:\s*Explanation:|\s*Example\s+\d+:|\s*Constraints:|\Z)",
        re.DOTALL,
    )
    cases: list[dict[str, Any]] = []
    for match in pattern.finditer(text):
        try:
            case_input = parse_example_input(match.group("input").strip(), parameter_names)
            case_output = parse_leetcode_value(match.group("output").strip())
        except LeetCodeClientError:
            continue
        cases.append({"input": case_input, "output": case_output})
    return cases


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
