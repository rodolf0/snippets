#!/usr/bin/env python

# original author: rafael darder

class lazy_value(object):
  "A descriptor-decorator for memoizing properties: it calcs once, then caches"
  def __init__(self, decorated_func):
    self.f = decorated_func
    self.__name__ = decorated_func.__name__
    self.__doc__ = decorated_func.__doc__
  def __get__(self, instance, owner):
    _r = self.f(instance)
    setattr(instance, self.__name__, _r)
    return _r


class _LogRow(object):
  """Allow accessing a row by name in a similar fasion to a dictionary
     but without all the whole dictionary implementation for each instance"""
  __slots__ = ['row', 'streamsrc']
  def __init__(self, row, streamsrc):
    object.__setattr__(self, 'streamsrc', streamsrc)
    object.__setattr__(self, 'row', row)

  def __cmp__(self, other):
    """cmp_fields should be a list of tuples where the first element
       is the field to compare and the second the sort order (1 or -1)"""
    for key, neg in self.streamsrc.cmp_fields:
      r = cmp(self.row[key], other.row[key])
      if r != 0:
        return r * neg
    return 0

  def __getitem__(self, key):
    "Allow indexing a row by name, idx or a slice"
    if isinstance(key,str):
      return self.row[self.streamsrc.idxlookup[key]]
    elif isinstance(key, (tuple, list)):
      return [self[i] for i in key]
    elif isinstance(key, (int, slice)):
      return self.row[key]
  def __setitem__(self, key, value):
    "Allow changes to the row either by name or index"
    if isinstance(key, str):
      self.row[self.streamsrc.idxlookup[key]] = value
    else:
      self.row[key] = value
  def __getattr__(self, key):
    "Access row contents as if they were attributes"
    if key in self.streamsrc.idxlookup:
      return self.row[self.streamsrc.idxlookup[key]]
  def __setattr__(self, key, value):
    "Access row contents as if they were attributes"
    if key in self.streamsrc.idxlookup:
      self.row[self.streamsrc.idxlookup[key]] = value
    else:
      object.__setattr__(self, key, value)
  def __iter__(self):
    "Iteration over row elements"
    return iter(self.row)
  def __repr__(self):
    return str(dict((self.streamsrc.keylookup[idx], col)
                      for idx, col in enumerate(self.row)))


class LogReader(object):
  """Interprets a stream as rows indexable by header names"""

  def __init__(self, stream, delim='\xfe'):
    self.stream = (line.rstrip('\r\n').split(delim) for line in stream)
    self.header = next(self.stream)
    self._current = self._next = None

  @lazy_value
  def idxlookup(self):
    "Calculate header names to index mappings just the first time"
    _mapping = dict((k, i) for i, k in enumerate(self.header))
    return _mapping

  @lazy_value
  def keylookup(self):
    "Calculate index to header name mappings (the dict is not ordered)"
    _mapping = dict((i, k) for k, i in self.idxlookup.items())
    return _mapping

  def resolv_cmpkeys(self, cmpkeys):
    "Map keys to indexes"
    return tuple((self.idxlookup[key], rev) for key, rev in cmpkeys)

  def __iter__(self):
    return self

  def __next__(self):
    "Keep a double buffer so that we can peek"
    if not self._next:
      if not self._current:
        # just starting
        self._next = _LogRow(next(self.stream), self)
      else:
        # no more lines
        raise StopIteration
    self._current = self._next
    try:
      self._next = _LogRow(next(self.stream), self)
    except StopIteration:
      self._next = None
    return self._current

  next = __next__

  def set_cmp_fields(self, cmp_fields):
    "A chainable func that sets the comparison keys by which rows are sorted"
    self.cmp_fields = self.resolv_cmpkeys(cmp_fields)
    return self

  def current(self):
    return self._current

  def EOF(self):
    "Tell if there's any more data"
    return self._current and not self._next



def test():
  import sys
  lr = LogReader(sys.stdin)
  for row in sorted(lr.set_cmp_fields([('User-ID', 1), ('Time', -1)])):
    print(row['User-ID'], row['Time'], row['Buy-ID'])

if __name__ == '__main__': test()

# vim: set sw=2 sts=2 : #
