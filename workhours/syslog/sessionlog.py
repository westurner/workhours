#!/usr/bin/env python
from __future__ import print_function

"""
Parse usrlog.sh bash / zsh shell history logs
"""

import collections
import codecs
import logging
import subprocess

from datetime import datetime
from itertools import ifilter

import arrow

log = logging.getLogger('parse_sessionlog')
log.setLevel(logging.DEBUG)


def get_local_timezone():
    output = subprocess.check_output('date +%z')
    if not output:
        return ''
    return output


def parse_date_field(datestr):
    dt = None
    _datestr = datestr.strip()
    try:
        dt = datetime.strptime(_datestr, "%m/%d/%y %H:%M.%S")
    except ValueError, e:
        # log.exception(e)
        try:
            dt = datetime.strptime(_datestr, "%y-%m-%d %H:%M:%S")
        except ValueError as e:
            dt = arrow.get(_datestr)
            logging.exception("{}: failed to parse: {}".format(e, datestr))
            pass
    return dt


def parse_sessionlog_line_original(line, session_prefix=''):
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
    terms = [w.strip() for w in line.split(':', 1)]
    session, rest = terms[0], len(terms) > 1 and terms[1:] or ''  # TODO
    # session, rest = map(str.strip, line.split(': ',1))
    date = cmd = cmdstr = dt = None
    if rest:
        rest_terms = [w.strip() for w in rest.split(':::', 1)]
        date, cmd = (rest_terms[0],
                     (len(rest_terms) > 1 and
                      u''.join(x.decode('utf8', errors='ignore')
                               for x in rest_terms[1:])))
        dt = parse_date_field(date)
        cmdstr = u'%s ::: %s' % (session, cmd)
    return (dt, cmdstr, session)


def do_pyparsing_things():
    from pyparsing import (
        Literal,
        Optional,
        Or,
        ParseException,
        ParserElement,
        Suppress,
        White,
        Word,
        alphanums,
        nums,
        restOfLine,
    )

    def build_date_pattern():
        """
        one form of iso8601::

            %y-%m-%dT%H:%M:%S%z
        """
        year = tz = Word(nums, exact=4)
        dash = Literal('-')
        colon = Literal(':')
        t = Literal('T')
        month = day = hour = minute = second = Word(nums, exact=2)

        pattern = (year + dash + month + dash + day +
                t + hour + colon + minute + colon + second +
                dash + tz)
        return pattern

    iso8601date = build_date_pattern()


    def build_pyparsing_patterns():

        ParserElement.setDefaultWhitespaceChars(" \t")

        unicodePrintables = u''.join(unichr(c) for c in xrange(65536)
                                    if not unichr(c).isspace())
        # urichars = alphanum + "-_/\:#?"
        urichars = unicodePrintables

        tab = Suppress(Literal('\t')).parseWithTabs()
        colon = Suppress(Literal(':'))
        tab_or_colon = Suppress(Or(tab, (White() + colon + White())))
        triplecolon = Suppress(Literal(':::'))
        tab_or_triple_colon = Suppress(Or(tab, White() + triplecolon + White()))

        date = Word(nums + "-_/\.T").setName('date_end')

        digit_or_other = White() + Or(Word(nums), Word(alphanums + "#"))

        # command = Word(unicodePrintables)
        command = restOfLine.setName('command')
        key = Word(urichars).setName('key')

        oldstyle_pattern = (
            key
            + tab_or_colon
            + date
            + tab_or_triple_colon
            + digit_or_other
            + command)

        pound_space = Suppress(Optional(Literal('# ')))  # . #######

        shelln = Word(' ' + nums).setName('shelln')

        twospaces = Suppress(Word(' ', exact=2))  # todo: development of the logfmt was on nb-mb1 and create
        date_end = iso8601date.setName('date_end')
        date_start = iso8601date.setName('date_start')
        newstyle_pattern_with_shelln = (
            pound_space +
            date_end + tab + key + tab + shelln + tab + command)

        newstyle_pattern_with_shelln_and_startdate = (
            pound_space +
            date_end + tab + key + tab + shelln + tab + date_start
            + twospaces + command)

        newstyle_pattern_without_numbers = (
            pound_space +
            date_end + tab + key + tab + command)

        newstyle_pattern_without_numbers_with_startdate = (
            pound_space +
            date_end + tab + key + tab + date_start + twospaces + command)

        hostname = Word(alphanums + '-_.').setName('hostname')
        username = Word(alphanums + '-_.').setName('username')
        path_after = Word(urichars).setName("path_after")
        command_sep = Literal('$$')

        """
        # 2015-02-06T01:27:26-0600	#57pFg92gUr0	/Users/W/-wrk/-ve27/workhours/src/workhours	 1625  	2015-02-06T00:26:39-0600	nb-mb1	W	$$	less $_USRLOG
        """

        newstyle = (
            pound_space +
            date_end + tab +
            key + tab +
            path_after + tab +
            shelln + tab +
            date_start + tab +
            hostname + tab +
            username + tab +
            command_sep + tab +
            command
        ).parseWithTabs()

        return (
            newstyle,
            list()
        )

        return (
            (oldstyle_pattern,
            ('key', 'date', 'shelln', 'command')),
            (newstyle_pattern_with_shelln,
            ('enddate', 'key', 'shelln', 'command')),
            (newstyle_pattern_with_shelln_and_startdate,
            ('enddate', 'key', 'shelln', 'startdate', 'command')),
            (newstyle_pattern_without_numbers,
            ('enddate', 'key', 'command')),
            (newstyle_pattern_without_numbers_with_startdate,
            ('enddate', 'key', 'startdate', 'command')),
        )


    SESSIONLOG_PATTERNS = build_pyparsing_patterns()


    def parse_sessionlog_line_pyparsing(line, session_prefix=None):
        for pattern, fields in SESSIONLOG_PATTERNS:
            try:
                log.debug((fields, pattern))
                tokens = pattern.parseString(line)
                log.debug(tokens.asList())
                return dict(zip(fields, tokens.asList()))  # TODO: field mapping
            except ParseException as e:
                log.exception(e)
                pass

            raise ParseException(repr(line))

