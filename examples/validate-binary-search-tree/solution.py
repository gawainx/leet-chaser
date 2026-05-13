"""LeetCode 98. Validate Binary Search Tree example solution."""

from typing import Any


class Solution:
    """Solve Validate Binary Search Tree with recursive value bounds."""

    def isValidBST(self, root: Any) -> bool:
        """Return whether a binary tree satisfies binary search tree ordering.

        Args:
            root: Root node of the binary tree, or ``None`` for an empty tree.

        Returns:
            True when every node value is within its valid lower and upper bound.
        """
        return self._is_valid_node(root, float("-inf"), float("inf"))

    def _is_valid_node(self, node: Any, lower: float, upper: float) -> bool:
        """Validate one subtree using exclusive value bounds.

        Args:
            node: Current tree node, or ``None`` for an empty subtree.
            lower: Exclusive lower bound for the node value.
            upper: Exclusive upper bound for the node value.

        Returns:
            True when the subtree is a valid binary search tree.
        """
        if node is None:
            return True
        if not lower < node.val < upper:
            return False
        return self._is_valid_node(node.left, lower, node.val) and self._is_valid_node(
            node.right,
            node.val,
            upper,
        )
