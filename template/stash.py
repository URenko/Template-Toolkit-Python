import re
import types

from template import util


class Error(Exception):
  pass


PRIVATE = r"^[_.]"

LONG_REGEX = re.compile(r"-?\d+")

def _to_lower(x):
  return str(x).lower()

def _to_long(x):
  try:
    return long(x)
  except ValueError:
    match = LONG_REGEX.match(str(x))
    if match:
      return long(match.group(0))
    else:
      return 0L

def _slice(seq, items):
  if isinstance(items, str):
    raise TypeError
  sliced = []
  for x in items:
    try:
      sliced.append(seq[x])
    except KeyError:
      sliced.append(None)
  return sliced

def _curry(func, *args):
  def curried(*x):
    return func(*(args + x))
  return curried

def increment(x):
  return x + 1

def decrement(x):
  return x - 1

ROOT_OPS = {
  "inc": increment,
  "dec": decrement,
  }

def scalar_item(scalar):
  return scalar

def scalar_list(scalar):
  return [scalar]

def scalar_hash(scalar):
  return {"value": scalar}

def scalar_length(scalar):
  return len(str(scalar))

def scalar_size(scalar):
  return 1

def scalar_defined(scalar):
  return 1

def scalar_match(scalar, search=None, matchall=False):
  if scalar is None or search is None:
    return string
  string = str(scalar)
  if matchall:
    matches = re.findall(search, string)
    if matches and isinstance(matches[0], tuple):
      matches = [item for group in matches for item in group]  # flatten
  else:
    match = re.search(search, string)
    if match:
      matches = match.groups()
  return matches or ""

def scalar_search(scalar=None, pattern=None):
  if scalar is None or pattern is None:
    return scalar
  return re.search(pattern, str(scalar)) and True or False

def scalar_repeat(scalar="", count=1):
  return str(scalar) * count

def scalar_replace(scalar="", pattern="", replace="", replaceall=True):
  if re.search(r"\$\d+", replace):
    # replacement string may contain backrefs
    raise NotImplementedError("Backreferences in replace()")
  else:
    return re.sub(pattern, replace, str(scalar), 1 - int(bool(replaceall)))

def scalar_remove(scalar=None, search=None):
  if scalar is None or search is None:
    return scalar
  return re.sub(search, str(scalar), "")

def scalar_split(scalar="", split=None, limit=None):
  if limit is not None:
    return str(scalar).split(split, limit)
  else:
    return str(scalar).split(split)

def scalar_chunk(scalar="", size=1):
  string = str(scalar)
  if size > 0:
    return [string[pos:pos+size] for pos in range(0, len(string), size)]
  else:
    seq = [string[max(pos,0):pos-size]
           for pos in range(len(string) + size, size, size)]
    seq.reverse()
    return seq

def scalar_substr(scalar="", offset=0, length=0):  # "replacement" arg ignored
  return str(scalar)[offset:offset+length]


def hash_item(hash, item=""):
  if PRIVATE and re.search(PRIVATE, item):
    return None
  else:
    return hash[item]

def hash_hash(hash):
  return hash

def hash_size(hash):
  return len(hash)

def hash_each(hash):
  return [item for pair in hash.iteritems() for item in pair]

def hash_keys(hash):
  return hash.keys()

def hash_values(hash):
  return hash.values()

hash_items = hash_each

def hash_pairs(hash):
  return [{"key": key, "value": value} for key, value in sorted(hash.items())]

def hash_list(hash, what=""):
  if what == "keys":
    return hash_keys(hash)
  elif what == "values":
    return hash_values(hash)
  elif what == "each":
    return hash_each(hash)
  else:
    return hash_pairs(hash)

def hash_exists(hash, key):
  return key in hash

def hash_defined(hash, key=None):
  if key is None:
    return True
  else:
    return hash.get(key) is not None

def hash_delete(hash, *keys):
  for key in keys:
    del hash[key]

