# Leet-Chaser

Leet-Chaser is a command-line tool for running LeetCode-style Python solutions locally. It keeps `solution.py` and `cases.toml` in the same problem directory, so you can run examples, add local cases, and debug one case without leaving your editor.

It supports regular function problems, linked lists, binary trees, in-place mutations, unordered outputs, and operation-sequence design problems such as LRU Cache.

中文文档: [README.md](README.md)

## Installation

Install with pip:

```shell
python -m pip install leet-chaser
leet-chaser --help
```

Use `uvx` when you do not want to install it into the current environment:

```shell
uvx leet-chaser --help
uvx leet-chaser init two-sum
uvx leet-chaser run two-sum
```

Inside this repository, use:

```shell
uv run leet-chaser --help
```

## Quick Start

Create a problem directory:

```shell
leet-chaser init two-sum
```

Generated files:

```text
two-sum/
├── solution.py
└── cases.toml
```

Write `solution.py`:

```python
from typing import List


class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        seen = {}
        for index, num in enumerate(nums):
            rest = target - num
            if rest in seen:
                return [seen[rest], index]
            seen[num] = index
        return []
```

Edit `cases.toml`:

```toml
entrypoint = "twoSum"

[[cases]]
input = [[2, 7, 11, 15], 9]
output = [0, 1]

[[cases]]
input = [[3, 2, 4], 6]
output = [1, 2]
```

Run the cases:

```shell
leet-chaser run two-sum
```

By default, the command runs `<problem-dir>/solution.py`. You can choose another entry file, and the argument does not need a `.py` suffix because the command completes it automatically:

```shell
leet-chaser run two-sum -e slv.py
leet-chaser run two-sum --entry slv_enhanced.py
leet-chaser run two-sum -e slv
```

## Initialize From a LeetCode Question Number

You can initialize from a public LeetCode question number. The command fetches the Python3 snippet and statement examples without login, OAuth, or cookies:

```shell
leet-chaser init -q 1
leet-chaser init --question-number 1
```

The default directory name is `lt{zero-padded question number}.{entrypoint}`:

```text
lt001.twoSum/
├── solution.py
└── cases.toml
```

You can override the directory name:

```shell
leet-chaser init custom-two-sum -q 1
```

The command prints progress while it fetches the question number, loads question details, generates local files, and writes them. Failures include the failing stage and reason, such as missing public problem, paid-only problem, GraphQL schema changes, network errors, or unparseable examples.

## Init Templates

Use `-t/--type` to create a TOML template for common problem shapes:

```shell
leet-chaser init reverse-list -t linklist
leet-chaser init validate-bst -t bitree
leet-chaser init level-order -t tree
leet-chaser init search-matrix -t matrix
```

Common aliases:

- `linklist`, `linked_list`, and `listnode` create a linked-list template.
- `bitree`, `binary_tree`, `tree`, and `treenode` create a binary-tree template.
- `matrix`, `grid`, and `2d-array` create a two-dimensional array template.

`-q/--question-number` and `-t/--type` cannot be used together because question-number initialization generates concrete cases from the problem statement.

## Case File Format

Regular function problems use a top-level `entrypoint` field for the method name on `Solution`. Each `[[cases]]` table has `input` as positional arguments and `output` as the expected return value:

```toml
entrypoint = "twoSum"

[[cases]]
input = [[2, 7, 11, 15], 9]
output = [0, 1]
```

Single-argument problems still wrap the argument in an array:

```toml
entrypoint = "isPalindrome"

[[cases]]
input = [121]
output = true
```

## Advanced Types

Linked-list problems can convert arrays into node objects with type metadata:

```toml
entrypoint = "reverseList"
input_types = ["linked_list"]
output_type = "linked_list"

[[cases]]
input = [[1, 2, 3]]
output = [3, 2, 1]
```

Binary-tree problems can use LeetCode level-order arrays. Empty children are written as the string `"null"`:

```toml
entrypoint = "isValidBST"
input_types = ["binary_tree"]

[[cases]]
input = [[5, 1, 4, "null", "null", 3, 6]]
output = false
```

You can import built-in node types in your solution:

```python
from leet_chaser.lt_typing import ListNode, TreeNode
```

See [docs/advanced-case-types.md](docs/advanced-case-types.md) for singly linked lists, doubly linked lists, circular linked lists, and binary trees.

## In-Place Mutation and Unordered Output

For in-place array mutation problems, compare a mutated input argument instead of the return value:

```toml
entrypoint = "moveZeroes"
inplace_write = true
inplace_index = 0

[[cases]]
input = [[0, 1, 0, 3, 12]]
output = [1, 3, 12, 0, 0]
```

`inplace_index` is 0-based. When `inplace_write` is enabled, the return value is ignored. If the solution returns a non-`None` value, the CLI prints a warning.

For problems such as 3Sum where output order does not matter, enable recursive unordered comparison:

```toml
entrypoint = "threeSum"
unordered_output = true

[[cases]]
input = [[-1, 0, 1, 2, -1, -4]]
output = [[-1, -1, 2], [-1, 0, 1]]
```

## Operations Mode for Design Problems

Design problems such as LRU Cache, Min Stack, and Trie can use `mode = "operations"`. The format stays close to LeetCode examples, so it is easy to copy from the statement:

```toml
mode = "operations"
class_name = "LRUCache"

[[cases]]
operations = ["LRUCache", "put", "put", "get", "put", "get"]
input = [[2], [1, 1], [2, 2], [1], [3, 3], [2]]
output = ["null", "null", "null", 1, "null", -1]
```

Rules:

- `class_name` is the class to instantiate from `solution.py`.
- `operations[0]` must equal `class_name`.
- `input[0]` is used to construct the instance; later inputs are passed to the operation at the same index.
- `operations`, `input`, and `output` must have matching lengths.
- LeetCode `null` is written as `"null"` in TOML and compared as Python `None`.
- Each case creates a fresh instance.

`leet-chaser init -q 146` automatically detects LRU Cache-style problems and generates an operations-mode `cases.toml`.

## Debug One Case

Put the case you want to inspect into `debug.toml`. It uses the same format as `cases.toml`, but should contain exactly one `[[cases]]` table:

```toml
entrypoint = "twoSum"

[[cases]]
input = [[2, 7, 11, 15], 9]
output = [0, 1]
```

The debug command reads `<problem-dir>/debug.toml` by default and prints variable changes line by line:

```shell
leet-chaser debug two-sum
leet-chaser debug two-sum -t seen -t rest
leet-chaser debug two-sum -c two-sum/custom-debug.toml
leet-chaser debug two-sum -e slv
```

The debug command currently targets regular `entrypoint` mode. For operations mode, use `run` output with case, step, and operation context to locate the failing call.

## Built-In Examples

Run LeetCode 1. Two Sum:

```shell
uv run leet-chaser run examples/two-sum
```

Run LeetCode 206. Reverse Linked List:

```shell
uv run leet-chaser run examples/reverse-linked-list
```

Run LeetCode 98. Validate Binary Search Tree:

```shell
uv run leet-chaser run examples/validate-binary-search-tree
```

## More Documentation

- [docs/init-command.md](docs/init-command.md): init command behavior and design.
- [docs/run-command.md](docs/run-command.md): run command behavior and design.
- [docs/debug-command.md](docs/debug-command.md): debug command behavior and design.
- [docs/test-case-toml.md](docs/test-case-toml.md): TOML case format.
- [docs/advanced-case-types.md](docs/advanced-case-types.md): linked lists, binary trees, and other advanced types.
