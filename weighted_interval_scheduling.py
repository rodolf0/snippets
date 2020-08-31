#!/usr/bin/env python
# https://algodaily.com/lessons/memoization-in-dynamic-programming/finding-the-interval-set?view=article

from typing import List, NamedTuple

class Interval(NamedTuple):
    start: int
    end: int
    weight: float


def schedule_attempt1(intervals: List[Interval]) -> List[Interval]:
    """Find non-overlapping intervals that maximize total weight"""

    total_weight = 0.0
    result: List[Interval] = []

    for interval in intervals:
        # Find the last item in result where there's no overlap with this test 'interval'
        discard_iterator = len(result) - 1
        while discard_iterator >= 0 and interval.start <= result[discard_iterator].end:
            discard_iterator -= 1

        # check what's the new weight once we nullify up to discard_iterator
        discount_value = sum(result[i].weight for i in range(discard_iterator + 1, len(result)))

        validate_weight = total_weight - discount_value + interval.weight

        # check if taking this interval in replacement of everything nulified is better
        if validate_weight > total_weight:
            result = result[:discard_iterator+1] + [interval]
            total_weight = validate_weight

    ## NOTE: PROBLEM with this approach is that it doesn't recover previously discarded intervals
    ##       that overlapped with the ones we're discarding right now.

    return result

def schedule_attempt2(intervals: List[Interval]) -> List[Interval]:
    """Find non-overlapping intervals that maximize total weight"""


if __name__ == "__main__":
    from pprint import pprint
    s = schedule_attempt2([
        Interval(1,  10,  5.0),
        Interval(7,  14, 15.0),
        Interval(12, 25, 20.0),
        Interval(30, 32,  3.0),
        Interval(28, 35,  1.0),
    ])
    pprint(s)