def hash_import(hash, imp=None):
  if isinstance(imp, dict):
    hash.update(imp)
  return ""

def hash_sort(hash):
  return sorted(hash.keys(), key=_to_lower)

def hash_nsort(hash):
  return sorted(hash.keys(), key=_to_long)

def list_item(list, item=0):
  return list[item]

def list_list(list):
  return list[:]

def list_hash(list, n=None):
  if n is not None:
    n = int(n or 0)
    return dict((index + n, item) for index, item in enumerate(list))
  else:
    return dict(util.chop(list, 2))

def list_push(list, *args):
  list.extend(args)
  return ""

def list_pop(list):
  return list.pop()

def list_unshift(list, *args):
  list[:0] = args
  return ""

def list_shift(list):
  return list.pop(0)

def list_max(list):
  return len(list) - 1

def list_size(list):
  return len(list)

def list_defined(list, index=None):
  if index is None:
    return 1
  else:
    return list[index] is not None

def list_first(list, count=None):
  if count is None:
    if list:
      return list[0]
    else:
      return None
  else:
    return list[:count]

def list_last(list, count=None):
  if count is None:
    if list:
      return list[-1]
    else:
      return None
  else:
    return list[-count:]

def list_reverse(list):
  copy = list[:]
  copy.reverse()
  return copy

def list_grep(list, pattern=""):
  regex = re.compile(pattern)
  return [item for item in list if regex.search(str(item))]

def list_join(list, joint=" "):
  return joint.join(str(item) for item in list)

def list_sort(list, field=None):
  if len(list) <= 1:
    return list[:]
  else:
    if field:
      return sorted(list, key=_smartsort(field, _to_lower))
    else:
      return sorted(list, key=_to_lower)

def list_nsort(list, field=None):
  if len(list) <= 1:
    return list[:]
  elif field:
    return sorted(list, key=_smartsort(field, _to_long))
  else:
    return sorted(list, key=_to_long)

def list_unique(list):
  seen = {}
  return [item for item in list if seen.setdefault(item, 0) is not None]

def list_import(list, *args):
  for arg in args:
    if isinstance(arg, list):
      list.extend(x for x in arg if x is not None)
  return list

def list_merge(list_, *args):
  copy = list_[:]
  for arg in args:
    if isinstance(arg, list):
      copy.extend(x for x in arg if x is not None)
  return copy

def list_slice(list, start=0, to=None):
  if to is None:
    return list[start:]
  else:
    return list[start:to]

def list_splice(list, offset=None, length=None, *replace):
  if replace:
    raise NotImplementedError("list splice with replacement")
  elif length is not None:
    offset = offset or 0
    removed = list[offset:length]
    del list[offset:length]
    return removed
  elif offset is not None:
    removed = list[offset:]
    del list[offset:]
    return removed
  else:
    removed = list[:]
    del list[:]
    return removed

def _smartsort(field, coerce):
  def getkey(element):
    key = element
    if isinstance(element, dict):
      key = element[field]
    else:
      attr = getattr(element, field, None)
      if callable(attr):
        key = attr()
    return coerce(key)
  return getkey

SCALAR_OPS = {
  "item": scalar_item,
  "list": scalar_list,
  "hash": scalar_hash,
  "length": scalar_length,
  "size": scalar_size,
  "defined": scalar_defined,
  "match": scalar_match,
  "search": scalar_search,
  "repeat": scalar_repeat,
  "replace": scalar_replace,
  "remove": scalar_remove,
  "split": scalar_split,
  "chunk": scalar_chunk,
  "substr": scalar_substr,
  }

LIST_OPS = {
  "item": list_item,
  "list": list_list,
  "hash": list_hash,
  "push": list_push,
  "pop": list_pop,
  "unshift": list_unshift,
  "shift": list_shift,
  "max": list_max,
  "size": list_size,
  "defined": list_defined,
  "first": list_first,
  "last": list_last,
  "reverse": list_reverse,
  "grep": list_grep,
  "join": list_join,
  "sort": list_sort,
  "nsort": list_nsort,
  "unique": list_unique,
  "import": list_import,
  "merge": list_merge,
  "slice": list_slice,
  "splice": list_splice,
  }

