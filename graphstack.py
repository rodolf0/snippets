#!/usr/bin/env python

from collections import namedtuple

GraphStack = namedtuple("GraphStack", ["data", "ancestors"])

def depth_first_recursive(stack, start):
    "Yield stacks encoded in the graph-stack"
    if len(stack.ancestors[start]) == 0:
        yield [stack.data[start]]
    for a in stack.ancestors[start]:
        # each ancestor may have multiple ancestors itself
        # we'll need to yield a stack for each one of those
        for x in depth_first_recursive(stack, a):
            yield [stack.data[start]] + x


def depth_first_iterative(stack, start):
    "Yield stacks encoded in the graph-stack"
    Cursor = namedtuple("Cursor", ["node", "child"])

    #import pdb
    #pdb.set_trace()

    unstack = [stack.data[start]]
    cursors = [Cursor(start, 0)]

    while len(cursors) > 0:
        cursor = cursors[-1]

        ancestors = stack.ancestors[cursor.node]
        if len(ancestors) == 0:
            # hit bottom of the stack, yield it
            yield unstack
            # Advance iterator
            while len(cursors) > 0:
                cursor = cursors[-1]
                if cursor.child + 1 < len(stack.ancestors[cursor.node]):
                    cursors[-1] = Cursor(cursor.node, cursor.child + 1)
                    break
                cursors.pop()
                #unstack.pop()  # called here or truncated below
            # /Advance iterator/
            # prune the return stack keeping the common bits,
            # discard the elements that belong to different paths
            unstack = unstack[:len(cursors)]
        else:
            a = ancestors[cursor.child]
            unstack.append(stack.data[a])
            # simulate call stack, go 1 level deeper DFS
            cursors.append(Cursor(a, 0))



if __name__ == "__main__":
    stack = GraphStack(
        data=["a", "b", "c", "d", "e", "f", "g", "h"],
        ancestors={0: [], 1: [0], 2: [1], 3: [1], 4: [2, 3], 5: [4], 6: [3, 5], 7: [6]},
    )
    print("iterative:")
    for s in depth_first_iterative(stack, 7):
        print(s)
    print("recursive:")
    for s in depth_first_recursive(stack, 7):
        print(s)
