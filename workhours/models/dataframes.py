#!/usr/bin/env python
# encoding: utf-8

"""
to_dataframes
"""
try:
    from pandas import DataFrame
except ImportError:
    print("FAILED TO IMPORT PANDAS")
from workhours.models import DBSession, Event

import logging
log = logging.getLogger('workhours.models.dataframes')

def to_dataframes(*args, **kwargs):
    """
    serialize data to dataframes
    """
    s = kwargs.get('session', DBSession())

    query = kwargs.get('query')
    if query is None:
        query = (Event.date, Event.source, Event.title, Event.url, Event.source_id)
        query = s.query(*query)
        log.debug('default query: %r' % query)
        log.debug('default query: %s' % query)
    else:
        log.debug('query: %r' % query)
        log.debug('query: %s' % query)

    column_names = kwargs.get('column_names',
            ('date',
             'source',
             'title',
             'url',
             'source_id',
             ))
    #log.debug('column_names: %r' % column_names)

    df = DataFrame.from_records(
            query.all(), # TODO
            columns=column_names,
            coerce_float=True)
    return df


import unittest
class Test_to_dataframes(unittest.TestCase):
    def test_to_dataframes(self):
        df = to_dataframes()
        assert df


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

