"""Linked-list node types and conversion helpers for LeetCode-style cases."""

from dataclasses import dataclass
from typing import Any


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


LINKED_TYPE_NAMES = frozenset(
    {
        "linked_list",
        "doubly_linked_list",
        "circular_linked_list",
    }
)


def build_linked_list(values: list[Any]) -> ListNode | None:
    """Build a singly linked list from an array of values.

    Args:
        values: Node values in head-to-tail order.

    Returns:
        Head node for the list, or ``None`` when ``values`` is empty.
    """
    head: ListNode | None = None
    tail: ListNode | None = None
    for value in values:
        node = ListNode(value)
        if head is None:
            head = node
        else:
            tail.next = node  # type: ignore[union-attr]
        tail = node
    return head


def build_doubly_linked_list(values: list[Any]) -> DoublyListNode | None:
    """Build a doubly linked list from an array of values.

    Args:
        values: Node values in head-to-tail order.

    Returns:
        Head node for the list, or ``None`` when ``values`` is empty.
    """
    head: DoublyListNode | None = None
    tail: DoublyListNode | None = None
    for value in values:
        node = DoublyListNode(value)
        if head is None:
            head = node
        else:
            tail.next = node  # type: ignore[union-attr]
            node.prev = tail
        tail = node
    return head


def build_circular_linked_list(values: list[Any], pos: int) -> ListNode | None:
    """Build a singly linked list with an optional cycle.

    Args:
        values: Node values in head-to-tail order before the cycle link.
        pos: Index that the tail points to, or ``-1`` for no cycle.

    Returns:
        Head node for the list, or ``None`` when ``values`` is empty.
    """
    head = build_linked_list(values)
    if head is None or pos == -1:
        return head

    nodes: list[ListNode] = []
    current = head
    while current is not None:
        nodes.append(current)
        current = current.next
    nodes[-1].next = nodes[pos]
    return head


def linked_list_to_array(head: ListNode | None) -> list[Any]:
    """Convert a singly linked list to an array.

    Args:
        head: Head node to traverse.

    Returns:
        Node values in traversal order before a repeated node is seen.
    """
    values: list[Any] = []
    seen: set[int] = set()
    current = head
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        values.append(current.val)
        current = current.next
    return values


def doubly_linked_list_to_array(head: DoublyListNode | None) -> list[Any]:
    """Convert a doubly linked list to an array.

    Args:
        head: Head node to traverse.

    Returns:
        Node values in traversal order before a repeated node is seen.
    """
    values: list[Any] = []
    seen: set[int] = set()
    current = head
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        values.append(current.val)
        current = current.next
    return values


def circular_linked_list_to_data(head: ListNode | None) -> dict[str, Any]:
    """Convert a possibly cyclic singly linked list to TOML-friendly data.

    Args:
        head: Head node to traverse.

    Returns:
        A dictionary with ``values`` and ``pos`` keys.
    """
    values: list[Any] = []
    node_indexes: dict[int, int] = {}
    current = head
    while current is not None:
        node_id = id(current)
        if node_id in node_indexes:
            return {"values": values, "pos": node_indexes[node_id]}
        node_indexes[node_id] = len(values)
        values.append(current.val)
        current = current.next
    return {"values": values, "pos": -1}


def normalize_linked_value(value: Any, value_type: str) -> Any:
    """Normalize a linked-list value to a comparable Python structure.

    Args:
        value: Linked-list value returned by a solution or parsed from TOML.
        value_type: Advanced case type name.

    Returns:
        A list or dictionary that can be compared and displayed.
    """
    if value_type == "linked_list":
        return linked_list_to_array(value)
    if value_type == "doubly_linked_list":
        return doubly_linked_list_to_array(value)
    if value_type == "circular_linked_list":
        return circular_linked_list_to_data(value)
    return value
