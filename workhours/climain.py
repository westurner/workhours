#!/usr/bin/env python
#encoding: utf-8
"""
workhours event aggregation CLI
"""

import logging
log = logging.getLogger() #'workhours')


import unittest
import os
class TestWorkhoursCLI(unittest.TestCase):
    def test_workhours_main(self):
        ARG_TESTS = (
            tuple(),
            ("--help",),
            ("-e","sqlite:///:memory:",),
            ("-e","sqlite:///:memory:","-p",),
            ("-e","sqlite:///:memory:","-p","--shell-log",
                os.environ.get("USRLOG",
                    os.path.expanduser('~/.usrlog'))),
            ("-e","sqlite:///:memory:","-p",)
        )

        for argset in ARG_TESTS:
            log.debug("test_main: %r" % (argset))
            try:
                main(*argset)
            except Exception, e:
                log.exception(e)

import sys
import logging
import optparse
from pprint import pformat
from collections import OrderedDict
import json
from ConfigParser import ConfigParser

def CommandlineOptionParser(*args,**kwargs):
    prs = optparse.OptionParser(
        usage="%prog [-c conf] [--fs path] [--db uri]] "
              "<options> [-s source path+] [-r report+]",
        description="""event aggregation CLI"""
    )

    prs.add_option('-c','--config',
                    dest='config_file',
                    action='store')

    prs.add_option('--db', '--eventsdb',
                    dest='eventsdb_uri',
                    action='store',
                    help='Filepath for the aggregate events database')

    prs.add_option('--fs', '--task-storage',
                    dest='fs_uri',
                    action='store',
                    help='Path where task and reports files will be stored')

    prs.add_option('-l', '--list-source-types',
                    dest='list_source_types',
                    action='store_true')

    prs.add_option('-s', '--src',
                    nargs=2,
                    dest='src_queues',
                    action='append',
                    help="Type and filename tuples "
                         "(ex. 'shell.log ./.usrlog')")
    prs.add_option('-P','--parse',
                    dest='parse',
                    action='store_true',
                    help='Parse')


    prs.add_option('-u', '--username',
                    dest='usernames',
                    action='append',
                    default=[],
                    help='Usernames to include',)


    prs.add_option('--list-report-types',
                    dest='list_report_types',
                    action='store_true',
                    help='List supported reports')
    prs.add_option('-r','--report',
                    dest='reports',
                    action='append',
                    type='choice',
                    choices=['gap','events'], # TODO
                    default=[],
                    help='Generate a report type')

    prs.add_option('-o','--output-file',
                    dest='output',
                    action='store',
                    default='-',
                    help="Output file (default: '-' for stdout)")
    prs.add_option('-O','--output-format',
                    dest='output_format',
                    action='store',
                    default=None,
                    help="Output format <csv|json> (default: None)")

    prs.add_option('-G','--gaptime',
                    dest='gaptime',
                    action='store',
                    type='float',
                    default=15,
                    help="Minute gap to detect between entries")

    prs.add_option('-p', '--print-all',
                    dest='dump_events_table',
                    action='store_true',
                    help='Dump the events table to stdout')


    prs.add_option('-v', '--verbose',
                    dest='verbose',
                    action='count',
                    default=0, )
    prs.add_option('-q', '--quiet',
                    dest='quiet',
                    action='store_true',)
    prs.add_option('-t', '--test',
                    dest='run_tests',
                    action='store_true',)

    return prs

