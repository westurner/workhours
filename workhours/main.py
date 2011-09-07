#!/usr/bin/env python
#encoding: utf-8
"""
event aggregation
"""
import codecs
import csv
import datetime
import urlparse
from sqlalchemy import MetaData, DateTime, Table, Column, Integer, Unicode, UnicodeText
from sqlalchemy import UniqueConstraint, ForeignKey
from sqlalchemy.orm import sessionmaker, mapper, relation #, eagerload
from workhours import setup_engine
from workhours.models.sqla_utils import MutationDict, JSONEncodedDict


class _Base(object):
    def getattrs(self, *attrs):
        if attrs:
            return (getattr(self, attr) for attr in attrs)
        return (getattr(self,attr) for attr in self.columns)


class TaskQueue(_Base):
    def __init__(self, type, label=None, uri=None):
        self.type = type
        self.label = label
        self.uri = uri


class Task(_Base):
    def __init__(self, queue_id, args, date=None, state=None, statemsg=None):
        self.queue_id = queue_id
        self.args = args
        self.date = date or datetime.datetime.now()
        self.state = state
        self.statemsg = statemsg


class Event(_Base):
    def __init__(self, source=None,
                        date=None,
                        url=None,
                        title=None,
                        meta=None,
                        place_id=None,
                        task_id=None,
                        *args,
                        **kwargs):
        self.source = source
        self.date = date
        self.url = url
        self.title = title
        self.meta = meta
        self.place_id = place_id
        self.task_id = task_id

    def _to_event_row(self):
        return (self.date, self.source, self.url)

    def _to_txt_row(self):
        return u"%s/%s/%s\t%s\t%s\t%s" % (
                self.task.queue.type,
                self.task.id,
                self.task.date,
                self.date,
                self.url,
                self.title)

    def __unicode__(self):
        return ("Event( %s %s %s )" % (self.date, self.source, self.url))

    def __str__(self):
        return unicode(self)

class Place(_Base):
    def __init__(self, url_, eventcount=0, meta=None):
        self.url=url_
        self.eventcount=eventcount
        self.meta=meta

        urlp = urlparse.urlparse(self.url)
        for attr in ('scheme','port','netloc','path','query','fragment'):
            setattr(self, attr, getattr(urlp, attr))
        del urlp
        # self.meta = # TODO


    @classmethod
    def get_or_create(cls, url, session=None, *args, **kwargs):
        s = session or meta.Session()
        obj = s.query(cls).filter(cls.url==url).first()
        if obj:
            obj.eventcount += 1
            s.flush()
        else:
            try:
                obj = cls(url, *args, **kwargs)
                s.add(obj)
            except Exception:
                raise
        return obj


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
        queues_tbl = Table('queues', meta,
            Column('id', Integer(), primary_key=True, nullable=False),
                Column('type', Unicode(length=255), index=True),
                Column('uri', UnicodeText()),
                Column('label', UnicodeText(), unique=True),
                Column('date', DateTime(), onupdate=datetime.datetime.now, index=True),
        )
        mapper(TaskQueue, queues_tbl)

        tasks_tbl = Table('tasks', meta,
            Column('id', Integer(), primary_key=True, nullable=False),
                Column('queue_id', Integer(), ForeignKey(queues_tbl.c.id), index=True),
                Column('args', MutationDict.as_mutable(JSONEncodedDict)),
                Column('label', UnicodeText()),
                Column('date', DateTime(), onupdate=datetime.datetime.now, index=True),
        )
        mapper(Task, tasks_tbl, properties={
            'queue': relation(TaskQueue, backref='tasks')
        })

        places_tbl = Table('places', meta, 
            Column('id', Integer(), primary_key=True, nullable=False),
                Column('url', UnicodeText(), index=True),

                Column('scheme', Unicode()),
                Column('netloc', UnicodeText(), index=True),
                Column('port', Integer(), ),
                Column('path', UnicodeText(), index=True),
                Column('query', UnicodeText(), index=True),
                Column('fragment', UnicodeText()),

                Column('eventcount', Integer()),
                Column('meta', MutationDict.as_mutable(JSONEncodedDict)),
        )
        mapper(Place, places_tbl)

        # TODO: tags

        events_tbl = Table('events', meta,
            Column('id', Integer(), primary_key=True, nullable=False),
                Column('source', Unicode(), index=True),
                Column('date', DateTime(), index=True),
                Column('url', UnicodeText()),
                Column('title', UnicodeText()),
                Column('meta', UnicodeText()),

                Column('place_id', Integer(), ForeignKey(places_tbl.c.id), nullable=True),
                Column('task_id', Integer(), ForeignKey(tasks_tbl.c.id), nullable=False),

                UniqueConstraint('date','url', name='uix_event_date_url'), # TODO
                UniqueConstraint('date','url','task_id', name='uix_event_task_id'),
        )
        mapper(Event, events_tbl, properties={
            'task': relation(Task, backref='events'),
            'place': relation(Place, backref='events'),
            #'queue': relation(TaskQueue, backref='events'),
        })

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

    for e in s.query(Event).order_by(Event.date):
        print e._to_txt_row()


