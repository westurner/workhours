#!/usr/bin/env python
#encoding: utf-8
from __future__ import print_function
"""
workhours event aggregation CLI
"""

import logging
log = logging.getLogger('workhours.cli') #'workhours')


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
            log.debug("test_main: %r" % argset)
            try:
                main(*argset)
            except Exception, e:
                log.exception(e)

import sys
import logging
import optparse
from pprint import pformat
from workhours.future import OrderedDict
import workhours.models.json as json
from ConfigParser import ConfigParser

def CommandlineOptionParser(*args,**kwargs):
    prs = optparse.OptionParser(
        usage="%prog [-c conf] [--fs path] [--db uri]] "
              "<options> [-s source path+] [-r report+]",
        description="""event aggregation CLI"""
    )

    prs.add_option('-c','--config',
                    dest='config_file',
                    action='store',
                    help='Queue and storage .ini configuration file')

    prs.add_option('--db', '--sqldb-url',
                    dest='sqldb_url',
                    action='store',
                    help='Filepath for the aggregate events database')
    prs.add_option('--fs', '--fs-url',
                    dest='fs_url',
                    action='store',
                    help='Path where task and reports files will be stored')
    prs.add_option('--es', '--esdb-url',
                    dest='esdb_url',
                    action='store',
                    help='Elasticsearch index URL')


    prs.add_option('-l', '--list-source-types',
                    dest='list_source_types',
                    action='store_true')
    prs.add_option('-s', '--src',
                    nargs=2,
                    dest='src_queues',
                    action='append',
                    help="Task(queue_name, filename)"
                         "tuples to append to queues"
                         '(ex. "shell.log ./.usrlog")')
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

import os
import codecs
def main(*args):
    """workhours CLI main function

    Parse args or sys.argv[1:] into opts and execute tasks

    opts
        .sqldb_url = str    #   from db_main.url
        .esdb_url = str
        .fs_url = str
        ._queues[queue_name] = list
    """

    prs = CommandlineOptionParser()
    args = args if args else sys.argv[1:]
    (opts, args) = prs.parse_args()

    if not opts.quiet:
        #datestr = datetime.datetime.now().strftime('%y-%m-%d-%H%M.%S')
        if '_CFG' in os.environ:
            logging.config.fileConfig(os.environ['_CFG'])
        else:
            logging.basicConfig()

        logging.addLevelName(3, 'TRACE')

        if opts.verbose:
            logging.getLogger().setLevel(logging.DEBUG)

            if opts.verbose > 1:
                logging.getLogger().setLevel(3)
            #if opts.verbose > 1:
            #    logging.getLogger('sqlalchemy').setLevel(logging.INFO)

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
        opts._output = (opts._output
                        or codecs.open(opts.output, 'w', encoding='utf8'))

    from workhours.tasks.events import QUEUES
    from workhours.config import read_queues_from_config

    opts._queues = getattr(opts, '_queues', OrderedDict())

    def get_value(_config, attr, configpath, opts):
        # if the file is in the config file
        if _config.has_option(*configpath):
            optsval = getattr(opts, attr, None)
            if optsval:
                log.warn("config %r overridden by cmdline" % attr)
            else:
                optsval = _config.get(*configpath)
        return optsval


    def read_config_file(config_file, opts=None, log=logging, **kwargs):
        """read a workhours .ini config file

        write settings into an optparse.Values object,
        log.warn when commandline and configfile settings

        """
        _config = ConfigParser()
        _config.read(config_file)

        opts.fs_url = get_value(_config,
                        'fs_url',   ('main','fs.url'), opts)
        opts.sqldb_url = get_value(_config,
                        'sqldb_url', ('main', 'db_main.url'), opts)
        opts.esdb_url = get_value(_config,
                        'esdb_url', ('main','esdb.url'), opts)


        # append queues from config to opts
        for source in read_queues_from_config(_config):
            #logging.debug( (queue_name, key, path) )
            if source.type not in opts._queues:
                opts._queues[source.type] = []
            opts._queues[source.type].append( source )

        return _config, opts


    # Read datastore and task queue configuration from config file

    _config = None
    if opts.config_file is not None:
        _config, opts = read_config_file(opts.config_file, opts)

    from workhours.config import Source
    if opts.src_queues:
        for (_type, _path) in opts.src_queues:
            if _type not in QUEUES:
                raise Exception(
                    "queue type %r not supported: %r" % (_type, _path))
            if _type not in opts._queues:
                opts._queues[_type] = []
            opts._queues[_type].append(
                Source(_type,None,os.path.expanduser(_path)))

    if opts.list_source_types:
        for queue_name in QUEUES:
            print(queue_name)
        exit(0)

    from workhours.models.files import initialize_fs
    if opts.fs_url is None:
        log.error("Must specify a fs url")
        exit(0)
    opts._filestore = initialize_fs( os.path.expanduser(opts.fs_url) )

    def debug_conf(opts):
        log.debug("sql.url: %r", opts.sqldb_url)
        log.debug("fs.url: %r", opts.fs_url)
        log.debug("es.url: %r", opts.esdb_url)
        #log.debug("queues:\n%s", json.dumps(opts._queues, indent=2))

    debug_conf(opts)

    if opts.parse and any(x[0] for x in opts._queues.iteritems()):
        from workhours.tasks.events import events_table_worker
        for result in events_table_worker(
                            opts.sqldb_url,
                            opts._queues,
                            filestore=opts._filestore):
            print(result, file=opts._output)

    def _do_events_report(opts):
        from workhours.reports.events import dump_events_table
        csv_path = opts._filestore.add_path('events.csv', None)
        for line in dump_events_table(opts.sqldb_url):
            print(line, file=opts._output)

    from workhours.reports.gaps import create_gap_csv
    from workhours import models
    def _do_gap_report(opts):
        opts.csv_path = reportsdir.add_path('gaps.csv', None)
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
        reportsdir = opts._filestore.mkdir('reports')
    for report in opts.reports:
        reportfunc = REPORTS.get(report)
        if reportfunc is None:
            raise Exception("report type %r unsupported" % report)
        result = reportfunc(opts)
        print(result, file=opts._output)

if __name__=="__main__":
    main()
