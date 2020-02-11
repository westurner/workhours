#!/usr/bin/env python
# encoding: utf-8

"""
parse_find_printf

Parse find printf output into tuples
::

    $ find $path -printf '%T@\t%s\t%u\t%Y\t%p\n'

Find printf formatters
::

    $ man find | cat | pyline "line.startswith((' '*14)+'%') and (line[14:20].strip(), line[21:].rstrip().replace('File\'s ','').lstrip())"

    %%	A literal percent sign.
    %a	last access time in the format returned by the C `ctime' function.
    %Ak	last  access  time  in the format specified by k, which is either `@' or a
    %b	The  amount  of disk space used for this file in 512-byte blocks. Since disk space
    %c	last status change time in the format returned by the C `ctime' function.
    %Ck	last status change time in the format specified by k, which is the same as
    %d	depth in the directory tree; 0 means the file is a command line argument.
    %D	The device number on which the file exists (the st_dev field of struct  stat),  in
    %f	name with any leading directories removed (only the last element).
    %F	Type of the filesystem the file is on; this value can be used for -fstype.
    %g	group name, or numeric group ID if the group has no name.
    %G	numeric group ID.
    %h	Leading  directories  of file's name (all but the last element).  If the file name
    %H	Command line argument under which file was found.
    %i	inode number (in decimal).
    %k	The  amount  of  disk  space  used for this file in 1K blocks. Since disk space is
    %l	Object of symbolic link (empty string if file is not a symbolic link).
    %m	permission  bits  (in  octal).  This option uses the `traditional' numbers
    %M	permissions (in symbolic form, as for ls).  This directive is supported  in
    %n	Number of hard links to file.
    %p	name.
    %P	name  with  the name of the command line argument under which it was found
    %s	size in bytes.
    %S	sparseness.  This is calculated as (BLOCKSIZE*st_blocks  /  st_size).   The
    %t	last modification time in the format returned by the C `ctime' function.
    %Tk	last modification time in the format specified by k, which is the  same  as
    %u	user name, or numeric user ID if the user has no name.
    %U	numeric user ID.
    %y	type (like in ls -l), U=unknown type (shouldn't happen)
    %Y	type (like %y), plus follow symlinks: L=loop, N=nonexistent
"""


from collections import namedtuple
from datetime import datetime

_FindEvent = namedtuple("FindEvent", ("date", "size", "user", "type", "url"))

# ('date', '%T@', 'time in fractional seconds since'),
# ('size', '%s', 'size in bites'),
# ('user', '%u', 'username'),
# ('type', '%Y', 'file type'),
# ('name', '%p', 'name')


class FindEvent(_FindEvent):
    def __str__(iterable):
        return "\t".join("%s" % attr for attr in iterable)


import logging

log = logging.getLogger("parse_find_printf")  # TODO


def _parse_find_printf(printf_iter, output, log=log):
    """
    mainfunc

    :param printf_iter: iterable of printf output lines
    :param output: output stream

    """
    for record in printf_iter:
        date, size, user, type_, name = record[:-1].split("\t", 4)
        try:
            date = float(date)
            date = datetime.fromtimestamp(date)
        except Exception as e:
            raise
        yield FindEvent(date, size, user, type_, name)


def parse_find_printf(uri, *args, **kwargs):
    with open(args[0]) as f:
        return _parse_find_printf(f, *args, **kwargs)


import unittest


class Test_parse_find_printf(unittest.TestCase):
    TEST_INPUT = """
1352793657.5742202430	s	d user /tmp
1319767478.3939859440	s	d user /tmp/path
1282865184.4291842300	s	f user ~/tildepath
1282865184.4211835980	s	d user ./relpath
1282865184.4211835981	s	f user ./relpath/1
"""

    def test_parse_find_printf(self):
        for event in parse_find_printf(TEST_INPUT.split("\n")):
            log.debug(event)


def main():
    import optparse
    import logging

    prs = optparse.OptionParser(
        usage="./%prog",
        description="Convert find printf on stdin to event tuples",
    )

    prs.add_option(
        "-v", "--verbose", dest="verbose", action="store_true",
    )
    prs.add_option(
        "-q", "--quiet", dest="quiet", action="store_true",
    )
    prs.add_option(
        "-t", "--test", dest="run_tests", action="store_true",
    )

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

    import sys

    for event in parse_find_printf(sys.stdin, sys.stdout):
        log.debug(event)


if __name__ == "__main__":
    main()
