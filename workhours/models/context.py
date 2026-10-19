import workhours.models.json as json
from collections.abc import Iterable
import json as stdlib_json
from pyramid.decorator import reify
from pyramid_restler.interfaces import IContext
from sqlalchemy import inspect as sa_inspect
from zope.interface import implementer


def null(*args, **kwargs):
    return {}


# @component.adapter(IRequest)
@implementer(IContext)
class PlainContext:
    """
    "Plain" Context object with stubbed attributes

    :class:`pyramid_restler.interfaces.IContext` interface."""

    json_encoder = json.DefaultJSONEncoder

    def __init__(
        self,
        request,
        get_member=None,
        get_collection=None,
        index_key=None,
        default_fields=None,
    ):
        """
        :param get_member: get_member method
        :param get_collection: get_collection method
        """

        self.request = request
        self._get_member = get_member or null
        self._get_collection = get_collection or null
        self.index_key = index_key
        self.default_fields = default_fields

    # @reify
    # def session(self):
    #    return self.session_factory()

    # def session_factory(self):
    #    return self.request.db_session

    def get_collection(self, *args, **kwargs):
        """
        SELECT *
        SELECT * WHERE {parse(kwargs)}
        """
        # TODO: pagination
        # kwargs.get('page')
        # kwargs.get('per_page')
        # resp {
        #    'entries': self._get_collection(*args, **kwargs),
        #    'currentPage': currentPage,
        #    'perPage': perPage,
        #    'totalEntries': totalEntries,
        # }
        #
        return self._get_collection(*args, **kwargs)

    def get_member(self, key):
        """
        SELECT * WHERE keyattr=key
        """
        # return self.get_member(key)
        # return self.fn(id) #get_number(int(n, 0))
        return self._get_member(key)

    def create_member(self, data):
        raise NotImplementedError()
        # redirect
        # member = self.entity(**data)
        # self.session.add(member)
        # self.session.commit()
        # return member

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
        if isinstance(key, (int, str)):
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
        # obj = self.get_json_obj(value, fields, wrap)
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
        return dict(results=obj, result_count=len(obj),)

    @classmethod
    def member_to_dict(cls, member, fields=None):
        # if fields is None:
        #    fields = self.default_fields
        return member._asdict()
        # dict((name, getattr(member, name)) for name in fields)

    @reify
    @classmethod
    def default_fields(cls):
        return self.fields

        # class_attrs = dir(self.entity)
        # for name in class_attrs:
        # if name.startswith('_'):
        # continue
        # attr = getattr(self.entity, name)
        # if isinstance(attr, property):
        # fields.append(name)
        # else:
        # try:
        # clause_el = attr.__clause_element__()
        # except AttributeError:
        # pass
        # else:
        # if issubclass(clause_el.__class__, Column):
        # fields.append(name)
        # fields = set(fields)
        # return fields


@implementer(IContext)
class SQLAlchemyORMContext:
    json_encoder = json.DefaultJSONEncoder
    entity = None

    def __init__(self, request):
        self.request = request

    @reify
    def session(self):
        return self.session_factory()

    def session_factory(self):
        return self.request.db_session

    def get_collection(
        self, distinct=False, order_by=None, limit=None, offset=None, filters=None
    ):
        query = self.session.query(self.entity)
        for filter_clause in getattr(self, "filters", ()):
            query = query.filter(filter_clause)
        for filter_name, value in (filters or {}).items():
            filter_method = getattr(self.entity, f"{filter_name}_filter", None)
            if filter_method is not None:
                query = query.filter(filter_method(value))
            else:
                query = query.filter_by(**{filter_name: value})
        if distinct:
            query = query.distinct()
        if order_by is not None:
            query = query.order_by(*order_by)
        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)
        return query.all()

    def get_member(self, member_id):
        if member_id is None:
            raise ValueError("member id cannot be None")
        return self.session.get(self.entity, member_id)

    def create_member(self, data):
        member = self.entity(**data)
        self.session.add(member)
        self.session.commit()
        return member

    def update_member(self, member_id, data):
        member = self.get_member(member_id)
        if member is None:
            return None
        for name, value in data.items():
            setattr(member, name, value)
        self.session.commit()
        return member

    def delete_member(self, member_id):
        member = self.get_member(member_id)
        if member is None:
            return None
        self.session.delete(member)
        self.session.commit()
        return member

    def get_member_id(self, member):
        identity = sa_inspect(member).identity
        if identity is None:
            return None
        return identity[0] if len(identity) == 1 else identity

    def get_member_id_as_string(self, member):
        member_id = self.get_member_id(member)
        if isinstance(member_id, str):
            return member_id
        return stdlib_json.dumps(member_id, cls=self.json_encoder)

    def to_json(self, value, fields=None, wrap=True):
        obj = self.get_json_obj(value, fields, wrap)
        return stdlib_json.dumps(obj, cls=self.json_encoder)

    def get_json_obj(self, value, fields=None, wrap=True):
        if fields is None:
            fields = self.default_fields
        if not isinstance(value, Iterable):
            value = [value]
        obj = [self.member_to_dict(member, fields) for member in value]
        if wrap:
            obj = self.wrap_json_obj(obj)
        return obj

    def wrap_json_obj(self, obj):
        return {"results": obj, "result_count": len(obj)}

    def member_to_dict(self, member, fields=None):
        if fields is None:
            fields = self.default_fields
        return {name: getattr(member, name) for name in fields}

    @reify
    def default_fields(self):
        return tuple(sa_inspect(self.entity).column_attrs.keys())


class WorkhoursORMContext(SQLAlchemyORMContext):
    entity = None

    json_encoder = json.DefaultJSONEncoder
    default_fields = ("_id",)
