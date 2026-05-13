"""Binary-tree node types and conversion helpers for LeetCode-style cases."""

from collections import deque
from typing import Any

from leet_chaser.lt_typing import TreeNode

BINARY_TREE_TYPE_NAME = "binary_tree"
TREE_NULL_VALUE = "null"
TREE_TYPE_NAMES = frozenset({BINARY_TREE_TYPE_NAME})


def build_binary_tree(values: list[Any]) -> TreeNode | None:
    """Build a binary tree from a LeetCode level-order array.

    Args:
        values: Level-order node values where ``"null"`` marks a missing child.

    Returns:
        Root node for the tree, or ``None`` when ``values`` is empty.

    Raises:
        ValueError: If the root value is ``"null"`` while more values remain.
    """
    if not values:
        return None
    if _is_tree_null(values[0]):
        if len(values) == 1:
            return None
        raise ValueError("binary tree root cannot be null when child values exist")

    root = TreeNode(values[0])
    parents: deque[TreeNode] = deque([root])
    value_index = 1
    while parents and value_index < len(values):
        parent = parents.popleft()

        left_value = values[value_index]
        value_index += 1
        if not _is_tree_null(left_value):
            parent.left = TreeNode(left_value)
            parents.append(parent.left)

        if value_index >= len(values):
            break
        right_value = values[value_index]
        value_index += 1
        if not _is_tree_null(right_value):
            parent.right = TreeNode(right_value)
            parents.append(parent.right)

    return root


def binary_tree_to_array(root: TreeNode | None) -> list[Any]:
    """Convert a binary tree to a trimmed LeetCode level-order array.

    Args:
        root: Root node to traverse.

    Returns:
        Level-order values with missing children represented by ``"null"`` and
        trailing null markers removed.
    """
    if root is None:
        return []

    values: list[Any] = []
    queue: deque[TreeNode | None] = deque([root])
    while queue:
        node = queue.popleft()
        if node is None:
            values.append(TREE_NULL_VALUE)
            continue
        values.append(node.val)
        queue.append(node.left)
        queue.append(node.right)

    while values and _is_tree_null(values[-1]):
        values.pop()
    return values


def normalize_tree_value(value: Any, value_type: str) -> Any:
    """Normalize a tree value to a comparable Python structure.

    Args:
        value: Tree value returned by a solution or parsed from TOML.
        value_type: Advanced case type name.

    Returns:
        A level-order array when ``value_type`` is ``binary_tree``; otherwise
        the original value.
    """
    if value_type == BINARY_TREE_TYPE_NAME:
        return binary_tree_to_array(value)
    return value


def _is_tree_null(value: Any) -> bool:
    """Return whether a level-order value marks a missing tree node.

    Args:
        value: Raw level-order array item.

    Returns:
        True when the value is the supported missing-node marker.
    """
    return value == TREE_NULL_VALUE
