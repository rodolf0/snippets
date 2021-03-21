#!/usr/bin/env python

import unittest
from typing import List, NamedTuple, Tuple, Dict, FrozenSet, Optional
import functools


class Item(NamedTuple):
    weight: int
    value: float


@functools.lru_cache(maxsize=None)
def ub_knapsack(available_weight: int, items: FrozenSet[Item]) -> float:
    subtree_value: List[float] = [
        i.value + ub_knapsack(available_weight - i.weight, items) for i in items
        if i.weight <= available_weight
    ]
    return max(subtree_value) if len(subtree_value) > 0 else 0.0


def ub_knapsack_i(max_weight: int, items: FrozenSet[Item]) -> float:
    # Build table of best value for weight
    best_value_for_weight = {}
    # NOTE: could take steps of GCD to avoid filling non-needed elements
    for w in range(max_weight + 1):
        best_value_for_weight[w] = 0.0
        for item in items:
            if item.weight <= w:
                best_value_for_weight[w] = max(
                    best_value_for_weight[w],
                    item.value + best_value_for_weight[w - item.weight]
                )
    return best_value_for_weight[max_weight]


class UnboundedKnapSackTest(unittest.TestCase):
    def test_0(self):
        items = frozenset(Item(x, x) for x in (1, 6, 9))
        self.assertEqual(ub_knapsack(12, items), 12)
        self.assertEqual(ub_knapsack_i(12, items), 12)

        items = frozenset(Item(x, x) for x in (3, 4, 4, 4, 8))
        self.assertEqual(ub_knapsack(9, items), 9)
        self.assertEqual(ub_knapsack_i(9, items), 9)

    def test_5(self):
        items = frozenset(Item(x, x) for x in (1,))
        self.assertEqual(ub_knapsack_i(2000, items), 2000)

    def test_11(self):
        items = frozenset(Item(x, x) for x in (3, 7, 9, 11))
        self.assertEqual(ub_knapsack(13, items), 13)
        self.assertEqual(ub_knapsack_i(13, items), 13)

        items = frozenset(Item(x, x) for x in (3, 7, 9))
        self.assertEqual(ub_knapsack(11, items), 10)
        self.assertEqual(ub_knapsack_i(11, items), 10)


def arg_dbg(fn):
    "Decorator to print function arguments"
    def wrapper(*args):
        print(f"{fn.__name__}{args}")
        return fn(*args)
    return wrapper


@functools.lru_cache(maxsize=None)
def knapsack_01(available_weight: int, items: Tuple[Item, ...]) -> float:
    # Top-down approach
    # NOTE: why is it enough to pass items[idx+1:] to subcalls?
    subtree_value: List[float] = []
    for idx, item in enumerate(items):
        if item.weight <= available_weight:
            # Include this item in the knapsack
            subtree_value.append(item.value + knapsack_01(
                available_weight - item.weight, items[idx+1:]))
        else:
            # Exclude this item from the knapsack
            subtree_value.append(knapsack_01(available_weight, items[idx+1:]))
    return max(subtree_value) if len(subtree_value) > 0 else 0.0


def knapsack_01_i(max_capacity: int, items: Tuple[Item, ...]) -> float:
    """
    Given a list of items (with weight and value) check what's the most
    value that can be packed in the knapsack.
    """
    # Bottom-up approach
    # value[(i, capacity)]: Max value that knapsack can hold
    # under 'capacity' when only the first 'i' items are available.
    value: Dict[Tuple[int, int], float] = {
        (0, c): 0.0 for c in range(max_capacity + 1)
    }
    for subset_limit, item in enumerate(items, start=1):
        value[(subset_limit, 0)] = 0.0
        for capacity in range(1, max_capacity + 1):
            value_including_item: float = (
                item.value + value[(subset_limit-1, capacity - item.weight)]
                if item.weight <= capacity
                else 0.0
            )
            value[(subset_limit, capacity)] = max(
                value[(subset_limit-1, capacity)], value_including_item)

    return value[(len(items), max_capacity)]


