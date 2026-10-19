"""SQLAlchemy types for portable canonical event timestamps."""

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.types import TypeDecorator


class ISODateTime(TypeDecorator):
    """Use ISO strings on SQLite, which otherwise discards timezone offsets."""

    impl = DateTime
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "sqlite":
            return dialect.type_descriptor(String(40))
        return dialect.type_descriptor(DateTime(timezone=True))

    def process_bind_param(self, value, dialect):
        if value is None or dialect.name != "sqlite":
            return value
        if not isinstance(value, datetime):
            raise TypeError("event timestamps must be datetime values")
        return value.isoformat(timespec="microseconds")

    def process_result_value(self, value, dialect):
        if value is None or not isinstance(value, str):
            return value
        return datetime.fromisoformat(value.replace("Z", "+00:00"))