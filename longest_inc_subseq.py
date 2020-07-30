#!/usr/bin/env python

def lis(sequence):
    # Each item may have more than one ancestor (but of equal path length)
    # Bootstrap ancestors of first item as length 1
    ancestors = {}
    for i, item in enumerate(sequence):
        item_path_len = 1
        candidates = set()
        # Build list of ancestors of item. Check each preceding item as a candidate.
        for j, prev in enumerate(sequence[:i]):
            # for LIS, ancestors need to be strictly less
            if not prev < item: continue
            # Check if j's path is longer than what we've seen so far to use it.
            # If its equally long as we'll track it to print all competing paths.
            j_path_len, _ = ancestors[j]
            if j_path_len + 1 >= item_path_len:
                # Found longer path, clear candidate ancestors to keep max
                if j_path_len + 1 > item_path_len:
                    candidates = set()
                # Update ancestors leading to this item (and increase path)
                item_path_len = j_path_len + 1
                candidates.add(j)
        # Update ancestors for current item
        ancestors[i] = (item_path_len, candidates)
    return ancestors


def unwind(sequence, ancestors):
    from pprint import pprint
    pprint(ancestors)
    # Get the item ending in the last
    argmax = max(ancestors.items(), key=lambda k: k[1][0])
    argmax, (path_length, back_pointers) = argmax

    print(f"Longest increasing subsequence length={path_length}")
    seq = [sequence[argmax]]
    while len(back_pointers) > 0:
        for bp in back_pointers:
            seq.insert(0, sequence[bp])
            (_, back_pointers) = ancestors[bp]
            # TODO: only prints a single path, check graphstack.py
            break
    print(f"seq={seq}")


# ./longest_inc_subseq.py 1 3 5 2 4 3 4 5 4
if __name__ == "__main__":
    import sys
    sequence = sys.argv[1:]
    ancestors = lis(sequence)
    unwind(sequence, ancestors)
    sys.exit(0)
    # alternative to unwind
    for stack in GraphStack(ancestors, sequence):
        print(stack)
