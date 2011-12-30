#!/usr/bin/env python3

# http://www.doughellmann.com/PyMOTW/multiprocessing/mapreduce.html
# http://mikecvet.wordpress.com/2010/07/02/parallel-mapreduce-in-python/

import os, re, string, sys, time
import operator
from collections import defaultdict
from itertools import chain
from multiprocessing import Pool

WHITE_SPACE = re.compile('\s+')
LOG_HEADER = re.compile('^Conversation with .*\)$')
LINE_HEADER = re.compile('^(\([^)]+\))? *[^:]+: *')
TR = str.maketrans(string.punctuation, ' ' * len(string.punctuation))
STOP_WORDS = set([
  'a', 'an', 'and', 'are', 'as', 'be', 'by', 'for', 'if', 'in',
  'is', 'it', 'of', 'or', 'that', 'the', 'to', 'with',
  'a', 'ante', 'bajo', 'con', 'contra', 'de', 'desde', 'en', 'entre',
  'hacia', 'hasta', 'para', 'por', 'segun', 'sin', 'sobre', 'tras',
  'la', 'las', 'lo', 'los', 'que', 'como',
])


def dir_walker(rootdirs):
  "Filepath generator rooted at rootdir"
  for rootdir in rootdirs:
    for root, dirs, files in os.walk(rootdir):
      for file in files:
        yield root + '/' + file


def word_reader(stream):
  "Returns a word generator from a stream"
  splitlines = (WHITE_SPACE.split(line.rstrip()) for line in stream)
  return (word for line in splitlines for word in line)


def pidgin_word_reader(stream):
  """Returns a word generator from a stream
     filtering pidgin headers and timestamps"""
  # discard pidgin logs header lines
  stream = (line for line in stream if not LOG_HEADER.match(line))
  # remove pidgin timestamps and contact name
  stream = (LINE_HEADER.sub('', line, count=1) for line in stream)
  # remove punctuation
  stream = (line.translate(TR) for line in stream)
  return word_reader(stream)


def sanitize_word(word):
  "Transform word and return if it should be accounted"
  word = word.lower()
  return word, len(word) > 2 and word not in STOP_WORDS


def wordcount_map(path):
  """
  Reads words from a file and maps them to to a list of
  tuples [(word, 1), ...] marking an occurence for each word
  """
  results = []
  with open(path, 'rt', encoding='latin-1') as stream:
    for word in pidgin_word_reader(stream):
      word, ok = sanitize_word(word)
      if ok:
        results.append((word, 1))
  return results


def partition(mapped_values):
  """
  Group a list of tuples that share the same key
  [(word1, 1), (word1, 1), (word2, 1)] -> [(word1, (1, 1)), ((word2, (1,))]
  """
  partitioned_data = defaultdict(list)
  for k, v in mapped_values:
    partitioned_data[k].append(v)
  return partitioned_data.items()


def wordcount_reduce(word_occurrence):
  """
  Aggregates the word ocurrence values by key
  (word1, (1, 1, 1)) -> (word1, 3)
  """
  return (word_occurrence[0], sum(word_occurrence[1]))


def mapreduce(log_dirs):
  workers = Pool(3)

  t_start = time.time()
  wordlists = workers.map(wordcount_map, dir_walker(log_dirs))
  t_end = time.time()
  sys.stderr.write("map fase: %0.3f ms\n" % (1000.0 * (t_end - t_start)))

  t_start = time.time()
  grouped = partition(chain(*wordlists))
  t_end = time.time()
  sys.stderr.write("partition fase: %0.3f ms\n" % (1000.0 * (t_end - t_start)))

  t_start = time.time()
  wordfreqs = workers.map(wordcount_reduce, grouped)
  t_end = time.time()
  sys.stderr.write("reduce fase: %0.3f ms\n" % (1000.0 * (t_end - t_start)))

  workers.close()
  workers.join()

  wordfreqs.sort(key=operator.itemgetter(1), reverse=True)
  for word, freq in wordfreqs:
    sys.stdout.write("%-7d %s\n" % (freq, word))


if __name__ == '__main__':
  if len(sys.argv) <= 1:
    sys.stderr.write("Usage: map_reduce.py <pidgin-logs-dir-1> ...\n")
    sys.exit(1)
  mapreduce(sys.argv[1:])
