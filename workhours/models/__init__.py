#!/usr/bin/env python
#encoding: utf-8
"""
workhours core models
"""
import datetime
import urlparse
from workhours.models.sqla_utils import MutationDict, JSONEncodedDict
from workhours.models.sql.guid import GUID
import logging
log = logging.getLogger('workhours.models')

__ALL__ = [
    'TaskQueue',
    'Task',
    'Event',
    'Place',
    'setup_mappers'
]


class _Base(object):
    _fields = ('_id',)
    _key_fields = ('_id',)

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

    def get_id(self, _id=None):
        return _id or getattr(self, '_id') or GUID.new_guid() #self.keyfunc()

    def keyfunc(self):
        return (getattr(self, attr) for attr in self.keyfields)

    def _asdict(self, fields=None):
        return {k:getattr(self,k) for k in fields or self._fields}

    def __str__(self):
        return unicode(self).encode('utf-8')


from workhours.models.passphrase import salt_passphrase
from workhours.models.passphrase import hash_passphrase
from workhours.models.passphrase import crypt

class User(_Base):
    """
    Application's user model.
    """
    _fields = (
        '_id',
        'username',
        'name',
        'email',
        'passphrase',
    )
    _key_fields = (
        'username',
    )

    def _get_passphrase(self):
        return self._passphrase

    def _set_passphrase(self, passphrase):
        self._passphrase = hash_passphrase(passphrase)

    passphrase = property(_get_passphrase, _set_passphrase)
    #passphrase = synonym('_passphrase', descriptor=passphrase) # TODO

    def __init__(self,
                    username=None,
                    passphrase=None,
                    _passphrase=None,
                    name=None,
                    email=None,
                    _id=None,
                    ):
        self.username = username
        self.name = name
        self.email = email
        self._id = self.get_id(_id)
        if _passphrase:
            self._passphrase = _passphrase
        elif passphrase:
            self.passphrase = passphrase

    @classmethod
    def get_by_username(cls, username):
        return DBSession.query(cls).filter(cls.username==username).one()

    @classmethod
    def check_passphrase(cls, username, passphrase):
        user = cls.get_by_username(username)
        if not user:
            return False
        return check(user.passphrase,salt_passphrase(passphrase))



class TaskQueue(_Base):
    """
    TODO: really more of a
    """
    _fields = (
        '_id',
        'type',
        'label',
        'uri',
        'host',
        'user',)
    _key_fields = (
        'type',
        'uri',
        'host',
        'user'
    )
    def __init__(self,
                    type=None,
                    label=None,
                    uri=None,
                    host=None,
                    user=None,
                    _id=None,
                    ):
        self.type = type
        self.label = label
        self.uri = uri
        self.host = host
        self.user = user
        self._id = self.get_id(_id)


class Task(_Base):
    _fields = (
        '_id',
        'queue_id',
        'args',
        'date',
        'state',
        'statemsg',
    )
    _key_fields = (
        '_id'
        #'queue_id',
    )
    def __init__(self,
                    queue_id=None,
                    args=None,
                    date=None,
                    state=None,
                    statemsg=None,
                    _id=None,
                    ):

        self.queue_id = queue_id
        self.args = MutationDict()
        log.debug(args)
        if args is not None:
            self.args.update(args)
        self.date = date or datetime.datetime.now()
        self.state = state
        self.statemsg = statemsg
        self._id = self.get_id(_id)

    def __unicode__(self):
        return u', '.join( (str(self._id), str(self.queue_id),
            str(self.date),
                ))


