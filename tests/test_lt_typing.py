"""Tests for public LeetCode-style typing helpers."""

from leet_chaser.linked_types import ListNode as LinkedListNode
from leet_chaser.lt_typing import DoublyListNode, ListNode, TreeNode
from leet_chaser.tree_types import TreeNode as BinaryTreeNode


def test_lt_typing_exports_common_node_classes() -> None:
    """Verify users can import common LeetCode node classes from one module.

    Args:
        None.

    Returns:
        None.
    """
    list_node = ListNode(1)
    doubly_node = DoublyListNode(2)
    tree_node = TreeNode(3)

    assert list_node.val == 1
    assert list_node.next is None
    assert doubly_node.val == 2
    assert doubly_node.prev is None
    assert doubly_node.next is None
    assert tree_node.val == 3
    assert tree_node.left is None
    assert tree_node.right is None


def test_internal_type_modules_reuse_lt_typing_classes() -> None:
    """Verify existing helper modules expose the same public node classes.

    Args:
        None.

    Returns:
        None.
    """
    assert LinkedListNode is ListNode
    assert BinaryTreeNode is TreeNode
