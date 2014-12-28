#!/usr/bin/env python
#encoding: utf-8
"""
event aggregation models
"""

import datetime

#from sqlalchemy import UniqueConstraint
#from sqlalchemy.ext.associationproxy import association_proxy
#from sqlalchemy.orm import sessionmaker, eagerload
from sqlalchemy import ForeignKey
from sqlalchemy import MetaData, DateTime, Table, Column, Integer, Unicode, UnicodeText
from sqlalchemy.orm import mapper, relation, object_session, column_property, synonym, clear_mappers

from workhours.models.sqla_utils import MutationDict, JSONEncodedDict

from workhours.models.sql.guid import GUID

from workhours.models import User
from workhours.models import TaskQueue
from workhours.models import TaskSource
from workhours.models import Task
from workhours.models import Place
from workhours.models import Event
from workhours.models import ReportType
from workhours.models import Report

_MAPPED = False
def setup_mappers(meta=None, engine=None):
    """
    Setup SQLAlchemy mappers for the aggregate events database

    :param meta: SQLAlchemy Metadata
    :type meta: SQLAlchemy Metadata

    :returns: SQLAlchemy meta
    """
    global _MAPPED # TODO
    if _MAPPED:
        #clear_mappers()
        return meta
    _MAPPED = True

    if meta is None:
        meta = MetaData()
    if engine:
        meta.bind = engine

    users_tbl = Table('users', meta,
        Column('id', GUID(), index=True, primary_key=True, ),
            Column('username', Unicode(32), index=True, unique=True),
            Column('name', Unicode(128)),
            Column('email', Unicode(128)),
            Column('passphrase_', Unicode(128)),
    )
    mapper(User, users_tbl, properties={
#        'passphrase': synonym("passphrase_")
    })

    queues_tbl = Table('queues', meta,
        Column('id', GUID(), primary_key=True, nullable=False),
            Column('type', Unicode(length=255), index=True, unique=True),
            Column('uri', UnicodeText()),
            Column('label', UnicodeText()),
            Column('date', DateTime(), index=True,
                onupdate=datetime.datetime.now),

            Column('host', UnicodeText()), # default=$(hostname)
            Column('user', UnicodeText())  # default=$(whoami)
    )
    mapper(TaskQueue, queues_tbl)


    tasksources_tbl = Table('tasksources', meta,
        Column('id', GUID(), primary_key=True, nullable=False),
            Column('queue_id', GUID(), ForeignKey(queues_tbl.c.id), index=True),
            Column('type', Unicode(length=255), index=True), # taskqueue.type # TODO
            Column('url', UnicodeText()),
            Column('label', UnicodeText()),
            Column('date', DateTime(), index=True,
                onupdate=datetime.datetime.now),

            Column('host', UnicodeText()), # default=$(hostname)
            Column('user', UnicodeText())  # default=$(whoami)
    )
    mapper(TaskSource, tasksources_tbl, properties={
        'queue': relation(TaskQueue, backref='sources')
        })

    tasks_tbl = Table('tasks', meta,
        Column('id', GUID(), primary_key=True, nullable=False),
            Column('source_id', GUID(),
                ForeignKey(tasksources_tbl.c.id), index=True),
            Column('args', MutationDict.as_mutable(JSONEncodedDict)),
            Column('label', UnicodeText()),
            Column('state', Unicode(), index=True, nullable=True), # TODO: ENUM: celery
            Column('statemsg', Unicode()),
            Column('date', DateTime(), index=True,
                onupdate=datetime.datetime.now,),
    )
    mapper(Task, tasks_tbl, properties={
        'source': relation(TaskSource, backref='tasks'),
    })

    places_tbl = Table('places', meta,
        Column('id', GUID(), primary_key=True, nullable=False),
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
        Column('id', GUID(), primary_key=True), # TODO, nullable=False),
            Column('source', Unicode(), index=True),
            Column('date', DateTime(), index=True),
            Column('url', UnicodeText()),
            Column('title', UnicodeText()),
            Column('meta', MutationDict.as_mutable(JSONEncodedDict)),

            Column('host', UnicodeText()),
            Column('user', UnicodeText()),

            Column('place_id', GUID(),
                ForeignKey(places_tbl.c.id), nullable=True),
            Column('source_id', GUID(),
                ForeignKey(tasksources_tbl.c.id), nullable=False),
            Column('task_id', GUID(),
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

    report_types_tbl = Table('report_types', meta,
        Column('id', GUID(), primary_key=True, nullable=False),
            Column('label', Unicode(), index=True),
            Column('data', MutationDict.as_mutable(JSONEncodedDict))
    )

    mapper(ReportType, report_types_tbl)

    reports_tbl = Table('reports', meta,
        Column('id', GUID(), primary_key=True, nullable=False),
            Column('report_type_id', GUID(),
                ForeignKey(report_types_tbl.c.id), nullable=False),
            Column('title', Unicode(), nullable=True),
            Column('data', MutationDict.as_mutable(JSONEncodedDict)))

    mapper(Report, reports_tbl, properties={
        'report_type': relation(ReportType, backref='reports'),
    })

    return meta

####

