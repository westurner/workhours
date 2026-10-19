#!/usr/bin/env python
# import collections
from sqlalchemy.ext.mutable import Mutable

"""
SQLAlchemy utilities

:See: http://www.sqlalchemy.org/docs/orm/extensions/mutable.html

::

    Column('data', MutationDict.as_mutable(JSONEncodedDict))


::

    MutationDict.associate_with(JSONEncodedDict)


"""


class MutationDict(Mutable, dict):
    @classmethod
    def coerce(cls, key, value):
        "Convert plain dictionaries to MutationDict."

        if not isinstance(value, MutationDict):
            if isinstance(value, dict):
                return MutationDict(value)

            # this call will raise ValueError
            return Mutable.coerce(key, value)
        else:
            return value

    def __setitem__(self, key, value):
        "Detect dictionary set events and emit change events."

        dict.__setitem__(self, key, value)
        self.changed()

    def __delitem__(self, key):
        "Detect dictionary del events and emit change events."

        dict.__delitem__(self, key)
        self.changed()


from sqlalchemy.types import TypeDecorator, VARCHAR

try:
    import simplejson

    json = simplejson
except ImportError as e:
    from . import json


class JSONEncodedDict(TypeDecorator):
    "Represents an immutable structure as a json-encoded string."

    impl = VARCHAR

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


def clear_mappers(mapped_classes):
    """
    Dispose registries for the supplied mapped classes.
    """
    from sqlalchemy import inspect

    registries = set()
    for mapped_class in mapped_classes:
        mapper = inspect(mapped_class, raiseerr=False)
        if mapper is not None:
            registries.add(mapper.registry)

    for mapper_registry in registries:
        mapper_registry.dispose()