import codecs
def main(*args):

    prs = CommandlineOptionParser()
    args = args if args else sys.argv[1:]
    (opts, args) = prs.parse_args()

    if not opts.quiet:
        #datestr = datetime.datetime.now().strftime('%y-%m-%d-%H%M.%S')
        logging.basicConfig()

        if opts.verbose:
            logging.getLogger().setLevel(logging.DEBUG)

            if opts.verbose > 1:
                logging.getLogger('sqlalchemy').setLevel(logging.INFO)

    if opts.run_tests:
        sys.argv = [sys.argv[0]] + args
        import unittest
        exit(unittest.main())

    #if opts.file is '-':
    #    _input_file = sys.stdin
    #else:
    #    _input_file = codecs.open(opts.file, 'r', encoding='utf8')

    if opts.output is '-':
        opts._output = sys.stdout
    else:
        opts._output = codecs.open(opts.output, 'w', encoding='utf8')
    _output = opts._output

    from workhours.tasks import QUEUES
    from workhours.models.files import TempDir

    opts._queues = OrderedDict()

    _config = None
    if opts.config_file:

        c = _config = ConfigParser()
        c.read(opts.config_file)

        # filesystem storage uri
        if _config.has_option('main','fs.uri'):
            if opts.fs_uri:
                logging.warn("config fs.uri overridden by cmdline")
            else:
                opts.fs_uri = _config.get('main','fs.uri')

        # events database url
        if _config.has_option('main','eventsdb.url'):
            if opts.eventsdb_uri:
                logging.warn("config eventsdb.url overridden by cmdline")
            else:
               opts.eventsdb_uri = _config.get('main','eventsdb.url')

        # elasticsearch url
        if _config.has_option('mas','esdb.uri'):
            if opts.esdb_uri:
                logging.warn("config esdb.uri overridden by cmdline")
            else:
                opts.esdb_uri = _config.get('main', 'esdb.uri')

        # read supported config file sections
        for queue_name in (
            sorted( set(QUEUES.keys()) & set(_config.sections()))):
            config_items = filter(bool,
                    (os.path.expanduser(v.strip())
                        for k,v in c.items(queue_name)))
            if queue_name not in opts._queues:
                opts._queues[queue_name] = []
            opts._queues[queue_name].extend( config_items )


    if opts.src_queues:
        for (_type, _path) in opts.src_queues:
            if _type not in QUEUES:
                raise Exception(
                    "queue type %r not supported: %r" % (_type, _path))
            if _type not in opts._queues:
                opts._queues[_type] = []
            opts._queues[_type].append(os.path.expanduser(_path))

    #else:
    #    opts._queues = OrderedDict(
    #        (queue_name, getattr(opts, queue_name.replace('.','_')))
    #            for queue_name in QUEUES )


    if opts.list_source_types:
        for queue_name in QUEUES:
            print(queue_name)
        exit(0)

    opts.filestore = TempDir(
                        path=os.path.expanduser(opts.fs_uri),
                        create=True)

    def debug_conf(opts):
        log.debug("eventsdb: %r", opts.eventsdb_uri)
        log.debug("fs.uri: %r", opts.fs_uri)
        log.debug("queues:\n%s", json.dumps(opts._queues, indent=2))

    debug_conf(opts)

    if opts.parse and any(x[0] for x in opts._queues.iteritems()):
        from workhours import tasks
        for result in tasks.populate_events_table(
                            opts.eventsdb_uri,
                            opts._queues,
                            fs=filestore):
            print(result, opts._output)

    def _do_events_report(opts):
        from workhours.reports.events import dump_events_table
        csv_path = reportsdir.add_path('events.csv', None)
        for line in dump_events_table(opts.eventsdb_uri):
            print(line, _output)

    from workhours.reports.gaps import create_gap_csv
    from workhours import models
    def _do_gap_report(opts):
        csv_path = reportsdir.add_path('gaps.csv', None)
        create_gap_csv(models.Event, opts.csv_path, opts.gaptime)

    REPORTS = {
        'gap': _do_gap_report,
        'events': _do_events_report,
    }

    if opts.list_report_types:
        for k, v in REPORTS.iteritems():
            print("%s := %r" % (k, v))
        exit(0)

    if opts.reports:
        reportsdir = opts.filestore.mkdir('reports')
    for report in opts.reports:
        reportfunc = REPORTS.get(report)
        if reportfunc is None:
            raise Exception("report type %r unsupported" % report)
        result = reportfunc(opts)

if __name__=="__main__":
    main()
