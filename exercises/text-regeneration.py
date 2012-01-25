#!/usr/bin/env python

INPUT="""
LAUNCELOT: Nay, indeed, if you had your eyes, you might fail of
the knowing me: it is a wise father that knows his
own child. Well, old man, I will tell you news of
your son: give me your blessing: truth will come
to light; murder cannot be hid long; a man's son
may, but at the length truth will out.
"""
MAX_WORD_SIZE=36

DEBUG = False

import re
WORDS = filter(None, re.split('\W+', INPUT))


def split_text(text):

  while text:

    # search smallest matching word
    small_word_end = 1
    while small_word_end < len(text) and \
          not is_a_word(text[:small_word_end]):
      small_word_end += 1
    if DEBUG: print "min word [%s]" % text[:small_word_end]

    # search for the bigest matching word
    big_word_end = small_word_end
    for i in xrange(1, MAX_WORD_SIZE):
      if is_a_word(text[:small_word_end+i]):
        big_word_end = small_word_end + i
    if DEBUG: print "max word [%s]" % text[:big_word_end]

    # validate that next word is valid
    while big_word_end > small_word_end and \
          not next_word_is_valid(text[big_word_end:]):
      big_word_end -= 1

    yield text[:big_word_end]
    text = text[big_word_end:]


def next_word_is_valid(text):
  for i in xrange(MAX_WORD_SIZE):
    if is_a_word(text[:i]):
      return True
  return False


def is_a_word(word):
  if DEBUG: print word
  if word in WORDS:
    return True
  else:
    return False


# some testing
if __name__ == '__main__':
  import sys
  nospaces = re.sub('\W+', '', INPUT)
  for word in split_text(nospaces):
    sys.stdout.write("%s " % word)
  sys.stdout.write("\n")
