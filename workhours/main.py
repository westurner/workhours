#!/usr/bin/env python
#encoding: utf-8
"""
event aggregation
"""

import datetime
import logging

from itertools import ifilter
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

log = logging.getLogger('workhours')

from workhours.models import Event, Place, Task, TaskQueue, setup_mappers
from workhours.future import OrderedDict

from workhours.firefox.history import parse_firefox_history
from workhours.firefox.history import parse_firefox_bookmarks
from workhours.webkit.bookmarks import parse_webkit_bookmarks
from workhours.webkit.history import parse_webkit_history
from workhours.delicious.bookmarks import parse_delicious_bookmarks
from workhours.trac.timeline import parse_trac_timeline
from workhours.syslog.sessionlog import parse_sessionlog
from workhours.syslog.wtmp import parse_wtmp_glob
from workhours.syslog.authlog import parse_authlog_glob

DEFAULT_FILES = lambda x: ( x['uri'], )
SQLITE_FILES =  lambda x: ( x['uri'],
                            '%s-journal' % x['uri'])

QUEUES=OrderedDict( (
    ( "firefox.bookmarks", (parse_firefox_bookmarks, SQLITE_FILES, ) ),
    ( "firefox.history", (parse_firefox_history, SQLITE_FILES, ), ),
    ( "webkit.bookmarks", (parse_webkit_bookmarks, DEFAULT_FILES, ), ),
    ( 'webkit.history', (parse_webkit_history, SQLITE_FILES, ), ),
    ( "delicious.bookmarks", (parse_delicious_bookmarks, DEFAULT_FILES, ), ),
    ( "trac.timelines", (parse_trac_timeline, DEFAULT_FILES, ), ),
    ( "log.shell", (parse_sessionlog, DEFAULT_FILES, ), ),
    ( "log.wtmp", (parse_wtmp_glob, DEFAULT_FILES, ), ),
    ( "log.auth", (parse_authlog_glob, DEFAULT_FILES, ), ),
) )




from workhours.models.files import TempDir

# TODO: more elegant generalization
def populate_events_table(eventsdb_uri, task_queues, fs):

    engine = create_engine(eventsdb_uri)
    meta = setup_mappers(engine)
    meta.bind = engine

    # Create tables
    meta.create_all()
    meta.Session = sessionmaker(bind=engine)

    s = meta.Session()
    for queue_k, tasks in task_queues.iteritems():
        s.begin(subtransactions=True)
        queue = TaskQueue( queue_k )
        s.add(queue)
        s.commit()

        parsefunc_iter, files = QUEUES[queue_k]

        for argset in tasks:
            log.debug("Task: %s" % str(argset))
            s.begin(subtransactions=True)
            task = Task( queue.id, args={'uri':argset} ) #!
            s.add(task)
            s.flush() # get task.id

            _log = logging.getLogger('%s.%s' % (queue_k, task.id))

            task_dirname = '%s_%s' % (task.id, queue_k)
            task_dir = fs.mkdir(task_dirname)

            # Run Tasks
            try:
                files_ = [task_dir.copy_here(f) for f in files(task.args)]
                uri = files_[0]
                for event_ in parsefunc_iter(uri=uri):
                    try:
                        _log.debug("%s : %s" % (type(event_), event_))
                        event = Event.from_uhm(queue_k, event_, task_id=task.id)
                        if event.url:
                            place = Place.get_or_create(event.url, session=s)
                            event.place_id = place.id
                        s.add(event)
                        # TODO:
                        # s.flush() # get event.id
                        # sunburnt.index(event + **addl_attrs)
                        # pyes.insert( **event.to_dict() )
                    except Exception, e:
                        task.status = 'err'
                        task.statusmsg = str(e)
                        s.flush()
                        raise
                s.commit()
            except Exception, e:
                log.error(e)
                raise
        s.commit()
    s.commit()

    #create_gap_csv(meta, output_filename, gaptime)




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

    prs.add_option('-g','--gaptime',
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
        populate_events_table(
            eventsdb_uri,
            opt_queues,
            fs=filestore,
        )

    if opts.dump_events_table:
        from workhours.reports.events import dump_events_table
        dump_events_table(opts.eventsdb_uri)

    if opts.gaptime:
        from workhours.reports.gaps import create_gap_csv
        reportsdir = filestore.mkdir('reports')
        csv_path = reportsdir.add_file('gaps.csv')
        create_gap_csv(csv_path,  opts.gaptime)

if __name__=="__main__":
    main()