class Event(_Base):
    _pyes_version = 0
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
    _fields = (
        '_id',
        'source',
        'date',
        'url',
        'title',
        'meta',
        'place_id',
        'task_id',
    )
    _key_fields = (
        'task_id',
        'date',
        'url',
    )
    def __init__(self, source=None,
                        date=None,
                        url=None,
                        title=None,
                        meta=None,
                        place_id=None,
                        task_id=None,
                        _id=None,
                        **kwargs
                        ):
        self.source = source
        self.date = date
        self.url = url
        self.title = title
        self.meta = MutationDict()
        if meta:
            self.meta.update(meta)
        if kwargs:
            self.meta.update(kwargs) # TODO
        self.place_id = place_id
        self.task_id = task_id
        self._id = self.get_id(_id)

    @classmethod
    def from_uhm(cls, source, obj, **kwargs):
        _kwargs = {}
        _kwargs['task_id'] = kwargs.get('task_id')

        try:
            if isinstance(obj, dict):
                _kwargs.update(obj)
                _obj = cls(source=source, **_kwargs)
            elif hasattr(obj, 'to_event_row'):
                _obj = cls(source=source, *obj.to_event_row(), **_kwargs)
            # punt
            elif hasattr(obj, '__iter__'):
                _obj = cls(source=source, *obj, **_kwargs)
            else:
                raise
        except Exception, e:
            log.error({'obj': obj,
                        'type': type(obj),
                        'dir': dir(obj)
                        })
            log.exception(e)
            raise

        return _obj

    def _to_event_row(self):
        return (self.date, self.source, self.url)

    def _to_txt_row(self):
        return u"%s\t%s\t%s" % (self.date, self.url, self.title and self.title or '')

    def __verbose(self):
        return ("%s/%s/%s\t%s\t%s\t%s" % (
                self.task_id,
                'other', #self.task.queue.type,
                self.task.date,
                self.date,
                self.url.encode('utf8', 'replace'),
                self.title.encode('utf8','replace')
                ))

    def __unicode__(self):
        return self._to_txt_row()

    def __str__(self):
        return unicode(self).encode('utf-8')

    #@property
    #def type(self):
    #    # FIXME TODO
    #    return self.task.queue.type
    #    return self.source


class Place(_Base):
    _pyes_version = 0
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
            'type': 'integer'},
        'netloc': {
            'boost': 1.0,
            'index': 'analyzed',
            'store': 'yes',
            'type': u'string',
            'term_vector':'with_positions_offsets',
        },
    }
    _fields = (
        '_id',
        'url',
        'eventcount',

        'meta',
        'scheme',
        'port',
        'netloc',
        'path',
        'query',
        'fragment',
    )
    _key_fields = (
        'url',
    )
    def __init__(self,
                    url=None,
                    eventcount=1,
                    meta=None,
                    _id=None,
                    ):
        self.url = url
        self.eventcount = eventcount
        self.meta = MutationDict()
        if meta is not None:
            self.meta.update(meta)
        if self.url is not None:
            self.parse_from(self.url)
        self._id = self.get_id(_id)

    def parse_from(self, url):
        urlp = urlparse.urlparse(url)
        for attr in ('scheme','port','netloc','path','query','fragment'):
            setattr(self, attr, getattr(urlp, attr))
        del urlp

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

    @property
    def title(self):
        # TODO
        return len(self.events) and self.events[-1].title or None


class ReportType(_Base):
    _fields = (
        '_id',
        'label',
        'data',
    )
    _key_fields = (
        'label',
        'data',
    )
    def __init__(self,
                    label=None,
                    _id=None,
                    data=None,
                    ):
        self.label = label
        self.data = MutationDict()
        if data:
            self.data.update(data)
        self._id = self.get_id(_id)


class Report(_Base):
    _fields = (
        '_id',
        'report_type_id',
        'title',
        'data',
    )
    _key_fields = (
        'report_type_id',
        'title',
        'data',
    )
    def __init__(self,
                    report_type_id=None,
                    title=None,
                    data=None,
                    _id=None,
                    ):
        self.report_type_id = report_type_id
        self.title = title
        self.data = MutationDict()
        if data:
            self.data.update(data)
        self._id = self.get_id(_id)


#all_models = [
#    (v) for (k,v) in models.__dict__.items()
#        if hasattr(v,'fields')
#        and not k.startswith('_')]


#from workhours.security.models import User
ALL_MODELS = (
    User,
    TaskQueue,
    Task,
    Place,
    Event,
    ReportType,
    Report,
)

from workhours.models.sql import open_db
from workhours.models.sql import Session
from workhours.models.sql import Base
from workhours.models.sql import DBSession # primary database session
from workhours.models.sql import initialize_sql

from pyramid.security import Everyone
from pyramid.security import Authenticated
from pyramid.security import Allow

from workhours.models.sql.tables import setup_mappers # ... ?

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
        self.request = request
        pass




