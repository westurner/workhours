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
    datestr = datestr.strip()
    for date_format in (
        "%m/%d/%y %H:%M.%S",
        "%m/%d/%y %H:%M:%S",
        "%m/%d/%y %H:%M",
        "%y-%m-%d %H:%M:%S",
    ):
        try:
            return datetime.strptime(datestr, date_format)
        except ValueError:
            continue
    logging.error("failed to parse: %s", datestr)
    return None


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

        (\\w*): (%d%d/%d%d/%d%d %d%d:%d.%d) ::: (\\w*)  (.*)
        (.*)

        keyvalue\tMM/DD/YY\t\\s*\\d+ command

    """
    terms = line.split(":", 1)
    if len(terms) != 2:
        raise ValueError("session log line is missing its session separator")
    session, rest = (term.strip() for term in terms)
    entry = rest.split(":::", 1)
    if len(entry) != 2:
        raise ValueError("session log line is missing its command separator")
    event_date = parse_date_field(entry[0])
    if event_date is None:
        raise ValueError("session log line has an invalid timestamp")
    session = "{}{}".format(session_prefix or "", session)
    command = entry[1].strip()
    return event_date, "{} ::: {}".format(session, command), session


def parse_sessionlog_line(line, session_prefix=None):
    return parse_sessionlog_line_original(line, session_prefix or "")


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

    with codecs.open(uri, "r", encoding="utf-8") as f:
        for line in filter(lambda x: bool(x.rstrip()), f):
            try:
                yield parse_sessionlog_line(line, session_prefix)
            except Exception as e:
                # log and drop unparsable (with this parser) lines
                logging.exception(e)
                logging.error("Failed to parse: {!r} ({})".format(line, e))
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
