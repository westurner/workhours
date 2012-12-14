#!/usr/bin/env python

# See: http://code.activestate.com/recipes/576693/

# Backport of OrderedDict() class that runs on Python 2.4, 2.5, 2.6, 2.7 and pypy.
# Passes Python2.7's test suite and incorporates all the latest updates.

try:
    from thread import get_ident as _get_ident
except ImportError:
    from dummy_thread import get_ident as _get_ident

try:
    from _abcoll import KeysView, ValuesView, ItemsView
except ImportError:
    pass

try:
    from collections import OrderedDict
except ImportError:
    from workhours.ordereddict import OrderedDict
