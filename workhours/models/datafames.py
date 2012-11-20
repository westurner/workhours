#!/usr/bin/env python
# encoding: utf-8
from __future__ import print_function
"""
to_dataframes
"""


def to_dataframes(dburi, *args, **kwargs):
    """
    serialize data to dataframes
    """
    import pandas

    from workhours import models
    s = models.Session(dburi)

    query = (Event.date, Event.title, Event.url)

    result_iter =  s.query(*query)
    df = DataFrame


import unittest
class Test_to_dataframes(unittest.TestCase):
    def test_to_dataframes(self):
        pass


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

    to_dataframes(*args, **kwargs)

if __name__ == "__main__":
    main()
from workhours.models import

