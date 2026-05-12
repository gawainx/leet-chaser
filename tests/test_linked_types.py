"""Tests for linked-list conversion helpers."""

from leet_chaser.linked_types import (
    build_circular_linked_list,
    build_doubly_linked_list,
    build_linked_list,
    circular_linked_list_to_data,
    doubly_linked_list_to_array,
    linked_list_to_array,
)


def test_build_linked_list_converts_values_to_nodes() -> None:
    """Verify singly linked lists can round-trip to arrays.

    Args:
        None.

    Returns:
        None.
    """
    head = build_linked_list([1, 2, 3])

    assert linked_list_to_array(head) == [1, 2, 3]


def test_build_doubly_linked_list_connects_prev_and_next() -> None:
    """Verify doubly linked nodes keep forward and backward links.

    Args:
        None.

    Returns:
        None.
    """
    head = build_doubly_linked_list([1, 2, 3])

    assert doubly_linked_list_to_array(head) == [1, 2, 3]
    assert head is not None
    assert head.next is not None
    assert head.next.prev is head


def test_build_circular_linked_list_records_cycle_position() -> None:
    """Verify circular linked lists normalize to values and cycle position.

    Args:
        None.

    Returns:
        None.
    """
    head = build_circular_linked_list([3, 2, 0, -4], 1)

    assert circular_linked_list_to_data(head) == {"values": [3, 2, 0, -4], "pos": 1}


def test_empty_linked_lists_convert_to_none() -> None:
    """Verify empty list inputs produce empty linked-list values.

    Args:
        None.

    Returns:
        None.
    """
    assert build_linked_list([]) is None
    assert build_doubly_linked_list([]) is None
    assert build_circular_linked_list([], -1) is None
