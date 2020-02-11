#!/usr/bin/env python


from datetime import datetime

import codecs
import logging
import subprocess

"""
Grep Shell history logs
"""

log = logging.getLogger("parse_sessionlog")


def get_local_timezone():
    output = subprocess.check_output("date +%z")
    if not output:
        return ""
    return output


def parse_date_field(datestr):
    dt = None
    _datestr = datestr
    datestr = datestr.strip()
    try:
        dt = datetime.strptime(datestr, "%m/%d/%y %H:%M.%S")
    except ValueError as e:
        # log.exception(e)
        try:
            dt = datetime.strptime(datestr, "%y-%m-%d %H:%M:%S")
        except ValueError as e:
            logging.error("failed to parse: {}".format(datestr))
            pass
    return dt


def parse_sessionlog_line_original(line, session_prefix=""):
    """
    Parse a line from a sessionlog file

    :param line: Line to parse
    :type line: str
    :param session_prefix: Optional session ID prefix
    :type session_prefix: str

    :returns: (datetime, eventstr)


    ::
        keyvalue: MM/DD/YY :::   1234  echo >> /dev/null << EOF
        line continuation
        EOF

        (\w*): (%d%d/%d%d/%d%d %d%d:%d.%d) ::: (\w*)  (.*)
        (.*)

        keyvalue\tMM/DD/YY\t\s*\d+ command

    """
    terms = [w.strip() for w in line.split(":", 1)]
    session, rest = terms[0], len(terms) > 1 and terms[1:] or ""  # TODO
    # session, rest = map(str.strip, line.split(': ',1))
    date = cmd = cmdstr = dt = None
    if rest:
        rest_terms = [w.strip() for w in rest.split(":::", 1)]
        date, cmd = (
            rest_terms[0],
            len(rest_terms) > 1
            and "".join(
                x.decode("utf8", errors="ignore") for x in rest_terms[1:]
            ),
        )
        dt = parse_date_field(date)
        cmdstr = "%s ::: %s" % (session, cmd)
    return (dt, cmdstr, session)


def build_pyparsing_pattern():
    from pyparsing import (
        Word,
        White,
        Optional,
        ZeroOrMore,
        OneOrMore,
        Or,
        Literal,
        nums,
        alphanums,
        printables,
    )

    unicodePrintables = "".join(
        chr(c) for c in range(65536) if not chr(c).isspace()
    )
    # urichars = alphanum + "-_/\:#?"
    urichars = unicodePrintables

    tab = Literal("\t")
    colon = Literal(":")
    tab_or_colon = White() + Or(tab, colon) + White()
    triplecolon = Literal(":::")
    tab_or_triple_colon = White() + Or(tab, triplecolon) + White()

    date = Word(nums + "-_/\.T")

    digit_or_other = White() + Or(Word(nums), Word(alphanums + "#"))

    command = Word(unicodePrintables)
    key = Word(unicodePrintables)

    pattern = (
        key
        + tab_or_colon
        + date
        + tab_or_triple_colon
        + digit_or_other
        + command
    )

    return pattern


PATTERN = build_pyparsing_pattern()


def parse_sessionlog_line(line, session_prefix=None):

    from pprint import pformat as pp

    print(pp(dir(PATTERN)))
    tokens = PATTERN.parse_string(line)
    # TODO: Dict
    return tokens.asList()


def parse_sessionlog(uri=None, session_prefix="", **kwargs):
    """
    Parse a .session_log file that looks something like::

         session_id: ---- date ---- ::: cmd
        oZ3OjCzcGyo: 06/08/10 19:28 ::: sh ./workhours.sh
        oZ3OjCzcGyo: 06/08/10 19:29 ::: sh ./workhours.sh
        oZ3OjCzcGyo: 06/08/10 19:29 ::: sh ./workhours.sh

    - Skip all but the first line of multi-line entries
    - Silently drop lines that fail to parse

    :param log_filename: filename of the logfile to parse
    :type log_filename: str
    :param session_prefix: ie. hostname prefix for session id
    :type session_prefix: str

    :returns: generator of (datetime, command string) tuples

    """

    with codecs.open(uri, "r+", encoding="utf-8") as f:
        for line in filter(lambda x: bool(x.rstrip()), f):
            try:
                yield parse_sessionlog_line(line, session_prefix)
            except Exception as e:
                # log and drop unparsable (with this parser) lines
                logging.exception(e)
                logging.error("Failed to parse: %r (%s)" % (line, e))
                continue


def main():
    """
    parse_sessionlog main() method
    """
    import sys
    import os

    if len(sys.argv) < 2:
        filename = os.path.join(os.environ["HOME"], "-usrlog.log")
    else:
        filename = sys.argv[1]
    for pair in parse_sessionlog(filename):
        print(" : ".join(str(x) for x in pair))
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
