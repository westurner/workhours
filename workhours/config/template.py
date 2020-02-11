#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
workhours_config_template
"""
import sys
import logging
log = logging.getLogger()

class ConfigTemplate(object):

    def generate(self, source_types=None, exclude=None):
        """
        run shell commands for source types

        Args:
            source_types (iterable): list of source types to find
            exclude (iterable): iterable of patterns to match
        Returns:
            StringIO: Templated config template
        """


    def write(self, path):
        templateio = self.generate()
        try:
            with codecs.open(path, encoding='utf-8') as f:
                # TODO: dotfiles: vim: ctrl-a beginning of line (like .bashrc)
                f.write(templateio)
        except Exception as e:
            raise


def workhours_config_template(path="workhours.ini"):
    """
    mainfunc
    """
    c = ConfigTemplate()
    c.write_to(path)

    return True


import unittest
class Test_workhours_config_template(unittest.TestCase):
    def test_workhours_config_template(self):
        c = ConfigTemplate()
        c.write_to(path)
        self.assertTrue(output)

    def test_template(self):
        # TODO
        pass


def main(*args):
    import optparse
    import logging
    import sys

    prs = optparse.OptionParser(usage="%prog: [args]")

    prs.add_option('-v', '--verbose',
                    dest='verbose',
                    action='store_true',)
    prs.add_option('-q', '--quiet',
                    dest='quiet',
                    action='store_true',)
    prs.add_option('-t', '--test',
                    dest='run_tests',
                    action='store_true',)

    args = args and list(args) or sys.argv[1:]
    (opts, args) = prs.parse_args(args)

    if not opts.quiet:
        logging.basicConfig()

        if opts.verbose:
            logging.getLogger().setLevel(logging.DEBUG)

    if opts.run_tests:
        sys.argv = [sys.argv[0]] + args
        import unittest
        sys.exit(unittest.main())

    output = workhours_config_template()
    return 0

if __name__ == "__main__":
    sys.exit(main())
