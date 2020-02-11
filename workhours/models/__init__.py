#!/usr/bin/env python
# encoding: utf-8
"""
workhours core models
"""
import datetime
import urllib.parse
from workhours.models.sqla_utils import MutationDict, JSONEncodedDict
from workhours.models.sql.guid import GUID
from sqlalchemy.orm import object_session
from sqlalchemy.ext.hybrid import hybrid_property
import sqlalchemy.orm.exc
import logging

log = logging.getLogger("workhours.models")

__ALL__ = [
    "User",
    "TaskQueue",
    "TaskSource",
    "Task",
    "Event",
    "Place",
    "ReportType",
    "Report",
    "setup_mappers",
]


class _Base(object):
    _fields = ("id",)
    _key_fields = ("id",)

    def getattrs(self, *attrs):
        if attrs:
            return (getattr(self, attr) for attr in attrs)
        return (getattr(self, attr) for attr in self.columns)

    @classmethod
    def select_columns(cls, attrs, order_by="date", session=None):
        s = session or object_session(cls)
        return s.query(*(getattr(cls, attr) for attr in attrs)).order_by(
            getattr(cls, order_by)
        )

    @classmethod
    def _new_id(cls):
        return GUID.new_guid()

    def keyfunc(self):
        return (getattr(self, attr) for attr in self.keyfields)

    def _asdict(self, fields=None):
        return {k: getattr(self, k) for k in (fields or self._fields)}

    # def __str__(self):
    #    return unicode(self).encode('utf-8')
    #
    #    def __unicode__(self):
    #        return unicode(self._asdict())

    @classmethod
    def get_or_create(cls, attr, value, **kwargs):
        try:
            obj = DBSession.query(cls).filter(attr == value).one()
            return obj
        except sqlalchemy.orm.exc.NoResultFound as e:
            kwargs[attr.property.key] = value  #
            obj = cls(**kwargs)
            return obj
        except sqlalchemy.orm.exc.MultipleResultsFound as e:
            raise


class User(_Base):
    """
    Application's user model.
    """

    _fields = (
        "id",
        "username",
        "first_name",
        "last_name",
        "email",
        "password_",
    )
    _key_fields = ("username",)

    def __init__(
        self,
        username=None,
        password=None,
        first_name=None,
        last_name=None,
        email=None,
        id=None,
    ):
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.id = id  # self.get_id(_id)
        self.password = password

    @classmethod
    def get_by_username(cls, username):
        return DBSession.query(cls).filter(cls.username == username).one()

    @classmethod
    def check_login(cls, username, password):
        try:
            user = cls.get_by_username(username)
            return user and user._check_password(password)
        except Exception as e:
            return False


class Command(_Base):
    _fields = (
        "id",
        "expire_on",
        "command_id",
        "command_type",
        "command_date",
        "identity",
    )
    pass


class TaskQueue(_Base):
    """
    TODO: really more of a
    """

    _fields = (
        "id",
        "type",
        "label",
        "uri",
        "host",
        "user",
    )

    _key_fields = ("type", "uri", "host", "user")

    def __init__(
        self, type=None, label=None, uri=None, host=None, user=None, id=None,
    ):
        self.type = type
        self.label = label
        self.uri = uri
        self.host = host
        self.user = user
        self.id = id


class TaskSource(_Base):
    """
    TODO: really more of a
    """

    _fields = (
        "id",
        "type",
        "label",
        "url",
        "host",
        "user",
        "queue_id",
    )
    _key_fields = ("type", "uri", "host", "user")

    def __init__(
        self,
        queue_id=None,
        type=None,
        label=None,
        url=None,
        host=None,
        user=None,
        id=None,
    ):
        self.queue_id = queue_id
        self.type = type  # queue.type
        self.label = label
        self.url = url
        self.host = host
        self.user = user
        self.id = id


