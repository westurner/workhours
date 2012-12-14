from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import TypeDecorator, CHAR
import uuid

import logging
log = logging.getLogger('workhours.models.sql.guid')

NAMESPACE = 'workhours' # TODO

class GUID(TypeDecorator):
    """Platform-independent GUID type.

    Uses Postgresql's UUID type, otherwise uses
    CHAR(32), storing as stringified hex values.

    """
    impl = CHAR

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        #if value is None:
        #    return value
        if dialect.name == 'postgresql':
            return str(value)
        else:

            if value is None:
                return GUID.new_guid(value)
            elif not isinstance(value, uuid.UUID):
                return value
            else:
                # hexstring
                return GUID.to_str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            return GUID.to_str(value)

    @classmethod
    def new_guid(cls, value=None):
        if value is None:
            guid = uuid.uuid4()
        else:
            guid = uuid.uuid5(NAMESPACE, value)
        log.log(3,'guid: %r' % guid)
        return GUID.to_str(guid) #uuid.UUID(guid)

    @classmethod
    def to_str(cls, value):
        return str(value) #"%.32x" % value
