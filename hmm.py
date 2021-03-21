#!/usr/bin/env python

from collections import Counter
import itertools
import math
from typing import (
    Dict,
    Iterable,
    List,
    NamedTuple,
    Optional,
    Set,
    Tuple,
)
import unittest


class AdditiveSmoothingBigramEstimator:
    """
    BigramEstimator uses sample data to build probabilities of Unigram and Bigrams.
    - https://en.wikipedia.org/wiki/N-gram
    - Uses Additive smoothing (https://en.wikipedia.org/wiki/Additive_smoothing) to
      account for non-observed elements.
    """

    def __init__(
        self, samples: Iterable[List[str]], uniqElements: Optional[int] = None
    ) -> None:
        """
        uniqElements may be provided if known, otherwise its estimated.
        """
        self.alpha: float = 1.0e-10
        self.pUnigram: Dict[str, float]
        self.pUnigramDefault: float
        self.unigramCounts: Counter
        self.uniques: int
        (
            self.pUnigram,
            self.pUnigramDefault,
            self.unigramCounts,
            self.uniques,
        ) = self._unigrams(samples, self.alpha, uniqElements)
        self.pBigram = self._bigrams(
            samples, self.unigramCounts, self.alpha, self.uniques
        )

    @staticmethod
    def _unigrams(
        samples: Iterable[List[str]], alpha: float, uniqElements: Optional[int] = None
    ) -> Tuple[Dict[str, float], float, Counter, int]:
        """
        Build unigram probabilities from sample data.
        Use additive smoothing to assign some probability to unseen elements.
        """
        unigrams: Counter = Counter(itertools.chain(*samples))
        # Additive smoothing: Assume we've seen all elements at least once
        # (times alpha) to assign non-0 probability to unseen elements.
        uniques: int = uniqElements if uniqElements else len(unigrams)
        totalCount: float = sum(unigrams.values()) + alpha * uniques
        # Estimate unigram probabilities
        pUnigram: Dict[str, float] = {
            i: (unigrams[i] + alpha) / totalCount for i in unigrams.elements()
        }
        pUnigramDefault: float = alpha / totalCount
        return pUnigram, pUnigramDefault, unigrams, uniques

    @staticmethod
    def _bigrams(
        samples: Iterable[List[str]],
        unigramCounts: Counter,
        alpha: float,
        uniques: int,
    ) -> Dict[Tuple[str, str], float]:
        """
        Build bigram probabilities from sample data.
        Use additive smoothing to assign some probability to unseen elements.
        """
        bigrams: Counter = Counter(itertools.chain(*[zip(s, s[1:]) for s in samples]))
        pBigram: Dict[Tuple[str, str], float] = {
            (i, j): (bigrams[(i, j)] + alpha) / (unigramCounts[i] + alpha * uniques)
            for i, j in bigrams.elements()
        }
        return pBigram

    def pX(self, x: str) -> float:
        """
        Return p(x) from p(x)/total
        """
        return self.pUnigram.get(x, self.pUnigramDefault)

    def pXY(self, x: str, y: str) -> float:
        """
        Return p(y|x) from p(x,y)/p(x)
        """
        return self.pBigram.get(
            (x, y),
            self.alpha
            / (self.pUnigram.get(x, self.pUnigramDefault) + self.alpha * self.uniques),
        )


class MarkovChain:
    "1st Order Markov Chain"

    def __init__(self, pEstimator: AdditiveSmoothingBigramEstimator) -> None:
        self.pEstimator = pEstimator

    def pSequence(self, sequence: List[str]) -> float:
        "Calculate the probability of this sequence of events"
        if len(sequence) == 0:
            return 0.0
        logProb = math.log(self.pEstimator.pX(sequence[0])) + sum(
            math.log(self.pEstimator.pXY(x, y)) for x, y in zip(sequence, sequence[1:])
        )
        return math.exp(logProb)


class MarkovChainTest(unittest.TestCase):
    def test_pSequence(self):
        # Calculate some initial state probabilities (probability of any state)
        samples: List[List[str]] = [
            list("accgcgctta"),
            list("gcttagtgac"),
            list("tagccgttac"),
        ]
        # Now that we've got same fake data build a MarkovChain
        mc: MarkovChain = MarkovChain(AdditiveSmoothingBigramEstimator(samples, 4))
        print(f'pSequence("cggt") = {mc.pSequence(list("cggt"))}')
        print(f'pSequence("gctt") = {mc.pSequence(list("gctt"))}')
        print(f'pSequence("ccgt") = {mc.pSequence(list("ccgt"))}')
        print(f'pSequence("qact") = {mc.pSequence(list("qact"))}')
        print(f'pSequence("tagt") = {mc.pSequence(list("tagt"))}')


class Hmm(NamedTuple):
    chain: MarkovChain

    def viterbiDecode(self, observed_states):
        "Show most likely events given observed states"


if __name__ == "__main__":
    unittest.main()

# Refs
# - http://pages.cs.wisc.edu/~molla/summer_research_program/lecture5.1.pdf
# - https://web.stanford.edu/~jurafsky/slp3/A.pdf
# - https://tscheffler.github.io/teaching/2016advancednlp/slides/04-smoothing.pdf