class Task(_Base):
    _fields = (
        "id",
        "source_id",
        "args",
        "date",
        "state",
        "statemsg",
    )
    _key_fields = (
        "id"
        #'queue_id',
    )

    def __init__(
        self,
        source_id=None,
        args=None,
        date=None,
        state=None,
        statemsg=None,
        id=None,
    ):

        self.source_id = source_id
        self.args = MutationDict()
        log.debug(args)
        if args is not None:
            self.args.update(args)
        self.date = date or datetime.datetime.now()
        self.state = state
        self.statemsg = statemsg
        self.id = id

    def __unicode__(self):
        return ", ".join((str(self.id), str(self.queue_id), str(self.date),))


class Event(_Base):
    _pyes_version = 0
    _pyes_schema = {
        "id": {
            "boost": 1.0,
            "index": "analyzed",
            "store": "yes",
            "type": "string",
        },
        "source": {
            "boost": 1.0,
            "index": "analyzed",
            "store": "yes",
            "type": "string",
            "term_vector": "with_positions_offsets",
        },
        "date": {
            "boost": 1.0,
            "index": "analyzed",
            "store": "yes",
            "type": "date",
        },
        "url": {
            "boost": 1.0,
            "index": "analyzed",
            "store": "yes",
            "type": "string",
        },
        "title": {
            "boost": 1.0,
            "index": "analyzed",
            "store": "yes",
            "type": "string",
        },
        "meta": {
            "boost": 1.0,
            "index": "analyzed",
            "store": "yes",
            "type": "string",
        },
        "place_id": {
            "boost": 1.0,
            "index": "analyzed",
            "store": "yes",
            "type": "string",
        },
        "source_id": {
            "boost": 1.0,
            "index": "analyzed",
            "store": "yes",
            "type": "string",
        },
        "task_id": {
            "boost": 1.0,
            "index": "analyzed",
            "store": "yes",
            "type": "string",
        },
    }
    _fields = (
        "id",
        "date",
        "url",
        "title",
        "meta",
        "place_id",
        "source",
        "source_id",
        "task_id",
    )
    _key_fields = (
        "date",
        "task_id",
        #'url',
    )

    def __init__(
        self,
        date=None,
        url=None,
        title=None,
        meta=None,
        place_id=None,
        source=None,
        source_id=None,
        task_id=None,
        id=None,
        **kwargs
    ):
        """
        Create a new event with a new _id attribute
        """
        self.id = id
        log.debug("new event: (%r, %r, %r, %r)" % (self.id, source, date, url))
        self.source = source
        self.date = date
        self.url = url
        self.title = title
        self.meta = MutationDict()
        if meta:
            self.meta.update(meta)
        if kwargs:
            self.meta.update(kwargs)  # TODO
        self.place_id = place_id
        self.source_id = source_id
        self.task_id = task_id

    @classmethod
    def from_uhm(cls, obj, **kwargs):
        # TODO
        _kwargs = {}
        _kwargs["task_id"] = kwargs.get("task_id")
        _kwargs["id"] = cls._new_id()
        _kwargs["source"] = kwargs.get("source")
        _kwargs["source_id"] = kwargs["source_id"]

        try:
            if isinstance(obj, dict):
                _kwargs.update(obj)
                _obj = cls(**_kwargs)
            elif hasattr(obj, "to_event_row"):
                _obj = cls(*obj.to_event_row()[:3], **_kwargs)  # TODO
            # punt
            elif hasattr(obj, "__iter__"):
                _obj = cls(*obj[:3], **_kwargs)  # TODO
            else:
                raise
        except Exception as e:
            log.error({"obj": obj, "type": type(obj), "dir": dir(obj)})
            log.exception(e)
            raise

        return _obj

    def _to_event_row(self):
        return (self.date, self.source, self.url)

    def _to_txt_row(self):
        return "%s\t%s\t%s" % (
            self.date,
            self.url,
            self.title and self.title or "",
        )

    def __verbose(self):
        return "%s/%s/%s\t%s\t%s\t%s" % (
            self.task_id,
            "other",  # self.task.queue.type,
            self.task.date,
            self.date,
            self.url.encode("utf8", "replace"),
            self.title.encode("utf8", "replace"),
        )

    def __unicode__(self):
        return self._to_txt_row()

    def __str__(self):
        return str(self).encode("utf-8")

    # @property
    # def type(self):
    #    # FIXME TODO
    #    return self.task.queue.type
    #    return self.source


