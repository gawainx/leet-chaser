"""Shared TOML snippets for generated case files."""

NORMAL_CASE_CONFIG_COMMENTS = """# Optional case configuration.
# Uncomment and adjust these fields when the problem needs them.
# Supported types: raw, linked_list, doubly_linked_list, circular_linked_list, binary_tree.
# input_types = ["raw"]  # One item per input argument; use raw for normal TOML values.
# output_type = "raw"  # Use a supported type when the returned value needs conversion before comparison.
#
# Linked-list example:
# input_types = ["linked_list"]
# output_type = "linked_list"
# input = [[1, 2, 3]]
# output = [3, 2, 1]
#
# Doubly linked-list example:
# input_types = ["doubly_linked_list"]
# output_type = "doubly_linked_list"
# input = [[1, 2, 3]]
# output = [1, 2, 3]
#
# Circular linked-list example:
# input_types = ["circular_linked_list"]
# output_type = "circular_linked_list"
# input = [{ values = [3, 2, 0, -4], pos = 1 }]
# output = { values = [3, 2, 0, -4], pos = 1 }
#
# Binary-tree example:
# input_types = ["binary_tree"]
# output_type = "binary_tree"
# input = [[4, 2, 7, 1, 3, 6, 9]]
# output = [4, 7, 2, 9, 6, 3, 1]
#
# inplace_write = true  # Enable for problems that mutate an input argument instead of returning the answer.
# inplace_index = 0  # Zero-based input argument index compared when inplace_write is true.
# unordered_output = true  # Enable when list output can be returned in any order.
# mode = "operations"  # Alternative mode for design problems; do not combine with entrypoint.

"""

OPERATIONS_CASE_CONFIG_COMMENTS = """# Operations mode case configuration.
# operations, input, and output must have the same length.
# operations[0] must equal class_name and constructs a fresh instance for each case.
# Use "null" in output for constructor or method calls that should return None.

"""
