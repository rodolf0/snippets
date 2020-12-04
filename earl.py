#!/usr/bin/env python

# An Early parser

import itertools
from typing import (
    Callable,
    Generator,
    Iterable,
    Iterator,
    List,
    NamedTuple,
    NewType,
    Optional,
    Set,
    Tuple,
    Union,
    Any,  # NOTE: using this until mypy supports recursive types
)
import unittest


class Symbol(NamedTuple):
    name: str
    pred: Optional[Callable[[str], bool]] = None

    def is_terminal(self) -> bool:
        return self.pred is not None

    def is_nonterm(self) -> bool:
        return self.pred is None


class Rule(NamedTuple):
    head: str
    spec: List[Symbol]

    def __str__(self) -> str:
        body: str = " ".join(s.name for s in self.spec)
        return f"{self.head} -> {body}"


class Grammar(NamedTuple):
    start: str
    rules_: List[Rule]

    def rules(self, start: str) -> List[Rule]:
        return [r for r in self.rules_ if r.head == start]


# What is the source of an item? either a completion, or the scan of a lexeme
BackPointer = Union[Tuple['Item', 'Item'], Tuple['Item', str]]


class Item:
    def __init__(
        self,
        rule: Rule,
        dot: int,
        start: int,
        end: int,
        backpointers: Set[BackPointer]
    ) -> None:
        self.rule: Rule = rule
        self.dot: int = dot
        self.start: int = start
        self.end: int = end
        self.backpointers: Set[BackPointer] = backpointers

    def __eq__(self, other: object) -> bool:
        "Explicitly exclude BackPointers"
        assert isinstance(other, Item), "Item expected"
        return (self.rule == other.rule and
                self.dot == other.dot and
                self.start == other.start and
                self.end == other.end)

    def __hash__(self) -> int:
        "Explicitly exclude BackPointers"
        rule_hash = hash((self.rule.head, tuple(self.rule.spec)))
        return hash((rule_hash, self.dot, self.start, self.end))

    def __str__(self) -> str:
        pre: str = " ".join(sym.name for sym in self.rule.spec[:self.dot])
        post: str = " ".join(sym.name for sym in self.rule.spec[self.dot:])
        # backpointers: str = ", ".join(str(bp) for bp in self.backpointers)
        return (f"|({self.start} - {self.end})"
                f" {self.rule.head} -> {pre} \u00b7 {post}"
                )  # f" #bp: {{{backpointers}}}|")

    @staticmethod
    def predict(rule: Rule, start: int) -> 'Item':
        return Item(rule, 0, start, start, set())

    @staticmethod
    def complete(src: 'Item', trig: 'Item', at: int) -> 'Item':
        return Item(src.rule, src.dot + 1, src.start, at, {(src, trig)})

    @staticmethod
    def scan(src: 'Item', end: int, input: str) -> 'Item':
        return Item(src.rule, src.dot + 1, src.start, end, {(src, input)})

    def is_complete(self) -> bool:
        return self.dot >= len(self.rule.spec)

    def can_complete(self, other: 'Item') -> bool:
        other_next_sym: Optional[Symbol] = other.next_symbol()
        return (self.is_complete() and
                other_next_sym is not None and other_next_sym.is_nonterm() and
                other_next_sym.name == self.rule.head)

    def can_scan(self, lexeme: str) -> bool:
        next_sym: Optional[Symbol] = self.next_symbol()
        return (next_sym.pred(lexeme) if next_sym and next_sym.pred else False)

    def next_symbol(self) -> Optional[Symbol]:
        return (self.rule.spec[self.dot]
                if len(self.rule.spec) > self.dot else None)


StateSet = NewType("StateSet", Set[Item])

# NOTE: List[ASTNode] when mypy supports recursive types
# ASTNode = Union[str, Tuple[str, List['ASTNode']]]
ASTNode = Union[str, Tuple[str, List[Any]]]


class ForestIterator(Iterable[ASTNode]):
    # Each item is the root of binary trees to be extracted first-depth.
    # Each item branches to the left on Source, to the right on Trigger.
    # That's the easy, non-ambiguous grammar case. Alternatively...
    # There's a 3rd dimension for each item. Multiple back-pointers could
    # be leading to each item. Which implies a partially overlapping tree.
    def __init__(self, parser_output: Set[Item]) -> None:
        self.items: Set[Item] = parser_output
        self.gens: List[Tuple[Item, Iterator[List[ASTNode]]]] = []

    def __iter__(self) -> Iterator[ASTNode]:
        self.gens = [(root, ForestIterator._trace_item(root))
                     for root in self.items]
        return self

    @staticmethod
    def _trace_item(item: Item) -> Generator[List[ASTNode], None, None]:
        # Base case, item has no source. Its the begining.
        if len(item.backpointers) == 0:
            yield []

        for source, trigger in item.backpointers:
            assert isinstance(source, Item), "BUG: Expected Item for source"
            for spec_prefix in ForestIterator._trace_item(source):
                if isinstance(trigger, Item):  # Backpointer is a Completion
                    # Eg: source: (E -> E + . E), trigger: (E -> n .) => (E -> E + E .)
                    for spec_suffix in ForestIterator._trace_item(trigger):
                        yield spec_prefix + [(str(trigger.rule), spec_suffix)]
                else:  # Backpointer is a Scan
                    # Eg: source: (E -> E . + E), trigger: '+' => (E -> E + . E)
                    assert isinstance(trigger, str)
                    yield spec_prefix + [trigger]

    def __next__(self) -> Tuple[str, List[ASTNode]]:
        if len(self.gens) == 0:
            raise StopIteration
        try:
            root, tree_generator = self.gens[0]
            tree: List[ASTNode] = next(tree_generator)
            return (str(root.rule), tree)
        except StopIteration:
            self.gens.pop(0)
            return self.__next__()


