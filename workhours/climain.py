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
    def setUp(self):
        import sys
        sys.argv[0] = 'workhours'
        sys.__exit = sys.exit
        sys.exit = lambda x: x

    def tearDown(self):
        sys.exit = sys.__exit

    def test_workhours_main(self):
        ARG_TESTS = (
            tuple(),
            ("-h",), ("--help",),
            ("-l",), ('--list-source-types',),

            ("--db","sqlite:///test.db","--fs","./tmp"),
            ("--db","sqlite:///test.db","--fs","./tmp",
                "--print-all"),
            ("--db","sqlite:///test.db","--fs","./tmp",
                "-s","log.shell",
                    os.environ.get("USRLOG",
                        os.path.expanduser('~/.usrlog')),
                "--parse",
                "--report=events"),
        )

        log = logging.getLogger('workhours.cli.test')
        for argset in ARG_TESTS:
            log.debug('$ workhours %s' % ' '.join(argset))
            #log.debug(argset)
            try:
                print(argset)
                ret = main(*argset)
                print('ret: %r' % ret)
                print(argset)
                self.assertFalse(ret, argset)
            except Exception, e:
                log.exception(e)
                raise


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
    prs.add_option('-I', '--ipython',
                    dest='ipython',
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
    (opts, args) = prs.parse_args(list(args))

    if not opts.quiet:
        #datestr = datetime.datetime.now().strftime('%y-%m-%d-%H%M.%S')
        if opts.config_file:
            logging.config.fileConfig(opts.config_file,)
        else:
            logging.basicConfig(
                format="%(asctime)s %(levelname)-5.5s [%(name)s][%(threadName)s] %(message)s"
            )

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
        ret = unittest.main()
        return ret
        #exit(unittest.main())

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
        optsval = getattr(opts, attr, None)
        # if the file is in the config file
        if _config.has_option(*configpath):
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
            log.debug("Adding queue %r %r" % (source.type, source) )
            if source.type not in opts._queues:
                opts._queues[source.type] = []
            opts._queues[source.type].append( source )

        return _config, opts


    # Read datastore and task queue configuration from config file

    _config = None
    if opts.config_file is not None:
        _config, opts = read_config_file(opts.config_file, opts)

    from workhours.config import ConfigTaskSource
    if opts.src_queues:
        for (_type, _path) in opts.src_queues:
            if _type not in QUEUES:
                raise Exception(
                    "queue type %r not supported: %r" % (_type, _path))
            if _type not in opts._queues:
                opts._queues[_type] = []
            task_src = ConfigTaskSource(
                    type=_type,
                    label=None, # TODO
                    url=os.path.expanduser(_path),
                    host='localhost', # TODO
                    user='user',
            )
            opts._queues[_type].append(task_src)

    if opts.list_source_types:
        for queue_name in QUEUES:
            print(queue_name)
        return 0
        #exit(0)


    def debug_conf(opts):
        log.debug("sql.url: %r", opts.sqldb_url)
        log.debug("fs.url: %r", opts.fs_url)
        log.debug("es.url: %r", opts.esdb_url)
        #log.debug("queues:\n%s", json.dumps(opts._queues, indent=2))

    debug_conf(opts)


    if opts.dump_events_table:
        opts.reports.append('events')

    if opts.parse or opts.reports:
        from workhours.models.files import initialize_fs
        if opts.fs_url is None:
            prs.error("Must specify a fs url")
            # return -3
        opts._filestore = initialize_fs(os.path.expanduser(opts.fs_url))


    if opts.parse:
        if not opts._queues:
            prs.error("--parse specified without any queues (see -c and/or -s)")
            # raise Exception()
        if any(x[0] for x in opts._queues.iteritems()):
            from workhours.tasks.events import events_table_worker
            for result in events_table_worker(
                                opts.sqldb_url,
                                opts._queues,
                                filestore=opts.fs_url):
                #print(result, file=opts._output)
                pass

    def _do_events_report(opts):
        log.debug("_do_events_report")
        from workhours.reports.events import dump_events_table
        csv_path = opts._filestore.add_path('events.csv', None)
        for line in dump_events_table(opts.sqldb_url):
            print(line, file=opts._output)

    from workhours.reports.gaps import create_gap_csv
    from workhours import models
    def _do_gap_report(opts):
        log.debug("_do_gap_report")
        opts.csv_path = reportsdir.add_path('gaps.csv', None)
        create_gap_csv(models.Event, opts.csv_path, opts.gaptime)

    REPORTS = {
        'gap': _do_gap_report,
        'events': _do_events_report,
    }


    if opts.list_report_types:
        for k, v in REPORTS.iteritems():
            print("%s := %r" % (k, v))
        #exit(0)


    if opts.reports:
        reportsdir = opts._filestore.mkdir('reports')
    for report in opts.reports:
        reportfunc = REPORTS.get(report)
        if reportfunc is None:
            raise Exception("report type %r unsupported" % report)
        result = reportfunc(opts)
        print(result, file=opts._output)

    if opts.ipython:
        from IPython import embed
        from workhours.models.sql import open_db
        from workhours.models.sql.tables import setup_mappers
        from workhours.models import Base
        if opts.sqldb_url is None:
            raise Exception("--db url must be specified")
        meta = open_db(
                opts.sqldb_url,
                setup_mappers=setup_mappers,
                create_tables_on_init=False,
                )
        s = meta.Session()
        embed(user_ns=locals())

    return 0

if __name__=="__main__":
    main()
