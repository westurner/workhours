#!/usr/bin/env python
# encoding: utf-8
from __future__ import print_function
"""
sequence_import

import a sequence of bookmarks/history visits,
- align and deduplicate overlapping sets

"""

from itertools import groupby, izip
from operator import attrgetter
from datetime import datetime, timedelta

from collections import namedtuple
Item = namedtuple('Item', ('date','url'))

def extend_timestamps(seq):
    """
    - "uniquify" timestamps as indices,
      adding +.001, +.002, +.003 for items with identical timestamps
      due to low resolution timestamping
    """
    for k,values in groupby(seq, attrgetter("date")):
        values = list(values)
        _len = len(values)
        for item, offset in izip(values, xrange(0,_len)):
            newdate = item.date + timedelta(microseconds=offset) # TODO: microseconds?
            yield Item(newdate, item.url)

def create_test_data():
    _now = datetime.now()
    events = [Item(_now, 'http://google.com'), Item(_now, 'http://yahoo.com')]
    for n in xrange(3):
        events.append(Item(datetime.now(), n))
    _now = datetime.now()
    events.append(Item(_now, 'another set'))
    events.append(Item(_now, 'that has lowres timestamps'))
    return events

import unittest
class Test_sequence_import(unittest.TestCase):
    def test_create_test_data(self):
        events = create_test_data()
        # ... read the metadata
        # ... the original wt is gtg
        # ... do you have a warrant or a NSL?
        # ... if not, you have violated due process.
        # ... it is wholly illegal to scan without consent.
        # ... we will consider you as an alternate.
        for e in events:
            print(e)

    def test_extend_timestamps(self):
        eventseq = create_test_data()
        updated = list( extend_timestamps(eventseq) )
        for orig, updated in izip(eventseq, updated):
            print(orig, updated)
            print((str(orig.date), str(updated.date)))


def main():
    import optparse
    import logging

    prs = optparse.OptionParser(usage="./%prog : args")

    prs.add_option('-v', '--verbose',
                    dest='verbose',
                    action='store_true',)
    prs.add_option('-q', '--quiet',
                    dest='quiet',
                    action='store_true',)
    prs.add_option('-t', '--test',
                    dest='run_tests',
                    action='store_true',)

    (opts, args) = prs.parse_args()

    if not opts.quiet:
        logging.basicConfig()

        if opts.verbose:
            logging.getLogger().setLevel(logging.DEBUG)

    if opts.run_tests:
        import sys
        sys.argv = [sys.argv[0]] + args
        import unittest
        exit(unittest.main())

    #sequence_import(seq)

if __name__ == "__main__":
    main()