class BinaryKnapSackTest(unittest.TestCase):
    def test_0(self):
        items = (Item(10, 60), Item(20, 100), Item(30, 120))
        self.assertEqual(knapsack_01(50, items), 220.0)
        self.assertEqual(knapsack_01_i(50, items), 220.0)

    def test_1(self):
        items = (Item(24, 24), Item(10, 18), Item(10, 18), Item(7, 10))
        self.assertEqual(knapsack_01(25, items), 36.0)
        self.assertEqual(knapsack_01_i(25, items), 36.0)

    def test_11(self):
        items = (Item(1, 1), Item(2, 6), Item(3, 10), Item(5, 16))
        self.assertEqual(knapsack_01(7, items), 22.0)
        self.assertEqual(knapsack_01_i(7, items), 22.0)
        self.assertEqual(knapsack_01(6, items), 17.0)
        self.assertEqual(knapsack_01_i(6, items), 17.0)

    def test_2(self):
        items = (Item(10, 100), Item(40, 280), Item(20, 120))
        self.assertEqual(knapsack_01(60, items), 400.0)
        self.assertEqual(knapsack_01_i(60, items), 400.0)

    def test_3(self):
        items = (Item(5, 10), Item(4, 40), Item(6, 30), Item(3, 50))
        self.assertEqual(knapsack_01(10, items), 90.0)
        self.assertEqual(knapsack_01_i(10, items), 90.0)

    def test_4(self):
        items = (Item(2, 1), Item(3, 2), Item(3, 5), Item(4, 9))
        self.assertEqual(knapsack_01(7, items), 14.0)
        self.assertEqual(knapsack_01_i(7, items), 14.0)

    def test_5(self):
        items = (Item(12, 10), Item(13, 20), Item(15, 30), Item(19, 40))
        self.assertEqual(knapsack_01(10, items), 0.0)
        self.assertEqual(knapsack_01_i(10, items), 0.0)

    def test_6(self):
        items = (Item(1, 1), Item(2, 2), Item(3, 3))
        self.assertEqual(knapsack_01(4, items), 4.0)
        items = (Item(1, 3), Item(2, 2), Item(3, 1))
        self.assertEqual(knapsack_01(4, items), 5.0)
        items = (Item(3, 3), Item(2, 2), Item(1, 1))
        self.assertEqual(knapsack_01(4, items), 4.0)
        items = (Item(3, 1), Item(2, 2), Item(1, 3))
        self.assertEqual(knapsack_01(4, items), 5.0)
        items = (Item(1, 1), Item(1, 2), Item(2, 3))
        self.assertEqual(knapsack_01(3, items), 5.0)
        items = (Item(2, 1), Item(1, 2), Item(1, 3))
        self.assertEqual(knapsack_01(3, items), 5.0)
        items = (Item(1, 1), Item(1, 2), Item(1, 3))
        self.assertEqual(knapsack_01(3, items), 6.0)

    def test_7(self):
        items = (
            Item(96, 359), Item(43, 963), Item(28, 465),
            Item(37, 706), Item(92, 146), Item(5, 282),
            Item(3, 828), Item(54, 962), Item(93, 492),
        )
        self.assertEqual(knapsack_01(383, items), 5057.0)
        self.assertEqual(knapsack_01_i(383, items), 5057.0)

    def test_8(self):
        items = (
            Item(4, 468), Item(4, 335), Item(5, 501), Item(2, 170),
            Item(2, 725), Item(4, 479), Item(9, 359), Item(8, 963),
            Item(5, 465), Item(3, 706), Item(8, 146), Item(8, 282),
            Item(10, 828), Item(4, 962), Item(2, 492), Item(10, 996),
            Item(9, 943), Item(7, 828), Item(6, 437), Item(1, 392),
            Item(3, 605), Item(9, 903), Item(7, 154), Item(1, 293),
            Item(3, 383), Item(5, 422), Item(9, 717), Item(7, 719),
            Item(6, 896), Item(1, 448), Item(10, 727), Item(1, 772),
            Item(1, 539), Item(7, 870), Item(2, 913), Item(4, 668),
            Item(9, 300), Item(10, 36), Item(4, 895), Item(5, 704),
            Item(5, 812), Item(7, 323),
        )
        self.assertEqual(knapsack_01(841, items), 24576.0)
        self.assertEqual(knapsack_01_i(841, items), 24576.0)


if __name__ == "__main__":
    unittest.main()
