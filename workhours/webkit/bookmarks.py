#!/usr/bin/env python
# encoding: utf-8
"""
Grep WebKit bookmarks JSON
"""

from codecs import open
from workhours.webkit import longdate_to_datetime
import logging
log = logging.getLogger('webkit.bookmarks')

import workhours.models.json as json

NODETYPE=u'folder'
NODEKEY=u'children'
def wbkt_trav(nodes, depth=0, path=None):
    if path is None:
        path = []

    for node in nodes:
        yield {   'path': u'/'.join(path),
                #node.get('type'), # folder || url
                'url':  node.get('url','').encode('utf-8','replace'),
                'title': node.get('name'), #u'%s' % node.get('name','').encode('utf-8','replace'),
                'date': longdate_to_datetime(long(node.get('date_added')))
        }
        if node.get('type') == NODETYPE:
            _p = path+[node.get('name')]
            for node in wbkt_trav(node[NODEKEY], depth=depth+1, path=_p):
                yield node
    return


def load_json_file(file_):
    with open(file_,'rb', encoding='utf-8') as f:
        #return json.loads(f.read()) #.decode('utf-8','replace')
        return json.load(f)

def parse_webkit_bookmarks(uri=None):
    log.info("Parsing: %s" % uri)
    bj = load_json_file(uri)
    #print bj['checksum'], bj['version']
    for nodekey in ('bookmark_bar','other'):
        for node in wbkt_trav(bj['roots'][nodekey][NODEKEY], path=[nodekey]):
            yield node


def print_bookmarks(file_, outp, flatten, dated):

    fmtstr="{path}\t{url}\t{title}\t{date}"
    if flatten:
        fmtstr="{url}\t{title}\t{date}"
    if dated:
        fmtstr = '{date}\t{url}\t{title}'

    for node in parse_webkit_bookmarks(file_):
        print fmtstr.format(**node)


def main():
    """
    mainfunc
    """
    pass


if __name__ == "__main__":
    import optparse
    import logging
    import sys
    import os

    prs = optparse.OptionParser(usage="./")

    prs.add_option('-b', '--read-bookmarks',
                    dest='read_bookmarks_file',
                    default=os.path.expanduser(
                            '~/.config/google-chrome/Default/Bookmarks')
                  )
    prs.add_option('-f', '--flatten-bookmarks',
                    dest='flatten_bookmarks',
                    action='store_true')
    prs.add_option('-d', '--print-date',
                    dest='dated',
                    action='store_true',)

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
        sys.argv = [sys.argv[0]] + args
        import unittest
        exit(unittest.main())

    if opts.read_bookmarks_file:
        #sys.stdout.encoding='UTF-8'
        print_bookmarks(opts.read_bookmarks_file,
                        sys.stdout,
                        flatten=opts.flatten_bookmarks,
                        dated=opts.dated)
    #main()
