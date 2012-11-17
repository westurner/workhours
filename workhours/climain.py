#!/usr/bin/env python
#encoding: utf-8
"""
event aggregation
"""

import logging
log = logging.getLogger('workhours')

from workhours.models.files import TempDir


def main():
    import sys
    import logging
    from optparse import OptionParser
    from pprint import pformat


    prs = OptionParser()

    prs.add_option('-c','--config',
                    dest='config_file',
                    action='store')

    prs.add_option('-p','--parse',
                    dest='parse',
                    action='store_true',
                    help='Parse')

    prs.add_option('--fs', '--task-storage',
                    dest='fs_uri',
                    action='store',
                    default='local',
                    help='Path for task file storage')
    prs.add_option('-e', '--eventsdb',
                    dest='eventsdb_uri',
                    action='store',
                    help='Filepath for the aggregate events database')

    prs.add_option('--ffb','--firefox-bookmarks',
                    dest='firefox_bookmarks',
                    action='append',
                    default=[],
                    help='FF places.sqlite path(s) ',)
    prs.add_option('--ffh','--firefox-history',
                    dest='firefox_history',
                    action='append',
                    default=[],
                    help='FF places.sqlite path(s) ',)


    prs.add_option('--wkb','--webkit-bookmarks',
                    dest='webkit_bookmarks',
                    action='append',
                    default=[],
                    help='WebKit bookmark JSON path(s)')
    prs.add_option('--wkh','--webkit-history',
                    dest='webkit_history',
                    action='append',
                    default=[],
                    help='WebKit History path(s)',)

    prs.add_option('--delb','--delicious-bookm',
                    dest='delicious_bookmarks',
                    action='append',
                    default=[],
                    help='Delicious bookmark JSON path(s)')

    prs.add_option('--ttl', '--trac-timeline',
                    dest='trac_timelines',
                    action='append',
                    default=[],
                    help='Trac timeline html path(s)')
    prs.add_option('--ttu', '--trac-username',
                    dest='usernames',
                    action='append',
                    default=[],
                    help='Trac usernames to include',)

    prs.add_option('-s','--shelllog',
                    dest='log_shell',
                    action='append',
                    default=[],
                    help='.session_log-style path(s)')

    prs.add_option('-w','--wtmp',
                    dest='log_wtmp',
                    action='append',
                    default=[],
                    help='wtmp path glob(s)')

    prs.add_option('-a','--authlog',
                    dest='log_auth',
                    action='append',
                    default=[],
                    help='auth.log path glob(s)')


    prs.add_option('-o', '--reports-path',
                    dest='reports_path',
                    action='store',
                    #default='workhours-%s.csv' % datestr,
                    help='File to write output csv into')

    prs.add_option('-g','--gap-report',
                    dest='gap_report',
                    action='store_true',
                    default=False,
                    help='Generate a report with gaps between events')
    prs.add_option('-G','--gaptime',
                    dest='gaptime',
                    action='store',
                    default=15,
                    help="Minute gap to detect between entries")

    prs.add_option('-d','--dump',
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

    (opts, args) = prs.parse_args()

    if not opts.quiet:
        #datestr = datetime.datetime.now().strftime('%y-%m-%d-%H%M')
        logging.basicConfig()

        if opts.verbose:
            logging.getLogger().setLevel(logging.DEBUG)

            if opts.verbose > 1:
                logging.getLogger('sqlalchemy').setLevel(logging.INFO)

    if opts.run_tests:
        sys.argv = [sys.argv[0]] + args
        import unittest
        exit(unittest.main())

    eventsdb_uri = opts.eventsdb_uri
    filestore_path = opts.fs_uri

    from workhours.tasks import QUEUES

    if opts.config_file:
        from ConfigParser import ConfigParser

        c = ConfigParser()
        c.read(opts.config_file)

        if c.has_option('main','fs.uri'):
            if filestore_path:
                logging.warn("config fs.uri overridden by cmdline")
            else:
                filestore_path = c.get('main','fs.uri')
        if c.has_option('main','eventsdb.uri'):
            if eventsdb_uri:
                logging.warn("config eventsdb.uri overridden by cmdline")
            else:
                eventsdb_uri = c.get('main','eventsdb.uri')

        opt_queues = {}
        for queue in sorted(set(QUEUES.keys()).intersection(set(c.sections()))): # !
            opt_queues[queue] = ifilter(bool, (v.strip() for k,v in c.items(queue)))
    else:
        opt_queues = dict( (q, getattr(opts, q.replace('.','_'))) for q in QUEUES )


    filestore = TempDir(path=filestore_path, create=True)

    log.debug("Database: %r", eventsdb_uri)
    log.debug("Filestore: %r", filestore_path)
    log.debug("Queues:\n%s", pformat(opt_queues))
    if opts.parse and any(x[0] for x in opt_queues.iteritems()):
        from workhours import tasks
        work workhours.models.sql import initiqlize_sql
        tasks.populate_events_table(
            eventsdb_uri,
            opt_queues,
            fs=filestore,
        )

    if opts.dump_events_table:
        from workhours.reports.events import dump_events_table
        from workhours.models import Session
        dump_events_table(opts.eventsdb_uri)

    if opts.gap_report:
        from workhours.reports.gaps import create_gap_csv
        reportsdir = filestore.mkdir('reports')
        csv_path = reportsdir.add_path('gaps.csv', None)
        from workhours import models
        create_gap_csv(models.Event, csv_path,  opts.gaptime)

if __name__=="__main__":
    main()
