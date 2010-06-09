from datetime import datetime
from itertools import ifilter
import logging

log = logging.getLogger('parse_sessionlog')

def parse_sessionlog_line(line, session_prefix=''):
    """
    Parse a line from a sessionlog file

    :param line: Line to parse
    :type line: str
    :param session_prefix: Optional session ID prefix
    :type session_prefix: str

    :returns: (datetime, eventstr)
    """
    session, rest = map(str.strip, line.split(': ',1))
    date, cmd = map(str.strip, rest.split(':::'))
    dt = datetime.strptime(date, "%m/%d/%y %H:%M")
    cmdstr = u'%s:%s: ::: %s' % (session_prefix, session, cmd)
    return (dt, cmdstr)


def parse_sessionlog(log_filename, session_prefix=''):
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

    with open(log_filename,'r+') as f:
        for line in ifilter(lambda x: bool(x.rstrip()), f):            
            try:
                yield parse_sessionlog_line(line, session_prefix)
            except Exception, e:
                # log and drop unparsable (with this parser) lines
                logging.error("Failed to parse: %r (%s)" % (line, e))
                continue


if __name__=="__main__":
    import sys
    import os
    if len(sys.argv) < 2:
        filename = os.path.join(os.environ['HOME'], '.session_log')
    else:
        filename = sys.argv[1]
    for pair in parse_sessionlog(filename):
        print '---'.join(map(str, pair))