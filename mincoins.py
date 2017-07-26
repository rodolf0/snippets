#!/usr/bin/env python
import sys
from collections import defaultdict

def min_coins(coin_values, coin_sum):
    # map from sum -> num coins
    bestsum = {0: 0}
    # map from sum -> coin-value added to get to this sum
    coinmap = {0: 0}

    for s in range(1, coin_sum + 1):
        for cv in coin_values:
            # we're going to add a coin with value 'cv' check if there's a way
            # to compose sum 's' by adding 'cv' to a previous sum
            if s-cv not in bestsum:
                continue
            # check if building sum 's' with 'cv' requires less coins than konwn
            if s not in bestsum or bestsum[s] > bestsum[s-cv] + 1:
                bestsum[s] = bestsum[s-cv] + 1
                coinmap[s] = cv

    # collect number of coins of each value needed for the sum
    coinset = defaultdict(int)
    while coin_sum > 0:
        cv = coinmap[coin_sum]
        coinset[cv] += 1
        coin_sum -= cv

    return coinset

if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.stderr.write("usage: mincoins <Cv1,Cv2,..> <sum>\n")
        sys.exit(1)
    coin_values = map(int, sys.argv[1].split(","))
    coin_sum = int(sys.argv[2])
    coins = min_coins(coin_values, coin_sum)
    for cv, count in coins.items():
        print("Coin-%d: %d" % (cv, count))
    print("Num coins: %d" % sum(coins.values()))
