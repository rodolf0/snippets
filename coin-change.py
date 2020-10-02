#!/usr/bin/env python3

# https://www.hackerrank.com/challenges/coin-change/problem

# It must return an integer denoting the number of ways to make change.
# getWays has the following parameter(s):
#    n: an integer, the amount to make change for
#    c: an array of integers representing available denominations

# Example input
# echo -e '10 4\n2 5 3 6'
# echo -e '4 3\n1 2 3'

import os
import sys

from collections import defaultdict


# Recursive way ... blows up the stack or times out
def makeChange2(upto_change, coins):
    ways = set()
    if upto_change > 0:
        for c in coins:
            if c == upto_change:
                # exact change
                ways.add((c,))
            elif c < upto_change:
                for part in makeChange2(upto_change - c, coins):
                    new_way = tuple(sorted((c,) + part))
                    ways.add(new_way)
    return ways


# Non recursive ... doesn't blowup stack but runs out of memory for big upto_change
def makeChange3(upto_change, coins):
    ways = defaultdict(set)
    for upto in range(1, upto_change + 1):
        for c in coins:
            if upto < c:
                # this coin is too large to make change
                continue
            if upto == c:
                # perfect change
                ways[upto].add((c,))
            elif upto > c:
                # need to get more change ... check smaller ways
                for w in ways[upto - c]:
                    new_way = tuple(sorted((c,) + w))
                    ways[upto].add(new_way)
    return ways[upto_change]


# still blows up :-( timeout
def makeChange4(upto_change, coins):
    # Idea: use dict to represent a single way to make change so that large
    # sequences don't use so much mem, ie: each combo has a fixed dict size
    # ways = {upto: set({c1: x-many, c2: y-many}, {...})}

    def make_count(coin_count):
        return tuple(coin_count.get(c, 0) for c in coins)

    max_coin = max(coins)

    ways = defaultdict(set)
    for upto in range(1, upto_change + 1):

        # put upper cap on space state, no need to look further back
        if upto > max_coin:
            del ways[upto - max_coin]

        for idx, c in enumerate(coins):
            if upto < c:
                # this coin is too large to make change
                continue
            if upto == c:
                # perfect change
                ways[upto].add(make_count({c: 1}))
            elif upto > c:
                # need to get more change ... check smaller ways
                for w in ways[upto - c]:
                    # w is each way to make change for (upto - c)
                    new_way = tuple(cnt if i != idx else cnt + 1 for i, cnt in enumerate(w))
                    ways[upto].add(new_way)
    return ways[upto_change]


# Non distinct ways
memo = {}
def makeChange5(upto_change, coins):
    # base case if remainder is 0, then there's a way
    # only 1 way to make change for 0 ... no coins
    if upto_change == 0:
        return 1
    # this path doesn't lead to exact change
    if upto_change < 0 or len(coins) == 0:
        return 0

    # If you don't care about distinct ways could just return
    # But want to deduplicate cases like (1 1 2) and (1 2 1)
    # return sum(makeChange5(upto_change - c, coins) for c in coins)

    if (upto_change, coins) not in memo:
        # sum ways to make change
        # we'll pick coin-0 and see how many ways we can make change with and without that coin
        including_coin = makeChange5(upto_change - coins[0], coins)
        excluding_coin = makeChange5(upto_change, coins[1:])
        memo[(upto_change, coins)] = including_coin + excluding_coin

    return memo[(upto_change, coins)]


def getWays(n, coins):
    coins = tuple(coins)
    ways = makeChange5(n, coins)
    sys.stderr.write(str(ways) + '\n')
    return ways
    #return len(ways)


if __name__ == '__main__':
    # Parse input
    first_multiple_input = input().rstrip().split()
    n = int(first_multiple_input[0])
    m = int(first_multiple_input[1])
    c = list(map(int, input().rstrip().split()))
    # Print the number of ways of making change for 'n' units using coins having the values given by 'c'
    ways = getWays(n, c)
    # write output
    sys.stdout.write(str(ways) + '\n')
    #with open(os.environ['OUTPUT_PATH'], 'w') as fptr:
        #fptr.write(str(ways) + '\n')
