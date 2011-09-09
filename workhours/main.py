#!/usr/bin/env python
#encoding: utf-8
"""
event aggregation
"""
import codecs
import csv
import datetime
import urlparse
from itertools import ifilter
from sqlalchemy import MetaData, DateTime, Table, Column, Integer, Unicode, UnicodeText
from sqlalchemy import UniqueConstraint, ForeignKey
from sqlalchemy.orm import sessionmaker, mapper, relation #, eagerload
from workhours import setup_engine
from workhours.models.sqla_utils import MutationDict, JSONEncodedDict

import logging
log = logging.getLogger()

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

    @classmethod
    def from_uhm(cls, source, event_, **kwargs):
        _kwargs = {}
        _kwargs['task_id'] = kwargs.get('task_id')
        if hasattr(event_, 'to_event_row'):
            event = cls(source, *event_.to_event_row(), **_kwargs)
        elif isinstance(event_, dict):
            _kwargs.update(event_)
            event = cls(source, **_kwargs)
        # punt
        elif hasattr(event_, '__iter__'):
            event = cls(source, *event_, **_kwargs)
        else:
            print type(event_)
            print dir(event_)
            print event_
            raise Exception()

        return event

    def _to_event_row(self):
        return (self.date, self.source, self.url)

    def _to_txt_row(self):
        return ("%s/%s/%s\t%s\t%s\t%s" % (
                self.task.queue.type,
                self.task.id,
                self.task.date,
                self.date,
                self.url,
                self.title)).encode('utf8','replace')

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
        s = session
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

                # UniqueConstraint('date','url','task_id', name='uix_event_date_url_taskid'), # TODO
                # breaks w/ webkit history on date !?
#                UniqueConstraint('source','date','url', 'task_id', name='uix_event_source_task_id'),
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
        try:
            print e._to_txt_row()
        except UnicodeEncodeError, error:
            print type(error.object), error.encoding
            print error.object.encode('utf8','replace')
            raise

from workhours.future import OrderedDict

from workhours.firefox.history import parse_firefox_history, parse_firefox_bookmarks
from workhours.webkit.bookmarks import parse_webkit_bookmarks
from workhours.webkit.history import parse_webkit_history
from workhours.delicious.bookmarks import parse_delicious_bookmarks
from workhours.trac.timeline import parse_trac_timeline
from workhours.syslog.sessionlog import parse_sessionlog
from workhours.syslog.wtmp import parse_wtmp_glob
from workhours.syslog.authlog import parse_authlog_glob

DEFAULT_FILES = lambda x: ( x['uri'], )

def sqlite_files(x):
    return (x['uri'], '%s-journal' % x['uri'])

QUEUES=OrderedDict( (
    ( "firefox.bookmarks", (parse_firefox_bookmarks, sqlite_files, ) ),
    ( "firefox.history", (parse_firefox_history, sqlite_files, ), ),
    ( "webkit.bookmarks", (parse_webkit_bookmarks, DEFAULT_FILES, ), ),
    ( 'webkit.history', (parse_webkit_history, sqlite_files, ), ),
    ( "delicious.bookmarks", (parse_delicious_bookmarks, DEFAULT_FILES, ), ),
    ( "trac.timelines", (parse_trac_timeline, DEFAULT_FILES, ), ),
    ( "log.shell", (parse_sessionlog, DEFAULT_FILES, ), ),
    ( "log.wtmp", (parse_wtmp_glob, DEFAULT_FILES, ), ),
    ( "log.auth", (parse_authlog_glob, DEFAULT_FILES, ), ),
) )


import tempfile
import shutil
import os

class TempDir(object):
    def __init__(self, path=None, create=True, dir='.'):
        if not path:
            if create:
                self.path = tempfile.mkdtemp(suffix='',prefix='tmp',dir=dir)
            else:
                self.path = os.path.join(dir, 'tasktmp')
            return
        else:
            self.path = path
            if create:
                os.mkdir(self.path) 

    def copy_here(self, filename, dest_path=None):
        if dest_path:
            dest = os.path.join(self.path, dest_path)
        else:
            dest = self.path

        dest_path=os.path.join(dest, os.path.basename(filename))
        shutil.copy2(filename, dest_path)
        return dest_path

    def mkdir(self, path):
        mkpath = os.path.join(self.path, path)
        os.mkdir(mkpath)
        return TempDir(path=mkpath, create=False)

    #def __del__(self):
        # if managed:
        #     shutil.rmtree(self.path)
    #    pass

# TODO: more elegant generalization
def populate_events_table(eventsdb_uri, task_queues, output_filename, gaptime):

    engine = setup_engine(eventsdb_uri)
    meta = setup_mappers(engine)
    meta.bind = engine

    # Create tables
    meta.create_all()
    meta.Session = sessionmaker(bind=engine)

    tmpdir = TempDir(dir='./')

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
            s.flush()
       
            task_dirname = '%s_%s' % (task.id, queue_k)
            task_dir = tmpdir.mkdir(task_dirname )

            # Run Tasks
            try:
                files_ = [task_dir.copy_here(f) for f in files(task.args)]
                print files_
                uri = files_[0] 
                for event_ in parsefunc_iter(uri=uri):
                    try:
                        log.debug("%s.Parsing %s : %s" % (task.id, type(event_), event_))

                        event = Event.from_uhm(queue_k, event_, task_id=task.id)
                        if event.url:
                            place = Place.get_or_create(event.url, session=s)
                            event.place_id = place.id
                        s.add(event)
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

            try:
                cw.writerow(e)
            except UnicodeDecodeError:
                e = list(e)
                e[2] = e[2].decode('utf8','replace') # ...
                cw.writerow(e)
            except UnicodeEncodeError, error:
                print type(error.object), error.encoding
                print error.object.encode('utf8','replace')
                e = list(e)
                e[2] = unicode(e[2]).encode('utf8','replace')
                e[3] = unicode(e[3]).encode('utf8','replace')
                print e
                cw.writerow(e)
            ltime = e.date


def main():
    import sys
    import logging
    from optparse import OptionParser
    from pprint import pformat

    datestr = datetime.datetime.now().strftime('%y-%m-%d-%H%M')

    prs = OptionParser()

    prs.add_option('-c','--config',
                    dest='config_file',
                    action='store')

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
        logging.basicConfig()

        if opts.verbose:
            logging.getLogger().setLevel(logging.DEBUG)

            if opts.verbose > 1:
                logging.getLogger('sqlalchemy').setLevel(logging.INFO)

    if opts.run_tests:
        sys.argv = [sys.argv[0]] + args
        import unittest
        exit(unittest.main())

    if opts.config_file:
        from ConfigParser import ConfigParser

        c = ConfigParser()
        c.read(opts.config_file)

        opt_queues = {}
        for queue in sorted(set(QUEUES.keys()).intersection(set(c.sections()))): # !
            opt_queues[queue] = ifilter(bool, list(v.strip() for k,v in c.items(queue)))
    else:
        opt_queues = dict( (q, getattr(opts, q.replace('.','_'))) for q in QUEUES )

    log.debug("Queues:\n%s", pformat(opt_queues))

    if any(x[0] for x in opt_queues.iteritems()):
        populate_events_table(
            opts.eventsdb,
            opt_queues,
            opts.output_csv,
            int(opts.gaptime)
        )

    if opts.dump_events_table:
        dump_events_table(opts.eventsdb)

if __name__=="__main__":
    main()
