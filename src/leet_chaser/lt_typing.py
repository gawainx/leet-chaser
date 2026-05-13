"""Reusable LeetCode-style node classes for local solutions."""

from dataclasses import dataclass
from typing import Any

__all__ = ["DoublyListNode", "ListNode", "TreeNode"]


@dataclass(eq=False)
class ListNode:
    """A LeetCode-style singly linked-list node.

    Attributes:
        val: Value stored in the node.
        next: Next node in the list, or ``None`` for the tail.
    """

    val: Any = 0
    next: "ListNode | None" = None


@dataclass(eq=False)
class DoublyListNode:
    """A LeetCode-style doubly linked-list node.

    Attributes:
        val: Value stored in the node.
        prev: Previous node in the list, or ``None`` for the head.
        next: Next node in the list, or ``None`` for the tail.
    """

    val: Any = 0
    prev: "DoublyListNode | None" = None
    next: "DoublyListNode | None" = None


@dataclass(eq=False)
class TreeNode:
    """A LeetCode-style binary-tree node.

    Attributes:
        val: Value stored in the node.
        left: Left child node, or ``None`` when no left child exists.
        right: Right child node, or ``None`` when no right child exists.
    """

    val: Any = 0
    left: "TreeNode | None" = None
    right: "TreeNode | None" = None
