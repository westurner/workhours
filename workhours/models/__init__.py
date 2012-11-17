#!/usr/bin/env python
#encoding: utf-8
"""
event aggregation models
"""
import datetime
import urlparse
from sqlalchemy import MetaData, DateTime, Table, Column, Integer, Unicode, UnicodeText
from sqlalchemy import ForeignKey
#from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import mapper, relation, object_session
#from sqlalchemy.orm import sessionmaker, eagerload
#from sqlalchemy.ext.associationproxy import association_proxy

from workhours.models.sqla_utils import MutationDict, JSONEncodedDict, clear_mappers

__ALL__=['TaskQueue',
         'Task',
         'Event',
         'Place',
         'setup_mappers']

import logging
log = logging.getLogger('models')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def open_db(dburi,
            setup_mappers=setup_mappers,
            destructive_recover=False,
            munge_mappers=[]):
    """
    Open a single session
    """

    try:
        engine = create_engine(dburi)
    except Exception:
        if dburi.startswith('sqlite') and destructive_recover:
            from workhours.models.sqlite_utils import commit_uncommitted_transactions
            commit_uncommitted_transactions(dburi)
            engine = create_engine(dburi)
        else:
            raise

    if munge_mappers:
        clear_mappers(munge_mappers)

    meta = setup_mappers(engine)
    meta.engine = engine
    meta.Session = sessionmaker(bind=engine)
    return meta


def Session(uri):
    meta = open_db(uri,
                    destructive_recover=False)
    return meta.Session()


class _Base(object):
    def getattrs(self, *attrs):
        if attrs:
            return (getattr(self, attr) for attr in attrs)
        return (getattr(self,attr) for attr in self.columns)

    @classmethod
    def select_columns(cls, attrs, order_by='date', session=None):
        s=session or object_session(cls)
        return (s.query(
                    *(getattr(cls,attr) for attr in attrs) )
                .order_by( getattr(cls,order_by)) )

    def __str__(self):
        return unicode(self).encode('utf-8')


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
    _pyes_schema = {
        'source': {
            'boost': 1.0,
            'index': 'analyzed',
            'store': 'yes',
            'type': u'string',
            'term_vector':'with_positions_offsets'},
        'date': {
            'boost': 1.0,
            'index': 'analyzed',
            'store': 'yes',
            'type': u'date',
        },
        'url': {
            'boost': 1.0,
            'index': 'analyzed',
            'store': 'yes',
            'type': 'string',
        },
        'title': {
            'boost': 1.0,
            'index': 'analyzed',
            'store': 'yes',
            'type': 'string',
        },
        'meta': {
            'boost': 1.0,
            'index': 'analyzed',
            'store': 'yes',
            'type': 'string',
        },
        'place_id': {
            'boost': 1.0,
            'index': 'analyzed',
            'store': 'yes',
            'type': 'string',
        },
        'task_id': {
            'boost': 1.0,
            'index': 'analyzed',
            'store': 'yes',
            'type': 'string',
        },

    }
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
    def from_uhm(cls, source, obj, **kwargs):
        _kwargs = {}
        _kwargs['task_id'] = kwargs.get('task_id')

        if isinstance(obj, dict):
            _kwargs.update(obj)
            _obj = cls(source, **_kwargs)
        elif hasattr(obj, 'to_event_row'):
            _obj = cls(source, *obj.to_event_row(), **_kwargs)
        # punt
        elif hasattr(obj, '__iter__'):
            _obj = cls(source, *obj, **_kwargs)
        else:
            print type(obj)
            print dir(obj)
            print obj
            raise Exception()

        return _obj

    def _to_event_row(self):
        return (self.date, self.source, self.url)

    def _to_txt_row(self):
        return ("%s/%s/%s\t%s\t%s\t%s" % (
                self.task_id,
                self.task.queue.type,
                self.task.date,
                self.date,
                self.url.encode('utf8', 'replace'),
                self.title.encode('utf8','replace')
                ))

    def __unicode__(self):
        return (u"Event( %s %s %s )" % (str(self.date), self.source, self.url))

    def __str__(self):
        return unicode(self).encode('utf-8')

class Place(_Base):
    _pyes_schema = {
        'url': {
            'boost': 1.0,
            'index': 'analyzed',
            'store': 'yes',
            'type': u'string',
            'term_vector':'with_positions_offsets'},
        'eventcount': {
            'boost': 1.0,
            'index': 'analyzed',
            'store': 'yes',
            'type': 'integer',
        },
    }

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
        obj = (session.query(cls)
                .filter(cls.url==url)
                .first())
        if obj:
            obj.eventcount += 1
            session.flush()
        else:
            try:
                obj = cls(url, *args, **kwargs)
                session.add(obj)
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
                Column('date', DateTime(), index=True,
                    onupdate=datetime.datetime.now),
        )
        mapper(TaskQueue, queues_tbl)

        tasks_tbl = Table('tasks', meta,
            Column('id', Integer(), primary_key=True, nullable=False),
                Column('queue_id', Integer(),
                    ForeignKey(queues_tbl.c.id), index=True),
                Column('args', MutationDict.as_mutable(JSONEncodedDict)),
                Column('label', UnicodeText()),
                Column('date', DateTime(), index=True,
                    onupdate=datetime.datetime.now,),
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

                Column('place_id', Integer(),
                    ForeignKey(places_tbl.c.id), nullable=True),
                Column('task_id', Integer(),
                    ForeignKey(tasks_tbl.c.id), nullable=False),

                # TODO: sync
                # UniqueConstraint('date','url','task_id',
                #    name='uix_event_date_url_taskid'),
                # breaks w/ webkit history on date !?
                # UniqueConstraint('source','date','url', 'task_id',
                #   name='uix_event_source_task_id'),
        )
        mapper(Event, events_tbl, properties={
            'task': relation(Task, backref='events'),
            'place': relation(Place, backref='events'),
            #'queue': relation(TaskQueue, backref='events'),
        })

    return meta

####

from workhours.models.sql import Base
from workhours.models.sql import DBSession
from workhours.models.sql import initialize_sql
from workhours.security.models import User

from pyramid.security import Everyone
from pyramid.security import Authenticated
from pyramid.security import Allow

#__ALL__ = ("Base", "DBSession", "initialize_sql",
            #"User",
            #"Everyone", "Authenticated", "Allow",
            #"RootFactory",
            #)

class RootFactory(object):
    __acl__ = [
        (Allow, Everyone, 'view'),
        (Allow, Authenticated, 'post')
    ]
    def __init__(self, request):
        pass


