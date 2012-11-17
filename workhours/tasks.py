#!/usr/bin/env python
"""
tasks

events
"""
import datetime
import logging

from itertools import ifilter


log = logging.getLogger('workhours.tasks')

from workhours.models import open_db
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



def setup_database(eventsdb_uri):
    engine = create_engine(eventsdb_uri)
    meta = setup_mappers(engine)
    meta.bind = engine

    # Create tables
    meta.create_all()
    meta.Session = sessionmaker(bind=engine)
    return (engine, meta)

# TODO: more elegant generalization
def populate_events_table(eventsdb_uri, task_queues, fs):
    #(engine, meta) = setup_database(eventsdb_uri)
    #s = meta.Session()
    s = open_db(eventsdb_uri)
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