import json

class UsrlogLine(object):
    def __init__(self, line):
        self.line = line
        self.fields = None
        self.dict = self.parse_line(line)

    @staticmethod
    def parse_fields(line):
        fields = line.split("\t", 8)
        return fields

    @classmethod
    def parse_line(cls, line):
        fields = cls.parse_fields(line)
        if len(fields) < 4:
            return
        # TODO: handle "^# " and '$$'
        _dict = collections.OrderedDict((
            ("l", line),
            ("fields", fields),

            ("datestr", fields[0].lstrip('# ')),
            ("id", fields[1]),
            ("path", fields[2]),
            ("histstr", '\t'.join(fields[3:])),
            ("histstrl", fields[3:]),
        #))
        #_dict.update((
            # these seem to vary from platform to platform
            # but should be handled by the \t-separated usrlog log format
            ("histnstr", fields[3]),    # int or "#note"
            ("histdate", (fields[4] if len(fields) > 4 else None)),
            ("histhostname", (fields[5] if len(fields) > 5 else None)),
            ("histuser", (fields[6] if len(fields) > 6 else None)),
            ("histcmd", (fields[8:] if len(fields) > 8 else None)),
        ))
        return _dict

    @classmethod
    def build_properties(cls, _dict):
        if _dict['l'].startswith('# '):
            has_comment_prefix = True
        if _dict['fields'][7] == '$$':
            has_cmd_prefix = True
        _dict['date'] = cls.parse_date(_dict['datestr'])
        _dict['histn'] = cls.to_int(_dict['histnstr'], default=None)
        _dict['histdate'] = cls.parse_date(_dict['histdate'])

        histcmd = _dict['histcmd']
        if histcmd is None:
            histstrl = _dict['histstrl']
            log.debug(('parse_usrlog_dict', (histcmd, histstrl), _dict))
            raise Exception((histcmd, histstrl))

        return _dict

    @staticmethod
    def to_int(maybeintstr, default=NotImplemented):
        try:
            return int(maybeintstr) if maybeintstr else maybeintstr
        except ValueError:
            if default is not NotImplemented:
                return default
            raise


    def parse_date(self):
        datestr = self.dict['date']
        date = parse_date_field(datestr)
        return date

    def __str__(self):
        return str(json.dumps(self.dict, indent=2))

    def __repr__(self):
        return str(json.dumps(self.dict, indent=2))


def parse_sessionlog(uri=None, session_prefix='', **kwargs):
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

    with codecs.open(uri, 'r+', encoding='utf-8') as f:
        for line in ifilter(lambda x: bool(x.rstrip()), f):
            try:
                yield UsrlogLine(line)
            except Exception, e:
                # log and drop unparsable (with this parser) lines
                logging.exception(e)
                logging.error(u"Failed to parse: %r (%s)" % (line, e))
                continue


def main():
    """
    parse_sessionlog main() method
    """
    import sys
    import os
    if len(sys.argv) < 2:
        filename = os.path.join(os.environ['HOME'], '-usrlog.log')
    else:
        filename = sys.argv[1]
    for pair in parse_sessionlog(filename):
        print(repr(pair))
        #print(u' : '.join(str(x) for x in pair))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
