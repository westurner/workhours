from ..models import json
from collections import Iterable
from pyramid.decorator import reify
from pyramid_restler.interfaces import IContext
from zope.interface import implementer
#from sqlalchemy.schema import Column

def null(*args, **kwargs):
    return {}

#@component.adapter(IRequest)
@implementer(IContext)
class PlainContext(object):
    """
    "Plain" Context object with stubbed attributes

    :class:`pyramid_restler.interfaces.IContext` interface."""

    json_encoder = json.DefaultJSONEncoder

    def __init__(self, request,
            get_member=None,
            get_collection=None,
            index_key=None,
            default_fields=None):
        """
        :param get_member: get_member method
        :param get_collection: get_collection method
        """

        self.request = request
        self._get_member = get_member or null
        self._get_collection = get_collection or null
        self.index_key = index_key
        self.default_fields = default_fields

    #@reify
    #def session(self):
    #    return self.session_factory()

    #def session_factory(self):
    #    return self.request.db_session

    def get_collection(self, *args, **kwargs):
        """
        SELECT *
        SELECT * WHERE {parse(kwargs)}
        """
        # TODO: pagination
        #kwargs.get('page')
        #kwargs.get('per_page')
        #resp {
        #    'entries': self._get_collection(*args, **kwargs),
        #    'currentPage': currentPage,
        #    'perPage': perPage,
        #    'totalEntries': totalEntries,
        #}
        #
        return self._get_collection(*args, **kwargs)

    def get_member(self, key):
        """
        SELECT * WHERE keyattr=key
        """
        #return self.get_member(key)
        #return self.fn(id) #get_number(int(n, 0))
        return self._get_member(key)

    def create_member(self, data):
        raise NotImplementedError()
        # redirect
        #member = self.entity(**data)
        #self.session.add(member)
        #self.session.commit()
        #return member

    def update_member(self, key, data):
        raise NotImplementedError()
    #    q = self.session.query(self.entity)
    #    member = q.get(key)
    #    if member is None:
    #        return None
    #    for name in data:
    #        setattr(member, name, data[name])
    #    self.session.commit()
    #    return member

    def delete_member(self, key):
        raise NotImplementedError()
    #    q = self.session.query(self.entity)
    #    member = q.get(key)
    #    if member is None:
    #        return None
    #    self.session.delete(member)
    #    self.session.commit()
    #    return member

    def get_member_key_as_string(self, member):
        """Return the proper string representation of the member"""
        key = member[self.index_key]
        if isinstance(key, (int, basestring)):
            return key
        else:
            return json.dumps(key, cls=self.json_encoder)

    def to_json(self, value, fields=None, wrap=True):
        """Convert instance or sequence of instances to JSON.

        ``value`` is a single ORM instance or an iterable that yields
        instances.

        ``fields`` is a list of fields to include for each instance.

        ``wrap`` indicates whether or not the result should be wrapped or
        returned as-is.

        """
        #obj = self.get_json_obj(value, fields, wrap)
        return json.dumps(value, cls=self.json_encoder)

    def get_json_obj(self, value, fields, wrap):
        if fields is None:
            fields = self.default_fields
        if not isinstance(value, Iterable):
            value = [value]
        obj = [self.member_to_dict(m, fields) for m in value]
        if wrap:
            obj = self.wrap_json_obj(obj)
        return obj
        return get_json_

    @classmethod
    def wrap_json_obj(cls, obj):
        return dict(
            results=obj,
            result_count=len(obj),
        )

    @classmethod
    def member_to_dict(cls, member, fields=None):
        #if fields is None:
        #    fields = self.default_fields
        return member
        #dict((name, getattr(member, name)) for name in fields)

    @reify
    @classmethod
    def default_fields(cls):
        return self.fields

        #class_attrs = dir(self.entity)
        #for name in class_attrs:
            #if name.startswith('_'):
                #continue
            #attr = getattr(self.entity, name)
            #if isinstance(attr, property):
                #fields.append(name)
            #else:
                #try:
                    #clause_el = attr.__clause_element__()
                #except AttributeError:
                    #pass
                #else:
                    #if issubclass(clause_el.__class__, Column):
                        #fields.append(name)
        #fields = set(fields)
        #return fields

