#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Исправленная копия dz01-ai-code.py (ДЗ 1, пункт 8): случайный опорный (Д2)
# и список equal для элементов, равных опорному (Д1); остальное — как у ИИ.
"""Fast sorting utilities.

Quicksort with a random pivot and three-way partition.
Expected time complexity: O(n log n) for any input.
"""

from __future__ import annotations

import random


def quicksort(data: list[int]) -> list[int]:
    """Sort a list of integers using the quicksort algorithm.

    Divide-and-conquer with a random pivot and three-way partition into
    elements less than, equal to and greater than the pivot.
    Expected time complexity: O(n log n) for any input order (expectation
    over the random pivot choices); the worst case O(n^2) is still possible
    but extremely unlikely. Expected recursion depth: O(log n).
    Extra memory: O(n) for the new lists (O(n^2) in the worst case).
    The input list is not modified; a new sorted list is returned.

    Examples
    --------
    >>> quicksort([3, 1, 2])
    [1, 2, 3]
    >>> quicksort([])
    []
    >>> quicksort([3, 1, 3, 1])
    [1, 1, 3, 3]
    """
    if len(data) <= 1:
        return list(data)
    pivot = random.choice(data)
    smaller = [x for x in data if x < pivot]
    equal = [x for x in data if x == pivot]
    larger = [x for x in data if x > pivot]
    return quicksort(smaller) + equal + quicksort(larger)


if __name__ == "__main__":
    example = [5, 2, 9, 1, 7]
    print("Input :", example)
    print("Sorted:", quicksort(example))
