import datetime
import subprocess
import os
import tempfile

def parse_authlog_yearless_date(datestr, year):
    """
    Augment an auth.log-style yearless date with a year

    :param datestr: datestring (ex ``May 14 01:27:18``)
    :type datestr: str
    :param year: year to add to date
    :type year: int

    :returns: datetime
    """
    if datestr[0:3] == 'Jan':
        raise Exception("careful")
    datestr = "%d %s" % (year, datestr)
    return datetime.datetime.strptime(datestr, "%Y %b %d %H:%M:%S")

def parse_authlog(filename, year=None):
    """
    Parse an auth.log file into event tuples

    :param filename: path to an auth.log file
    :type filename: str
    :param year: year to assume date is under
    :type year: int

    :returns: generator of (datetime, eventstr) tuples

    Auth.log files look like::

        May 14 01:27:18 cdl sshd[27605]: pam_sm_authenticate: Called
        May 14 01:27:18 cdl sshd[27605]: pam_sm_authenticate: username = [username]
        May 14 01:27:18 cdl sshd[27605]: Accepted password for username from ::1 port 51910 ssh2
        May 14 01:27:18 cdl sshd[27605]: pam_unix(sshd:session): session opened for user username by (uid=0)
        May 14 16:21:55 cdl sshd[27605]: pam_unix(sshd:session): session closed for user username
        May 14 16:54:11 cdl gnome-screensaver-dialog: gkr-pam: unlocked login keyring

    """
    if not year:
        year = datetime.datetime.now().year

    with open(filename, 'r+') as f:
        for line in f:
            datestr, rest = line[0:15], line[16:]
            dt = parse_authlog_yearless_date(datestr, year)
            hostname, rest = rest.split(' ',1)
            process, rest = map(str.strip, rest.split(':',1))

            yield (dt, u"%s :: %s :: %s" % (hostname, process, rest))

def parse_authlog_glob(glob_pattern):
    """
    Parse an auth.log file

    :param glob_pattern: File glob to one or more auth.log files
    :type glob_pattern: str

    :returns: generator of (datetime, eventstr) tuples

    """
    tmpfilename = None
    try:
        tmp_hndl, tmpfilename = tempfile.mkstemp()

        # Gunzip if necessary and cat into tmpfile
        subprocess.call("zcat -f %s | grep -v CRON > %s" % (glob_pattern, tmpfilename), shell=True)
        for u in parse_authlog(tmpfilename):
            yield u

    finally:
        if tmpfilename:
            os.remove(tmpfilename)

if __name__=="__main__":
    import sys
    if len(sys.argv) < 2:
        fileglob = '/var/log/auth*'
    else:
        fileglob = sys.argv[1]
    for u in parse_auth_log(fileglob):
        print u