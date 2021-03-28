#!/usr/bin/env python

from collections import Counter
import itertools
import math
import numpy as np
from typing import (
    Callable,
    Dict,
    Iterable,
    List,
    NamedTuple,
    Optional,
    Tuple,
    Union,
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


class TuringGoodBigramEstimator:
    """
    BigramEstimator uses sample data to build probabilities of Unigram and Bigrams.
    """

    def __init__(self, samples: Iterable[List[str]]) -> None:
        self.unigrams: Counter = Counter(itertools.chain(*samples))
        bigrams: Counter = Counter(itertools.chain(*[zip(s, s[1:]) for s in samples]))
        self.uniqElements: int = len(self.unigrams)
        # Counts of all bigrams we've seen x times.
        # Eg: There's 1k different bigrams we've seen x times.
        biFreqFreq: Counter = Counter(bigrams.values())
        biFFLogFit: Callable[[float], float] = self.logFit(
            biFreqFreq.keys(), biFreqFreq.values()
        )
        self.adjBigrams: Dict[Tuple[str, str], float] = {
            bigram: (count + 1)
            * biFreqFreq.get(count + 1, biFFLogFit(count + 1))
            / biFreqFreq.get(count, biFFLogFit(count))
            for bigram, count in bigrams.items()
        }
        # N0 (Estimation of non-observed bigrams) ~ (all posible - observed)
        unseenBigrams: float = self.uniqElements * self.uniqElements - len(bigrams)
        self.adjUnseenBigraam = biFreqFreq.get(1, biFFLogFit(1)) / unseenBigrams

    @staticmethod
    def logFit(
        xValues: Iterable[float], yValues: Iterable[float]
    ) -> Callable[[float], float]:
        [fit_a, fit_b] = np.polyfit(np.log(list(xValues)), list(yValues), 1)
        # Build a function to map points to fit curve
        def _fn(x: float) -> float:
            return fit_a + fit_b * math.log(x)

        return _fn

    def pXY(self, x: str, y: str) -> float:
        """ Return p(y|x) from p(x,y)/p(x) adjusted by Good-Turing"""
        return self.adjBigrams.get((x, y), self.adjUnseenBigraam) / self.unigrams.get(
            x, 1
        )

    def pX(self, x: str) -> float:
        return self.unigrams.get(x, 1) / self.uniqElements


class MarkovChain:
    "1st Order Markov Chain"

    def __init__(
        self,
        pEstimator: Union[AdditiveSmoothingBigramEstimator, TuringGoodBigramEstimator],
    ) -> None:
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
        print(f'pSequence("ta") = {mc.pSequence(list("ta"))}')

    def test_pSequenceGoodTuring(self):
        # Calculate some initial state probabilities (probability of any state)
        samples: List[List[str]] = [
            list("accgcgctta"),
            list("gcttagtgac"),
            list("tagccgttac"),
        ]
        # Now that we've got same fake data build a MarkovChain
        mc: MarkovChain = MarkovChain(TuringGoodBigramEstimator(samples))
        print(f'pSequence("cggt") = {mc.pSequence(list("cggt"))}')
        print(f'pSequence("gctt") = {mc.pSequence(list("gctt"))}')
        print(f'pSequence("ccgt") = {mc.pSequence(list("ccgt"))}')
        print(f'pSequence("qact") = {mc.pSequence(list("qact"))}')
        print(f'pSequence("tagt") = {mc.pSequence(list("tagt"))}')
        print(f'pSequence("ta") = {mc.pSequence(list("ta"))}')


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
