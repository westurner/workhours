#!/usr/bin/env python
#encoding: utf-8
"""
event aggregation
"""
import csv
import datetime
from sqlalchemy import MetaData, DateTime, Table, Column, Integer, Unicode, UnicodeText
from sqlalchemy.orm import sessionmaker, mapper #, relation, eagerload
from workhours import setup_engine

from codecs import open

class Event(object):
    def __init__(self, source, datetime, url, title=None, description=None):
        self.source = source
        self.datetime = datetime
        self.url = url
        self.title = title
        self.description = description

    def _to_event_row(self):
        return (self.datetime, self.source, self.url)

    def __unicode__(self):
        return ("Event( %s %s %s)" % (self.datetime, self.source, self.url))

    def __str__(self):
        return unicode(self)


_MAPPED = False
def setup_mappers(engine):
    """
    Setup SQLAlchemy mappers for the aggregate events database

    :param engine: SQLAlchemy engine
    :type engine: SQLAlchemy engine

    :returns: SQLAlchemy meta
    """
    meta = MetaData()

    global _MAPPED # FIXME:
    if not _MAPPED:
        _MAPPED = True
        events_tbl = Table('events', meta,
            Column(u'id', Integer(), primary_key=True, nullable=False),
                Column(u'source', Unicode(length=255), index=True),
                Column(u'datetime', DateTime(), index=True),
                Column(u'url', UnicodeText()),
                    # TODO:
                    Column(u'title', UnicodeText()),
                    Column(u'description', UnicodeText()),
        )

        mapper(Event, events_tbl)

    return meta


def dump_events_table(dburi):
    """
    Print Events Table to stdout

    :param dburi: SQLAlchemy database URI
    :type dburi: str
    """
    engine = setup_engine(dburi)
    meta = setup_mappers(engine)
    meta.bind = engine
    meta.Session = sessionmaker(bind=engine)
    s = meta.Session()

    for e in s.query(Event).order_by(Event.datetime).all():
        print e


# TODO: more elegant generalization
def populate_events_table(eventsdb_uri,
                        ff_hist_paths,
                        trac_timeline_paths,
                        usernames,
                        sessionlog_filenames,
                        wtmp_globs,
                        authlog_globs,
                        output_filename, gaptime):
    engine = setup_engine(eventsdb_uri)
    meta = setup_mappers(engine)
    meta.bind = engine

    # Create tables
    meta.create_all()
    meta.Session = sessionmaker(bind=engine)

    s = meta.Session()

    from workhours.firefox.history import parse_firefox_history
    for ffpath in ff_hist_paths or []:
        for e in parse_firefox_history(ffpath):
            s.add(Event('firefox', *e))
        s.flush()

    from workhours.trac.timeline import parse_trac_timeline
    for path in trac_timeline_paths:
        for e in parse_trac_timeline(open(path,'rb',encoding='UTF-8'), usernames):
            s.add(Event('trac', *e))
        s.flush()

    from workhours.syslog.sessionlog import parse_sessionlog
    for sspath in sessionlog_filenames or []:
        for e in parse_sessionlog(sspath, session_prefix=''):
            s.add(Event('shell', *e))
        s.flush()

    from workhours.syslog.wtmp import parse_wtmp_glob
    for wtmp_glob in wtmp_globs or []:
        for e in parse_wtmp_glob(wtmp_glob):
            s.add(Event('wtmp', *e))
        s.flush()

    from workhours.syslog.authlog import parse_authlog_glob
    for authlog_glob in authlog_globs or []:
        for e in parse_authlog_glob(authlog_glob):
            s.add(Event('authlog', *e))
        s.flush()

    s.commit()

    create_gap_csv(meta, output_filename, gaptime)


def create_gap_csv(meta, output_filename, gaptime=15):
    """
    Generate a CSV with '----' lines where events are
    separated by more than ``gaptime`` minutes

    :param meta: SQLAlchemy meta (with meta.Session)
    :type meta: SQLAlchemy meta
    :param output_filename: path to the CSV output file
    :type output_filename: str
    :param gaptime: Minimum gap size
    :type gaptime: int

    :returns: None
    """
    s = meta.Session()
    with open(output_filename,'w+') as f:
        cw = csv.writer(f)
        cw.writerow(('datetime','source','visit_date'))

        ltime = None
        for e in ( s.query(Event).
                order_by(Event.datetime).
                all() ):
            ctime, source, url = cur_row = e._to_event_row()
            if ltime and (ltime + datetime.timedelta(minutes=gaptime)) < ctime:
                cw.writerow(('--------','-------','------'))
                cw.writerow(cur_row)
                ltime = ctime


def main():
    import sys
    import logging
    from optparse import OptionParser
    
    datestr = datetime.datetime.now().strftime('%y-%m-%d-%H%M')

    prs = OptionParser()

    prs.add_option('-f', '--ff-hist',
                    dest='firefox_history',
                    action='append',
                    default=[],
                    help='FF places.sqlite path(s) ',)

    prs.add_option('-l', '--trac-timeline',
                    dest='trac_timelines',
                    action='append',
                    default=[],
                    help='Trac timeline html path(s)')
    prs.add_option('-u', '--username',
                    dest='usernames',
                    action='append',
                    default=[],
                    help='Trac usernames to include',)

   
    prs.add_option('-s','--sessionlog',
                    dest='sessionlog',
                    action='append',
                    help='.session_log-style paths')

    prs.add_option('-w','--wtmp',
                    dest='wtmp_globs',
                    action='append',
                    help='wtmp path glob(s)')

    prs.add_option('-a','--authlog',
                    dest='authlog_globs',
                    action='append',
                    help='auth.log path glob(s)')

    prs.add_option('-e', '--eventsdb',
                    dest='eventsdb',
                    action='store',
                    default='events-%s.sqlite' % datestr,
                    help='Filepath for the aggregate events database')

    prs.add_option('-g','--gaptime',
                    dest='gaptime',
                    action='store',
                    default=15,
                    help="Minute gap to detect between entries")
    prs.add_option('-o', '--output-csv',
                    dest='output_csv',
                    action='store',
                    default='workhours-%s.csv' % datestr,
                    help='File to write output csv into')


    prs.add_option('-d','--dump',
                    dest='dump_events_table',
                    action='store_true',
                    help='Dump the events table to stdout')


    prs.add_option('-v', '--verbose',
                    dest='verbose',
                    action='store_true',)
    prs.add_option('-q', '--quiet',
                    dest='quiet',
                    action='store_true',)
    prs.add_option('-t', '--test',
                    dest='run_tests',
                    action='store_true',)

    (opts, args) = prs.parse_args()

    if not opts.quiet:
        logging.basicConfig()

        if opts.verbose:
            logging.getLogger().setLevel(logging.DEBUG)

    if opts.run_tests:
        sys.argv = [sys.argv[0]] + args
        import unittest
        exit(unittest.main())

    if any( (opts.firefox_history,
            opts.trac_timelines,
            opts.sessionlog,
            opts.wtmp_globs,
            opts.authlog_globs) ):

        populate_events_table(
            opts.eventsdb,
            opts.firefox_history,
            opts.trac_timelines,
            opts.usernames,
            opts.sessionlog,
            opts.wtmp_globs,
            opts.authlog_globs,
            opts.output_csv,
            int(opts.gaptime)
        )

    if opts.dump_events_table:
        dump_events_table(opts.eventsdb)

if __name__=="__main__":
    main()
