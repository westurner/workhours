#!/usr/bin/env python
"""
Grep WTMP logs
"""
import tempfile
import subprocess
import os
import datetime
from pyutmp import UtmpFile

to_datetime = lambda x: datetime.datetime.fromtimestamp(x)


def parse_wtmp(uri=None):
    """
    Parse a wtmp file into event tuples

    :param filename: Path to a wtmp file
    :type filename: str

    :returns: generator of (datetime, eventstr) tuples

    """
    filename = uri
    for u in UtmpFile(filename):
        d = u.__dict__.copy()
        dt = to_datetime(d.pop("ut_time"))
        type = d.pop("ut_type")
        user = d.pop("ut_user")

        logstr = u"%s(%s) %s" % (
            user,
            type,
            ", ".join("%s: %r" % (k, d[k]) for k in sorted(d.keys()) if d[k]),
        )

        yield (dt, logstr)


def parse_wtmp_glob(uri=None):
    """
    Parse one or more wtmp files into event tuples

    :param glob_pattern: Glob to one or more wtmp files
    :type glob_pattern: str

    :returns: generator of (datetime, eventstr) tuples

    """
    glob_pattern = uri
    tmpfilename = None
    try:
        tmp_hndl, tmpfilename = tempfile.mkstemp()

        # Gunzip if necessary and cat into tmpfile
        subprocess.call(
            "zcat -f %s > %s" % (glob_pattern, tmpfilename), shell=True
        )
        for u in parse_wtmp(tmpfilename):
            yield u

    finally:
        if tmpfilename:
            os.remove(tmpfilename)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        fileglob = "/var/log/wtmp*"
    else:
        fileglob = sys.argv[1]
    for u in parse_wtmp_glob(fileglob):
        print u
