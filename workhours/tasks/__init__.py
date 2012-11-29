#!/usr/bin/env python
"""
tasks

events
"""
import datetime
import logging

from itertools import ifilter


log = logging.getLogger('workhours.tasks')

import workhours.models
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
from workhours.syslog.find import parse_find_printf

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
) )


import workhours.models as models
from workhours.models.sqla_utils import MutationDict
import json

import os
def check_queue_set(task_queues):
    errflag = False
    for queue_k, tasks in task_queues.iteritems():
        for argset in tasks:
            if not os.path.exists(argset.url) and os.path.isfile(argset.url):
                errflag = True
                print("Queued source not found: %r %r"
                        % (queue_k, argset.url))
    return not errflag

# TODO: more elegant generalization
def populate_events_table(eventsdb_uri, task_queues, fs):
    if not check_queue_set(task_queues):
        raise Exception()

    meta = models.open_db(eventsdb_uri, models.setup_mappers)
    s = meta.Session()
    for queue_k, tasks in task_queues.iteritems():
        s.begin(subtransactions=True)
        queue = TaskQueue( queue_k )
        s.add(queue)
        s.commit()

        parsefunc_iter, files = QUEUES[queue_k]

        for argset in tasks:
            log.debug("Task: %s" % str(argset))
            # TODO
            s.begin(subtransactions=True)
            task = Task( queue.id, argset._asdict())
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
                    log.debug(event_)
                    try:
                        #_log.debug("%s : %s" % (type(event_), event_))
                        event = Event.from_uhm(queue_k, event_, task_id=task.id)
                        if event.url:
                            place = Place.get_or_create(event.url, session=s)
                            event.place_id = place.id
                        s.add(event)

                        # TODO:
                        s.flush() # get event.id
                        # sunburnt.index(event + **addl_attrs)
                        # pyes.insert( **event.to_dict() )
                        yield event

                    except Exception, e:
                        task.status = 'err'
                        task.statusmsg = str(e)
                        s.flush()
                        raise

                s.commit()
            except Exception, e:
                log.error(e)
                log.exception(e)
                #s.rollback() # TODO
                raise
                #pass # TOOD
        s.commit()
    s.commit()
