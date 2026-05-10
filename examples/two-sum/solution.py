"""LeetCode 1. Two Sum example solution."""


class Solution:
    """Solve Two Sum with a single-pass hash table."""

    def twoSum(self, nums: list[int], target: int) -> list[int]:
        """Return indices of the two numbers that add up to target.

        Args:
            nums: Input integers containing exactly one valid answer.
            target: Sum that two distinct elements must produce.

        Returns:
            Indices of the two matching numbers.
        """
        seen: dict[int, int] = {}
        for index, num in enumerate(nums):
            complement = target - num
            if complement in seen:
                return [seen[complement], index]
            seen[num] = index
        return []
