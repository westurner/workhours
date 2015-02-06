#!/usr/bin/env python
"""
tasks

events
"""
import datetime
import logging
import transaction
import workhours.models
from workhours.models import TaskQueue, TaskSource, Task, Event, Place
from workhours.models import open_db
from workhours.models.sql.tables import setup_mappers
from workhours.future import OrderedDict
import workhours.models.json as json

from workhours.firefox.history import parse_firefox_history
from workhours.firefox.history import parse_firefox_bookmarks
from workhours.webkit.bookmarks import parse_webkit_bookmarks
from workhours.webkit.history import parse_webkit_history
from workhours.delicious.bookmarks import parse_delicious_bookmarks
from workhours.trac.timeline import parse_trac_timeline
from workhours.syslog.sessionlog import parse_sessionlog
from workhours.syslog.wtmp import parse_wtmp_glob
from workhours.syslog.authlog import parse_authlog_glob
from workhours.syslog.find import parse_find_printf
from workhours.bookmarks.json import parse_bookmarks_json
from workhours.bookmarks.html import parse_bookmarks_html


log = logging.getLogger('workhours.tasks')

DEFAULT_FILES = lambda x: ( x['url'], )
SQLITE_FILES =  lambda x: ( x['url'],
                            '%s-journal' % x['url'])

# TODO: registry
QUEUES=OrderedDict( (
    ( "firefox.bookmarks", (parse_firefox_bookmarks, SQLITE_FILES, ) ),
    ( "firefox.history", (parse_firefox_history, SQLITE_FILES, ), ),
    ( "webkit.bookmarks", (parse_webkit_bookmarks, DEFAULT_FILES, ), ),
    ( 'webkit.history', (parse_webkit_history, SQLITE_FILES, ), ),
    ( "delicious.bookmarks", (parse_delicious_bookmarks, DEFAULT_FILES, ), ),
    ( "trac.timelines", (parse_trac_timeline, DEFAULT_FILES, ), ),
    ( "log.shell", (parse_sessionlog, DEFAULT_FILES, ), ),
    ( "find", (parse_find_printf, DEFAULT_FILES, ), ),
    ( "log.wtmp", (parse_wtmp_glob, DEFAULT_FILES, ), ),
    ( "log.auth", (parse_authlog_glob, DEFAULT_FILES, ), ),
    ( "bookmarks.json", (parse_bookmarks_json, DEFAULT_FILES, ), ),
    ( "bookmarks.html", (parse_bookmarks_html, DEFAULT_FILES, ), ),
) )

import os
def check_queue_set(task_queues):
    errflag = False
    for queuetype, tasks in task_queues.iteritems():
        for argset in tasks:
            if not os.path.exists(argset.url) and os.path.isfile(argset.url):
                errflag = True
                print("Queued source not found: %r %r"
                        % (queuetype, argset.url))
    return not errflag



from pprint import pformat

def update_task_queues(eventsdb_uri, task_queues, filestore):
    log.debug(pformat(dict(task_queues)))
    log.debug("UPDATING TASK QUEUES")
    if not check_queue_set(task_queues):
        raise Exception()

    for queue_type, sources in task_queues.iteritems():
        #import ipdb
        #ipdb.set_trace()
        try:
            meta = open_db(eventsdb_uri, setup_mappers, create_tables_on_init=False)
            s = meta.Session()

            queue = TaskQueue.get_or_create(
                        TaskQueue.type, queue_type,
                        id=TaskQueue._new_id(),
                        type=queue_type,
                        #uri=sources[0].url, # TODO)
                        host='localhost', # TODO
                        user='username', # TODO
            )
            s.add(queue)

            for source in sources:
                source = TaskSource(
                        id=TaskSource._new_id(),
                        queue_id=queue.id,
                        **source._asdict()
                )
                s.add(source)

            s.commit()
            transaction.commit()
        except Exception, e:
            log.exception(e)
            transaction.abort()
        finally:
            s.close()

from workhours.models.files import TempDir # TODO
def parse_event_source(eventsdb_uri, queue_id, filestore_uri=None):
    """
    Create and execute a Task for each TaskSource

    """
    log.debug("parse_event_source: (%r, %r)" % (eventsdb_uri, queue_id))

    filestore = TempDir(filestore_uri or os.environ.get('$_TMP')) # TODO
    meta = open_db(eventsdb_uri, setup_mappers, create_tables_on_init=True)
    s = meta.Session()
    s.expire_on_commit = False

    # lookup queue
    queue = s.query(TaskQueue).filter(TaskQueue.id==queue_id).one()
    queue_type = queue.type

    parser_parse, get_fileset = QUEUES[queue.type]

# a Task, really, is a combination of
# * _id: a globally unique ID
# * queue_id: TaskQueue with a queue.type that maps to a parsing function
# * args: arguments

    for source in queue.sources: #sources:

        s = meta.Session()
        task = Task(
                    id=Task._new_id(),
                    source_id=source.id,
                    #args=argset._asdict(),
                    args=source._asdict()
                    )
        log.info("TASK: %r : %s " % (task, task._asdict()))
        s.add(task)
        transaction.commit()

        _log = logging.getLogger('workhours.tasks.%s.%s' % (queue.type, task.id))

        #transaction.commit() # get task.id
        task_dirname = '%s_%s' % (task.id, queue.type)

        task_dir = filestore.mkdir(task_dirname)

        # Run Tasks
        try:
            #meta = open_db(eventsdb_uri, setup_mappers, create_tables_on_init=True)

            #s = meta.Session()
            files_ = [
                task_dir.copy_here(f)
                    for f in get_fileset(task.args)
            ]
            uri = files_[0]

            for parser_event in parser_parse(uri=uri):
                _log.log(3, "%r : %s" % (parser_event, parser_event))
                try:
                    event = Event.from_uhm(
                        parser_event,
                        id=Event._new_id(),
                        task_id=task.id,
                        #source=queue_type,
                        source=source.type,
                        #source=task.args['type'],
                        source_id=source.id
                    )
                    if event.url and '://' in event.url[:10]:
                        place = Place.get_or_create(event.url, session=s)
                        event.place_id = place.id
                    s.add(event)
                    #transaction.commit()

                    # TODO:
                    #s.flush() # get event.id
                    # sunburnt.index(event + **addl_attrs)
                    # pyes.insert( **event.to_dict() )
                    yield event

                except Exception, e:
                    task.status = 'err'
                    task.statusmsg = str(e)
                    s.flush()
                    raise

            s.commit()
            transaction.commit()
        except Exception, e:
            #log.error("ERROR Parsing: %s" % queue)
            #log.error(e)
            log.exception(e)
            #s.rollback()
            #transaction.abort()
            raise
            pass # TOOD
        finally:
            s.close()
            pass

def events_table_worker(eventsdb_uri, task_queues, filestore):
    log.debug("events_table_worker")

    meta = open_db(eventsdb_uri, setup_mappers, create_tables_on_init=True)

    update_task_queues(eventsdb_uri, task_queues, filestore)

    s = meta.Session()
    task_queues = s.query(TaskQueue).all() # TODO
    #event_sources = s.query(TaskSource).all()
    for queue in task_queues:
        try:
            log.info('parsing event source: %r ' % (queue.type))
            for event in parse_event_source(eventsdb_uri, queue.id, filestore_uri=filestore):
                yield event
        except Exception, e:
            raise
            pass # TODO
