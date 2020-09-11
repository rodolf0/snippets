#!/usr/bin/env python
# https://algodaily.com/lessons/memoization-in-dynamic-programming/finding-the-interval-set?view=article

from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Interval:
    start: int
    end: int
    weight: float
    # By default the predecesor is the root
    # NIT: instead of actual intervals could array ala entity-component-system
    predecesor: Optional['Interval'] = None
    chain_value: float = 0.0


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
    # Sort intervals by end time so new intervals don't invalidate current paths
    intervals = sorted(intervals, key=lambda it: it.end)
    heads: List[Interval] = [Interval(0, 0, 0.0)]

    # Loop through end-time sorted intervals
    # 1. Start-time of interval must be greater than chain's end,
    #    otherwise need to find a previous fork-point and have a new head.
    # 2. If going back to fork a chain, need to verify new weight is greater.

    for interval_idx, interval in enumerate(intervals):
        current_heads = heads.copy()  # Get a copy of heads for this iteration
        for head_idx, chain_head in enumerate(current_heads):
            chain_cursor = chain_head
            # Search for point in the chain where interval doesn't overlap
            while interval.start < chain_cursor.end:
                assert chain_cursor.predecesor is not None, "BUG"
                chain_cursor = chain_cursor.predecesor
            assert interval.start >= chain_cursor.end, "BUG"

            new_chain_value = chain_cursor.chain_value + interval.weight

            # Check if interval adds any value, else discard it
            if new_chain_value > chain_head.chain_value:
                new_head = Interval(
                    start=interval.start,
                    end=interval.end,
                    weight=interval.weight,
                    predecesor=chain_cursor,
                    chain_value=new_chain_value,
                )
                if chain_head == chain_cursor:
                    # Can insert at the tip of the chain
                    heads[head_idx] = new_head
                else:
                    # Append new head
                    heads.append(new_head)
    return heads


if __name__ == "__main__":
    from pprint import pprint
    heads = schedule_attempt2([
        Interval(1,  10,  5.0),
        Interval(7,  14, 15.0),
        Interval(12, 25, 20.0),
        Interval(30, 32,  3.0),
        Interval(28, 35,  1.0),
    ])
    pprint(heads)
    best = max(heads, key=lambda h: h.chain_value)
    print(f"Best chain {best}")