HASH_OPS = {
  "item": hash_item,
  "hash": hash_hash,
  "size": hash_size,
  "each": hash_each,
  "keys": hash_keys,
  "values": hash_values,
  "items": hash_items,
  "pairs": hash_pairs,
  "list": hash_list,
  "exists": hash_exists,
  "defined": hash_defined,
  "delete": hash_delete,
  "import": hash_import,
  "sort": hash_sort,
  "nsort": hash_nsort,
  }



class Stash:
  def __init__(self, params=None):
    params = params or {}
    self.contents = {"global": {}}
    self.contents.update(params)
    self.contents.update(ROOT_OPS)
    self._PARENT = None
    self._DEBUG = bool(params.get("_DEBUG"))

  def __getitem__(self, key):
    return self.contents.get(key)

  def __setitem__(self, key, value):
    self.contents[key] = value

  def clone(self, params=None):
    params = params or {}
    import_ = params.get("import")
    if isinstance(import_, dict):
      del params["import"]
    else:
      import_ = None
    clone = Stash()
    clone.contents.update(self.contents)
    clone.contents.update(params)
    clone._DEBUG = self._DEBUG
    clone._PARENT = self
    if import_:
      HASH_OPS["import"](clone, import_)
    return clone

  def declone(self):
    return self._PARENT or self

  def get(self, ident, args=None):
    ident = util.unscalar(ident)
    root = self
    if isinstance(ident, str) and ident.find(".") != -1:
      ident = [y for x in ident.split(".")
                 for y in (re.sub(r"\(.*$", "", x), 0)]
    if isinstance(ident, (list, tuple)):
      for a, b in util.chop(ident, 2):
        result = self._dotop(root, a, b)
        if result is not None:
          root = result
        else:
          break
    else:
      result = self._dotop(root, ident, args)

    if result is None:
      result = self.undefined(ident, args)
    return util.PerlScalar(result)

  def set(self, ident, value, default=False):
    root = self
    ident = util.unscalar(ident)
    value = util.unscalar(value)
    # ELEMENT: {
    if isinstance(ident, str) and ident.find(".") >= 0:
      ident = [y for x in ident.split(".")
                 for y in (re.sub(r"\(.*$", "", x), 0)]
    if isinstance(ident, (list, tuple)):
      chopped = list(util.chop(ident, 2))
      for i in range(len(chopped)-1):
        x, y = chopped[i]
        result = self._dotop(root, x, y, True)
        if result is None:
          # last ELEMENT
          return ""
        else:
          root = result
      result = self._assign(root, chopped[-1][0], chopped[-1][1],
                            value, default)
    else:
      result = self._assign(root, ident, 0, value, default)

    if result is None:
      return ""
    else:
      return result

  def _assign(self, root, item, args=None, value=None, default=False):
    item = util.unscalar(item)
    args = util.unscalar_list(args)
    atroot = root is self
    if root is None or item is None:
      return None
    elif PRIVATE and re.search(PRIVATE, item):
      return None
    elif isinstance(root, dict) or atroot:
      if not (default and root.get(item)):
        root[item] = value
        return value
    elif isinstance(root, (list, tuple)) and re.match(r"-?\d+$", str(item)):
      item = int(item)
      if not (default and 0 <= item < len(root) and root[item]):
        root[item] = value
        return value
    elif isinstance(root, types.InstanceType):
      if not (default and getattr(root, item)()):
        args.append(value)
        return getattr(root, item)(*args)
    else:
      raise Error("don't know how to assign to %s.%s" % (root, item))

    return None

  def _dotop(self, root, item, args=None, lvalue=False):
    root = util.unscalar(root)
    item = util.unscalar(item)
    args = util.unscalar_list(args)
    atroot = root is self
    result = None

    # return undef without an error if either side of dot is unviable
    if root is None or item is None:
      return None

    # or if an attempt is made to access a private member, starting _ or .
    if PRIVATE and isinstance(item, str) and re.search(PRIVATE, item):
      return None

    found = True
    isdict = isinstance(root, dict)
    if atroot or isdict:
      # if root is a regular dict or a Template::Stash kinda dict (the
      # *real* root of everything).  We first lookup the named key
      # in the hash, or create an empty hash in its place if undefined
      # and the lvalue flag is set.  Otherwise, we check the HASH_OPS
      # pseudo-methods table, calling the code if found, or return None
      if isdict:
        # We have to try all these variants because Perl hash keys are
        # stringified, but Python's aren't.
        try:
          value = root[item]
        except (KeyError, TypeError):
          try:
            value = root[str(item)]
          except (KeyError, TypeError):
            try:
              value = root[int(item)]
            except (KeyError, TypeError, ValueError):
              value = None
      else:
        value = root[item]
      if value is not None:
        if callable(value):
          result = value(*args)
        else:
          return value
      elif lvalue:
        # we create an intermediate hash if this is an lvalue
        root[item] = {}
        return root[item]
      # ugly hack: only allow import vmeth to be called on root stash
      else:
        try:
          value = HASH_OPS.get(item)
        except TypeError:  # Because item is not hashable, presumably.
          value = None
        if (value and not atroot) or item == "import":
          result = value(root, *args)
        else:
          try:
            return _slice(root, item)
          except TypeError:
            found = False
    elif isinstance(root, (list, tuple)) or hasattr(root, "TT_LIST_ATTRIBUTE"):
      # if root is a list then we check for a LIST_OPS pseudo-method
      # or return the numerical index into the list, or None
      root = getattr(root, "TT_LIST_ATTRIBUTE", root)
      try:
        value = LIST_OPS.get(item)
      except TypeError:  # Because item is not hashable, presumably.
        value = None
      if value:
        result = value(root, *args)
      else:
        try:
          value = root[int(item)]
        except TypeError:
          sliced = []
          try:
            return _slice(root, item)
          except TypeError:
            pass
        except IndexError:
          return None
        else:
          if callable(value):
            result = value(*args)
          else:
            return value
    elif isinstance(root, types.InstanceType):
      try:
        value = getattr(root, item)
      except (AttributeError, TypeError):
        # Failed to get object method, so try some fallbacks.
        try:
          func = HASH_OPS[item]
        except (KeyError, TypeError):
          pass
        else:
          return func(root.__dict__, *args)
      else:
        if callable(value):
          return value(*args)
        else:
          return value
    elif item in SCALAR_OPS and not lvalue:
      result = SCALAR_OPS[item](root, *args)
    elif item in LIST_OPS and not lvalue:
      result = LIST_OPS[item]([root], *args)
    elif self._DEBUG:
      raise Error("don't know how to access [%r].%s" % (root, item))
    else:
      result = []

    if not found and self._DEBUG:
      raise Error("%s is undefined" % (item,))
    elif result is not None:
      return result
    elif self._DEBUG:
      raise Error("%s is undefined" % (item,))
    else:
      return None

  def getref(self, ident, args=None):
    root = self
    if util.is_seq(ident):
      chopped = list(util.chop(ident, 2))
      for i, (item, args) in enumerate(chopped):
        if i == len(chopped) - 1:
          break
        root = self._dotop(root, item, args)
        if root is None:
          break
    else:
      item = ident
    if root is not None:
      return lambda *x: self._dotop(root, item, tuple(args or ()) + x)
    else:
      return lambda *x: ""


  def update(self, params):
    if params is not None:
      import_ = params.get("import")
      if isinstance(import_, dict):
        self.contents.update(import_)
        del params["import"]
      self.contents.update(params)

  def undefined(self, ident, args):
    return ""
