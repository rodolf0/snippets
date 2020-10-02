#!/usr/bin/env python3
# https://www.hackerrank.com/challenges/equal/problem

import os
import sys

choco_bars = (1, 2, 5)

def equal(choco_dist):
    if all(x == choco_dist[0] for x in choco_dist):
        # we've reached equality
        return True

    for bars in choco_bars:
        for exc in range(len(choco_dist)-1, -1, -1):
            new_choco_dist = []
            for c, chocos in enumerate(choco_dist):
                if exc == c:
                    new_choco_dist.append(chocos)
                else:
                    new_choco_dist.append(chocos + bars)

            #new_choco_dist = [(c + bars if c != exc_idx else c) for c in choco_dist]
            sys.stderr.write(str(new_choco_dist) + '\n')
            if equal(new_choco_dist):
                return True



if __name__ == '__main__':
    results = []
    # Parse input
    n_test_cases = int(input().rstrip())
    for t in range(n_test_cases):
        num_colleagues = int(input().rstrip())
        num_chocolates = list(map(int, input().rstrip().split()))
        results.append(equal(num_chocolates))

    # write output
    #with open(os.environ['OUTPUT_PATH'], 'w') as fptr:
        #fptr.write(str(ways) + '\n')
    for res in results:
        sys.stdout.write(str(res) + '\n')
