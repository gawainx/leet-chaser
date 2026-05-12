# Unordered Output Comparison Plan

## Phase 1: Case Metadata

- Status: Finished
- Task: Add `unordered_output` to parsed and written case files.
- Implementation: Added a `CaseFile` boolean field, TOML parser validation, and writer round-trip support.
- Expected Tests: Case-file parsing, writing, and non-boolean rejection pass.

## Phase 2: Runner Comparison

- Status: Finished
- Task: Use `unordered_output = true` to compare list outputs without depending on element order.
- Implementation: Added comparison helpers that recursively convert list and dict values into stable keys before comparison.
- Expected Tests: Three-sum style reordered output passes; missing output item fails; default ordered comparison remains strict.

## Phase 3: Documentation

- Status: Finished
- Task: Document the new case metadata for users.
- Implementation: Updated README and TOML case docs, and added a design document with scope and validation notes.
- Expected Tests: Documentation examples use valid TOML syntax.