from workhours.firefox.history import parse_firefox_history
from workhours.webkit.bookmarks import parse_webkit_bookmarks
from workhours.delicious.bookmarks import parse_delicious_bookmarks
from workhours.trac.timeline import parse_trac_timeline
from workhours.syslog.sessionlog import parse_sessionlog
from workhours.syslog.wtmp import parse_wtmp_glob
from workhours.syslog.authlog import parse_authlog_glob
EVENT_COLUMNS=-1
QUEUES={
    "firefox.history": (parse_firefox_history, EVENT_COLUMNS, ),
    "webkit.bookmarks": (parse_webkit_bookmarks, EVENT_COLUMNS, ),
    "delicious.bookmarks": (parse_delicious_bookmarks, EVENT_COLUMNS, ),
    "trac.timeline": (parse_trac_timeline, EVENT_COLUMNS, ),
    "log.shell": (parse_sessionlog, EVENT_COLUMNS, ),
    "log.wtmp": (parse_wtmp_glob, EVENT_COLUMNS, ),
    "log.auth": (parse_authlog_glob, EVENT_COLUMNS, ),
}


# TODO: more elegant generalization
def populate_events_table(eventsdb_uri, task_queues, output_filename, gaptime):

    engine = setup_engine(eventsdb_uri)
    meta = setup_mappers(engine)
    meta.bind = engine

    # Create tables
    meta.create_all()
    meta.Session = sessionmaker(bind=engine)

    s = meta.Session()

    for queue_k, tasks in task_queues.iteritems():
        queue = TaskQueue( queue_k )
        s.add(queue)
        s.flush()

        parsefunc_iter, attrs = QUEUES[queue_k]

        for argset in tasks:
            task = Task( queue.id, args={'uri':argset} ) #!
            s.add(task)
            s.flush()
            # parse source
            for event_ in parsefunc_iter(**task.args ):
                try:
                    if isinstance(event_, dict):
                        kwargs = event_
                        kwargs['task_id'] = task.id
                        event = Event(**kwargs)
                    else:
                        args = event_
                        event = Event(*args , task_id=task.id)

                    place = Place.get_or_create(event_['url'], session=s)
                    event.place_id = place.id
                    s.add(event)
                except Exception, e:
                    task.status = 'err'
                    task.statusmsg = str(e)
                    s.flush()
                    raise
            s.flush()
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
    with codecs.open(output_filename,'w+',encoding='utf-8') as f:
        cw = csv.writer(f)
        rows=('date','source','url','title')
        cw.writerow(rows)

        ltime = None
        gaprow = len(rows)*('--------',)
        for e in (s.query(
                    *(getattr(Event,attr) for attr in rows))
                    .order_by(Event.date) ):
            if ltime and (ltime + datetime.timedelta(minutes=gaptime)) < e.date:
                cw.writerow(gaprow)
            cw.writerow(e)
            ltime = e.date


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

    prs.add_option('-k','--webkit-bookm',
                    dest='webkit_bookmarks',
                    action='append',
                    default=[],
                    help='WebKit bookmark JSON path(s)')

    prs.add_option('--delicious-bookm',
                    dest='delicious_bookmarks',
                    action='append',
                    default=[],
                    help='Delicious bookmark JSON path(s)')

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
                    default=[],
                    help='.session_log-style paths')

    prs.add_option('-w','--wtmp',
                    dest='wtmp_globs',
                    action='append',
                    default=[],
                    help='wtmp path glob(s)')

    prs.add_option('-a','--authlog',
                    dest='authlog_globs',
                    action='append',
                    default=[],
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

    queues = {
        'firefox.history': opts.firefox_history,
        'webkit.bookmarks': opts.webkit_bookmarks,
        'delicious.bookmarks': opts.delicious_bookmarks,
        'trac.timeline': opts.trac_timelines,
        'log.shell': opts.sessionlog,
        'log.wtmp': opts.wtmp_globs,
        'log.auth': opts.authlog_globs
    }

    if opts.verbose:
        print queues

    if any(queues.itervalues()):
        populate_events_table(
            opts.eventsdb,
            queues,
            opts.output_csv,
            int(opts.gaptime)
        )

    if opts.dump_events_table:
        dump_events_table(opts.eventsdb)

if __name__=="__main__":
    main()
