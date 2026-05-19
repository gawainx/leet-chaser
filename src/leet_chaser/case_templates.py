"""Shared TOML snippets for generated case files."""

NORMAL_CASE_CONFIG_COMMENTS = """# Optional case configuration.
# Uncomment and adjust these fields when the problem needs them.
# input_types = ["raw"]  # Supported: raw, linked_list, doubly_linked_list, circular_linked_list, binary_tree.
# output_type = "raw"  # Use a supported type when the returned value needs conversion before comparison.
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
