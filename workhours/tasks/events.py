#!/usr/bin/env python
"""
tasks

events
"""
import datetime
import logging
import workhours.models
from workhours.models import TaskQueue, Task, Event, Place
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

def events_table_worker(eventsdb_uri, task_queues, filestore):

    log.debug(task_queues)
    if not check_queue_set(task_queues):
        raise Exception()

    for queuetype, sources in task_queues.iteritems():
        try:
            meta = open_db(eventsdb_uri, setup_mappers, create_tables_on_init=True)
            s = meta.Session()

            s.begin(subtransactions=True)
            queue = TaskQueue( type=queuetype )
            s.add(queue)
            s.commit()
            #s.close()

            parser_parse, get_fileset = QUEUES[queuetype]

            # Consume task iterable
            for argset in sources:
                s = meta.Session()
                s.begin(subtransactions=True)
                task = Task(queue_id=queue._id,
                            args=argset._asdict())
                log.debug("%r : %s " % (task, task._asdict()))
                s.add(task)
                s.commit() # get task._id

                _log = logging.getLogger('workhours.tasks.%s.%s' % (queuetype, task._id))

                task_dirname = '%s_%s' % (task._id, queuetype)
                task_dir = filestore.mkdir(task_dirname)

                # Run Tasks
                try:
                    files_ = [
                        task_dir.copy_here(f)
                            for f in get_fileset(task.args)
                    ]
                    uri = files_[0]
                    for event_ in parser_parse(uri=uri):
                        _log.log(3, "%r : %s" % (event_, event_))
                        try:
                            #_log.debug("%s : %s" % (type(event_), event_))
                            event = Event.from_uhm(
                                        queuetype,
                                        event_,
                                        task_id=task._id)
                            if event.url and '://' in event.url[:10]:
                                place = Place.get_or_create(event.url, session=s)
                                event.place_id = place._id
                            s.add(event)

                            # TODO:
                            #s.flush() # get event._id
                            # sunburnt.index(event + **addl_attrs)
                            # pyes.insert( **event.to_dict() )
                            yield event

                        except Exception, e:
                            task.status = 'err'
                            task.statusmsg = str(e)
                            s.flush()
                            raise

                    s.commit()
                    s.close()
                except Exception, e:
                    log.error("ERROR Parsing: %s" % queuetype)
                    log.error(e)
                    log.exception(e)
                    s.rollback()
                    raise
                    #pass # TOOD
        except Exception, e:
            log.exception(e)
        finally:
            s.close()
