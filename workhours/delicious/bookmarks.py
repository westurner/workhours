#!/usr/bin/env python
"""
delhtml2json - Delicious HTML Export to JSON Converter

"""
import datetime
import logging
from BeautifulSoup import BeautifulSoup

from codecs import open

try:
    import simplejson
    json = simplejson
except ImportError, e:
    import json

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

##
# Tests
test_input_html="""<!DOCTYPE NETSCAPE-Bookmark-file-1>
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<!-- This is a simplified delicious HTML bookmark export -->
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p><DT><A HREF="http://web.mit.edu/newsoffice/2010/max-flow-speedup-0927.html" ADD_DATE="1285972779" PRIVATE="0" TAGS="graph,network,algorithms,sweet">First improvement of fundamental algorithm in 10 years</A> <!-- [sic] -->
<DT><A HREF="http://en.wikipedia.org/wiki/ANTLR" ADD_DATE="1276760483" PRIVATE="0" TAGS="wikipedia,code,for:s,for:user@domain">ANTLR - Wikipedia, the free encyclopedia</A>
<DD>&quot;These actions are written in the programming language that the recognizer is being generated in.&quot;
</DL><p><!-- s.e.r.v.e.r.yahoo.net uncompressed/chunked Thu Dec 16 01:50:52 UTC 2010 -->
"""

test_output_expected=[
    {"url":     u"http://web.mit.edu/newsoffice/2010/max-flow-speedup-0927.html",
        "title":   u"First improvement of fundamental algorithm in 10 years",
        "tags":    [u"graph", u"network", u"algorithms", u"sweet"],
        #"date":   1285972779,
        "date": datetime.datetime(2010, 10, 1, 17, 39, 39),
        "private": 0,
        "comment": None},
    {"url":     u"http://en.wikipedia.org/wiki/ANTLR",
        "title":   u"ANTLR - Wikipedia, the free encyclopedia",
        "tags":    [u"wikipedia", u"code"],
        #"date":   1276760483,
        "date":   datetime.datetime(2010, 6, 17, 2, 41, 23),
        "private": 0,
        "comment": "&quot;These actions are written in the programming "
                   "language that the recognizer is being generated in.&quot;",
    }
]

import unittest
class TestIt(unittest.TestCase):
    def test_it(self):
        output = [x for x in extract_delicious_bookmarks(test_input_html)]
        self.assertEqual(output, test_output_expected)


def extract_delicious_bookmarks(htmlstr):
    """
    Extract and iterate over bookmarks
    """
    s = htmlstr
    footer_comment = s[ s.rfind("</DL><p><!--")+12 : s.rfind("-->") ].strip()

    export_datestr = footer_comment.split(" uncompressed/chunked ")[1].strip()
    log.info("Exported date: %s" % export_datestr)

    bs = BeautifulSoup(htmlstr)

    link_tag_count = len(bs.findAll("a"))
    log.info("Found %r <a> tags" % link_tag_count)

    link_count = 0
    comment_count = 0

    for dt in bs.findAll("dt"):
        comment = None
        link_count = link_count + 1
        linknode = dt.findChild("a")
        nextnode = dt.findNextSibling()

        if nextnode and nextnode.name == u'dd':
            comment = nextnode.text
            comment_count = comment_count + 1

        yield map_bookmark_node(linknode, comment=comment)

    log.info("Exported %d bookmarks (%d with comments)" % (link_count,comment_count))
    assert link_tag_count == link_count


OVERWRITABLE_ATTRS=['comment']
def map_bookmark_node(link_node, **kwargs):
    l = link_node

    try:
        r = {
            'url': l['href'],
            'title': l.text and l.text.decode('utf-8','replace'),
            'tags': l.has_key("tags") and [t for t in l['tags'].encode('utf-8','replace').split(',')
                                            if t
                                                and not t.startswith("for:") ]
                                      or [],
            'date': datetime.datetime.fromtimestamp(int(l['add_date'])),
            'private': l['private'] == u'1',
        }
    except Exception:
        log.error("EXCEPTION:")
        log.error(l)
        raise

    for kw in OVERWRITABLE_ATTRS:
        if kw in kwargs:
            r[kw] = kwargs[kw]

    return r


def convert_bookmarks_html_to_json(sourcefile_path, output_path):
    
    htmlstr = open(sourcefile_path, "r+").read()
    dest_file = open(output_path, "w")

    json.dump(
        [x for x in extract_delicious_bookmarks(htmlstr)],
        dest_file,
        indent=4)

    log.info("Converted %s -> %s." % (sourcefile_path, output_path))


def parse_delicious_bookmarks(path_):
    with open(path_, 'rb', encoding='UTF-8') as f:
        for node in extract_delicious_bookmarks(f.read()):
            yield node

def main():
    import optparse

    prs = optparse.OptionParser(
        usage="%progname -c <bookmarks.html>")
    prs.add_option("-t","--tests",action="store_true",
                   help="Run tests")

    prs.add_option("-c","--convert",action="store",
                   help="Delicious Bookmarks HTML File")

    prs.add_option("-o","--output",action="store",
                   default="bookmarks.json",
                   help="Destination JSON file (default: ./bookmarks.json)")

    (opts, args) = prs.parse_args()

    if opts.tests:
        import sys
        sys.argv.remove("-t")
        unittest.main()
        exit()

    if opts.convert:
        convert_bookmarks_html_to_json(opts.convert, opts.output)
        exit()

    print prs.print_help()
    

if __name__=="__main__":
    main()