class ForestIteratorSimple(Iterable[ASTNode]):
    # Each item is the root of binary trees to be extracted first-depth.
    # Each item branches to the left on Source, to the right on Trigger.
    # That's the easy, non-ambiguous grammar case. Alternatively...
    # There's a 3rd dimension for each item. Multiple back-pointers could
    # be leading to each item. Which implies a partially overlapping tree.
    def __init__(self, parser_output: Set[Item]) -> None:
        self.items: Set[Item] = parser_output
        self.roots: List[Item] = []

    def __iter__(self) -> Iterator[ASTNode]:
        self.roots = list(self.items)
        return self

    @staticmethod
    def _trace_item(item: Item) -> List[ASTNode]:
        # Base case, item has no source. Its the begining.
        if len(item.backpointers) == 0:
            return []

        source, trigger = next(iter(item.backpointers))  # TODO: iterate all
        assert isinstance(source, Item), "BUG: Expected Item for source"

        prefix: List[ASTNode] = ForestIteratorSimple._trace_item(source)
        if isinstance(trigger, Item):  # Backpointer is a Completion
            # Eg: source: (E -> E + . E), trigger: (E -> n .) => (E -> E + E .)
            suffix: List[ASTNode] = ForestIteratorSimple._trace_item(trigger)
            return prefix + [(str(trigger.rule), suffix)]
        else:  # Backpointer is a Scan
            # Eg: source: (E -> E . + E), trigger: '+' => (E -> E + . E)
            assert isinstance(trigger, str)
            return prefix + [trigger]

    def __next__(self) -> Tuple[str, List[Any]]:
        if len(self.roots):
            root: Item = self.roots.pop()
            return (str(root.rule), ForestIteratorSimple._trace_item(root))
        raise StopIteration


def parse(grammar: Grammar, input: Iterable[str]) -> Set[Item]:

    # 0. populate StateSet-0: add items for rules matching start symbol
    s0 = StateSet({Item.predict(rule, start=0)
                   for rule in grammar.rules(grammar.start)})
    statesets: List[StateSet] = [s0]

    # extract an iterator out of input
    input = iter(input)

    for stateset_id in itertools.count():
        curstate: StateSet = statesets[stateset_id]
        # DEBUG: print(f"StateSet[{stateset_id}]: {curstate}")

        prev_item_count: Optional[int] = None
        while len(curstate) != prev_item_count:
            prev_item_count = len(curstate)

            new_items: List[Item] = []
            for trigger in curstate:
                next_sym: Optional[Symbol] = trigger.next_symbol()
                if next_sym and next_sym.is_nonterm():
                    # Prediction: add rules starting with next symbol
                    new_items.extend(
                        Item.predict(rule, stateset_id)
                        for rule in grammar.rules(next_sym.name))
                elif next_sym is None and trigger.is_complete():
                    # Completion: add items with rules that completed
                    assert trigger.start <= stateset_id, "Item starts after end of stream"
                    new_items.extend(
                        Item.complete(src, trigger, stateset_id)
                        for src in statesets[trigger.start]
                        if trigger.can_complete(src))
                else:
                    # Scan: populate next state, ignored at this stage
                    assert next_sym is not None and next_sym.is_terminal(), \
                        "BUG: Expected Scan"

            # DEBUG: print(f"New items: {new_items}")
            # augment current stateset with new items, merging back-pointers
            for newitem in new_items:
                for existent in curstate:
                    # Merge back-pointers into existing item
                    if existent == newitem:
                        existent.backpointers.update(newitem.backpointers)
                        break
                else:  # item is new
                    curstate.add(newitem)

        # Scan: populate next state with items that lexeme can advance
        lexeme: Optional[str] = next(input, None)
        if lexeme is None:
            break
        # DEBUG: print(f"Lexeme: {lexeme}")
        statesets.append(
            StateSet({Item.scan(item, stateset_id + 1, lexeme)
                      for item in curstate if item.can_scan(lexeme)}))

    # Collect items from the last StateSet that have completed,
    # span all input, and which their rule matches the grammar start symbol.
    parsed_trees: Set[Item] = {
        item for item in iter(statesets[-1])
        if item.start == 0 and
        item.is_complete() and
        item.rule.head == grammar.start}

    if len(parsed_trees) == 0:
        raise RuntimeError("Couldn't parse input")

    return parsed_trees


class ParserTest(unittest.TestCase):
    def test_ambig_math(self):
        E = Symbol("E")
        plus = Symbol('+', lambda x: x == '+')
        times = Symbol('*', lambda x: x == '*')
        n = Symbol('n', lambda x: x.isdigit())
        grammar = Grammar("E", [
            Rule('E', [n]),
            Rule('E', [E, plus, E]),
            Rule('E', [E, times, E]),
        ])
        trees = parse(grammar, [c for c in "3+4*5"])
        print("Trees:")
        for tree in ForestIterator(trees):
            print(tree)

    def test_SS_b(self):
        S = Symbol("S")
        b = Symbol('b', lambda x: x == 'b')
        grammar = Grammar("S", [
            Rule('S', [S, S]),
            Rule('S', [b]),
        ])
        trees = parse(grammar, "b b b".split())
        print("Trees:")
        for tree in ForestIterator(trees):
            print(tree)

    def test_SSX_b(self):
        S = Symbol("S")
        X = Symbol("X")
        b = Symbol('b', lambda x: x == 'b')
        grammar = Grammar("S", [
            Rule('S', [S, S, X]),
            Rule('X', []),
            Rule('S', [b]),
        ])
        trees = parse(grammar, "b b b".split())
        print("Trees:")
        for tree in ForestIterator(trees):
            print(tree)


if __name__ == "__main__":
    unittest.main()
