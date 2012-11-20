
===========
workhours
===========

An event aggregator.

Two components coupled by a database and a data model

1. ETL System
2. Reports webapp

Two .INI-style config files:

1. ``local.ini`` -- read by ``workhours.tasks`` and ``workhours.climain``
2. ``development.ini`` -- read by pserve, gunicorn


ETL System
===========

Command Line Interface
-------------------------
::

   $ workhours --help
   Usage: workhours [-c conf] [--fs path] [--db uri]] <options> [-s source path+] [-r report+]

   event aggregation CLI

   Options:
      -h, --help            show this help message and exit
      -c CONFIG_FILE, --config=CONFIG_FILE
      --db=EVENTSDB_URI, --eventsdb=EVENTSDB_URI
                              Filepath for the aggregate events database
      --fs=FS_URI, --task-storage=FS_URI
                              Path where task and reports files will be stored
      -l, --list-source-types
      -s SRC_QUEUES, --src=SRC_QUEUES
                              Type and filename tuples (ex. 'shell.log ./.usrlog')
      -P, --parse           Parse
      -u USERNAMES, --username=USERNAMES
                              Usernames to include
      --list-report-types   List supported reports
      -r REPORTS, --report=REPORTS
                              Generate a report type
      -o OUTPUT, --output-file=OUTPUT
                              Output file (default: '-' for stdout)
      -O OUTPUT_FORMAT, --output-format=OUTPUT_FORMAT
                              Output format <csv|json> (default: None)
      -G GAPTIME, --gaptime=GAPTIME
                              Minute gap to detect between entries
      -p, --print-all       Dump the events table to stdout
      -v, --verbose         
      -q, --quiet           
      -t, --tes


Extraction
-----------
a one-pass copy and parse of each source listed in ``-c --config-file`` as
::

   [queue_type]
   uniqkey_n = file_uri_n

and on the commandline as ``source path`` to ``-s --src``::

   workhours -s log.shell ~/shell.log

Each source is copied into a filestore at ``fs.uri specified as either

* config: ``fs.uri`` in the config file
* CLI: ``--fs`` on the commandline

and read into a SQL database wrapped by SQLAlchemy specified either by

* Config: ``eventsdb.uri`` in the ``local.ini`` configuration file
* CLI: ``--db <sqlite:///:memory:>``

- TODO: add file:///
- TODO: es indexing


Interfaces
~~~~~~~~~~~~
Parse functions are imported ("registered")
as named queues ``workhours.tasks`` linked to ``parse_`` functions.

Creating an Event record
'''''''''''''''''''''''''
.. code-block:: python

   @classmethod
   def Event.from_uhm(cls, source, obj, **kwargs):
        _kwargs = {}
        _kwargs['task_id'] = kwargs.get('task_id')

        try:
            if isinstance(obj, dict):
                _kwargs.update(obj)
                _obj = cls(source, **_kwargs)
            elif hasattr(obj, 'to_event_row'):
                _obj = cls(source, *obj.to_event_row(), **_kwargs)
            # punt
            elif hasattr(obj, '__iter__'):
                _obj = cls(source, *obj, **_kwargs)
            else:
                raise Exception("uh")
        except Exception, e:
            log.error({'obj': obj,
                        'type': type(obj),
                        'dir': dir(obj)
                        })
            log.exception(e)
            raise Exception()

- TODO: normalize parse function signatures: ``*args``, ``*kwargs``
- TODO: ``workhours.interfaces.IDataSource``
- TODO: Tag Support
- TODO: IDataSource Interface

Tasks
~~~~~~~~~
- TODO: Tests
- TODO: Standard bookmarks.html file
- TODO: HTTP common log
- TOOD: Pyline column mappings

Load
-----
Interfaces
~~~~~~~~~~~~
- ``to_event_row()``: ``tuple``
- TODO: IEventRecord Interface

SQLAlchemy
~~~~~~~~~~~~
* sqlite:///:memory:
* mysql://...
* [...]://...

ElasticSearch
~~~~~~~~~~~~~~~
* TODO: tasks configuration
* TODO: elasticsearch sqlalchemy event integration

PANDAS
~~~~~~~~
* TODO: generate a ``pandas.DataFrame`` from event tables

Models
--------
Standard python classes mapped to 
SQLAlchemy tables.

- ``Event``
- ``Place``
- ``TaskQueue``
- ``Task Models``

Event
~~~~~~~~~
::

   Event .
         .date
         .url
         .text
         .task_id
         

- TODO: sadisplay
- TODO: stdout norm (__{str,unicode}__)



eventually
------------
* TODO: periodic tasks
* TODO: inotify throttling
* TODO: messaging middleware
* TODO: celery || zmq


Reports webapp
===============

Events database
-----------------
* TODO: handle potentially frequently changing events.db files when
* TODO: or, manage two databases and two sets of models (see)

sqlalchemy
~~~~~~~~~~~
TODO: tests: histograms with sqlalchemy date paging

pandas
~~~~~~~
TODO: date aggregation

elasticsearch
~~~~~~~~~~~~~~
* TODO: webapp configuration
* TODO: fulltext search
* TODO: faceted search and highlighting

UI
---
TODO: events HTML tables + paging
TODO: frequency timeline histogram
TODO: REST API
TODO: js layer