class Place(_Base):
    _pyes_version = 0
    _pyes_schema = {
        "id": {
            "boost": 1.0,
            "index": "analyzed",
            "store": "yes",
            "type": "string",
        },
        "url": {
            "boost": 1.0,
            "index": "analyzed",
            "store": "yes",
            "type": "string",
            "term_vector": "with_positions_offsets",
        },
        "eventcount": {
            "boost": 1.0,
            "index": "analyzed",
            "store": "yes",
            "type": "integer",
        },
        "netloc": {
            "boost": 1.0,
            "index": "analyzed",
            "store": "yes",
            "type": "string",
            "term_vector": "with_positions_offsets",
        },
    }
    _fields = (
        "id",
        "url",
        "eventcount",
        "meta",
        "scheme",
        "port",
        "netloc",
        "path",
        "query",
        "fragment",
    )
    _key_fields = ("url",)

    def __init__(
        self, url=None, eventcount=1, meta=None, id=None,
    ):
        self.url = url
        self.eventcount = eventcount
        self.meta = MutationDict()
        if meta is not None:
            self.meta.update(meta)
        if self.url is not None:
            self.parse_from(self.url)
        self.id = id

    def parse_from(self, url):
        urlp = urllib.parse.urlparse(url)
        for attr in ("scheme", "port", "netloc", "path", "query", "fragment"):
            setattr(self, attr, getattr(urlp, attr))
        del urlp

    @classmethod
    def get_or_create(cls, url, session=None, *args, **kwargs):
        obj = session.query(cls).filter(cls.url == url).first()
        if obj:
            obj.eventcount += 1
            session.flush()
        else:
            try:
                obj = cls(url, *args, id=cls._new_id(), **kwargs)
                session.add(obj)
            except Exception:
                raise
        return obj

    @property
    def title(self):
        # TODO
        return len(self.events) and self.events[-1].title or None


class ReportType(_Base):
    _fields = (
        "id",
        "label",
        "data",
    )
    _key_fields = (
        "label",
        "data",
    )

    def __init__(
        self, label=None, id=None, data=None,
    ):
        self.label = label
        self.data = MutationDict()
        if data:
            self.data.update(data)
        self.id = id


class Report(_Base):
    _fields = (
        "id",
        "report_type_id",
        "title",
        "data",
    )
    _key_fields = (
        "report_type_id",
        "title",
        "data",
    )

    def __init__(
        self, report_type_id=None, title=None, data=None, id=None,
    ):
        self.report_type_id = report_type_id
        self.title = title
        self.data = MutationDict()
        if data:
            self.data.update(data)
        self.id = id


# all_models = [
#    (v) for (k,v) in models.__dict__.items()
#        if hasattr(v,'fields')
#        and not k.startswith('_')]


# from workhours.security.models import User
ALL_MODELS = (
    User,
    TaskQueue,
    TaskSource,
    Task,
    Place,
    Event,
    ReportType,
    Report,
)

from workhours.models.sql import open_db
from workhours.models.sql import Session
from workhours.models.sql import Base
from workhours.models.sql import DBSession  # primary database session
from workhours.models.sql import initialize_sql

from pyramid.security import Everyone
from pyramid.security import Authenticated
from pyramid.security import Allow

from workhours.models.sql.tables import setup_mappers  # ... ?

# __ALL__ = ("Base", "DBSession", "initialize_sql",
# "User",
# "Everyone", "Authenticated", "Allow",
# "RootFactory",
# )


class RootFactory(object):
    __acl__ = [(Allow, Everyone, "view"), (Allow, Authenticated, "post")]

    def __init__(self, request):
        self.request = request
        pass
