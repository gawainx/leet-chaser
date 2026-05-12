"""LeetCode 206. Reverse Linked List example solution."""

from typing import Any


class Solution:
    """Solve Reverse Linked List with iterative pointer rewiring."""

    def reverseList(self, head: Any) -> Any:
        """Reverse a singly linked list.

        Args:
            head: Head node of the linked list, or ``None`` for an empty list.

        Returns:
            Head node of the reversed linked list.
        """
        previous = None
        current = head
        while current is not None:
            next_node = current.next
            current.next = previous
            previous = current
            current = next_node
        return previous
