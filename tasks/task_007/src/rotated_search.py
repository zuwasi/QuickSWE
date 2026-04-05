"""
Binary Search on a Rotated Sorted Array.

A sorted array may be rotated at an unknown pivot point. For example,
[0,1,2,4,5,6,7] might become [4,5,6,7,0,1,2]. This module provides
a function to search for a target value in O(log n) time.
"""


def search(nums, target):
    """Search for a target in a rotated sorted array.

    The array was originally sorted in ascending order, then rotated
    at some pivot index. All elements are unique.

    Args:
        nums: List of unique integers, sorted then rotated.
        target: The integer value to search for.

    Returns:
        The index of target if found, otherwise -1.
    """
    if not nums:
        return -1

    left, right = 0, len(nums) - 1

    while left <= right:
        mid = (left + right) // 2

        if nums[mid] == target:
            return mid

        # Check if the left half is sorted
        if nums[left] <= nums[mid]:
            # Target is in the left sorted half
            if nums[left] < target < nums[mid]:
                right = mid - 1
            else:
                left = mid + 1
        else:
            # Right half is sorted
            if nums[mid] < target <= nums[right]:
                left = mid + 1
            else:
                right = mid - 1

    return -1


def find_rotation_point(nums):
    """Find the index of the minimum element (rotation pivot).

    Args:
        nums: A rotated sorted array of unique integers.

    Returns:
        The index of the smallest element.
    """
    if not nums:
        return -1

    left, right = 0, len(nums) - 1

    while left < right:
        mid = (left + right) // 2
        if nums[mid] > nums[right]:
            left = mid + 1
        else:
            right = mid

    return left


def search_with_duplicates(nums, target):
    """Search in a rotated sorted array that may contain duplicates.

    This is a slower variant (worst case O(n)) that handles duplicates.

    Args:
        nums: List of integers (may have duplicates), sorted then rotated.
        target: The integer to find.

    Returns:
        True if target is found, False otherwise.
    """
    if not nums:
        return False

    left, right = 0, len(nums) - 1

    while left <= right:
        mid = (left + right) // 2

        if nums[mid] == target:
            return True

        if nums[left] == nums[mid] == nums[right]:
            left += 1
            right -= 1
        elif nums[left] <= nums[mid]:
            if nums[left] <= target < nums[mid]:
                right = mid - 1
            else:
                left = mid + 1
        else:
            if nums[mid] < target <= nums[right]:
                left = mid + 1
            else:
                right = mid - 1

    return False
