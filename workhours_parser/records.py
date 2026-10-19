"""Immutable, validated records shared by source parsers and exporters."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from importlib.resources import files
import json
import re
from types import MappingProxyType

from jsonschema import Draft202012Validator


class SourceRecordError(ValueError):
    """Raised when a canonical source record violates its contract."""


_DURATION_PATTERN = re.compile(
    r"^P(?:(?P<weeks>\d+(?:\.\d+)?)W|"
    r"(?:(?P<days>\d+(?:\.\d+)?)D)?"
    r"(?:T(?:(?P<hours>\d+(?:\.\d+)?)H)?"
    r"(?:(?P<minutes>\d+(?:\.\d+)?)M)?"
    r"(?:(?P<seconds>\d+(?:\.\d+)?)S)?)?)$"
)

_SCHEMA_PATH = files(__package__).joinpath("schemas", "source-record-v1.json")
with _SCHEMA_PATH.open("r", encoding="utf-8") as _schema_file:
    SOURCE_RECORD_SCHEMA = json.load(_schema_file)

Draft202012Validator.check_schema(SOURCE_RECORD_SCHEMA)
_RECORD_VALIDATOR = Draft202012Validator(SOURCE_RECORD_SCHEMA)


def _as_datetime(value, field):
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as error:
            raise SourceRecordError(
                "{} must be an ISO 8601 datetime".format(field)
            ) from error
    raise SourceRecordError("{} must be a datetime or ISO 8601 string".format(field))


def _duration_delta(value):
    if not isinstance(value, str):
        raise SourceRecordError("duration must be an ISO 8601 duration string")
    match = _DURATION_PATTERN.fullmatch(value)
    if match is None or not any(match.groupdict().values()):
        raise SourceRecordError(
            "duration must use the fixed-unit ISO 8601 duration form"
        )

    parts = match.groupdict()
    if "T" in value and not any(
        parts[unit] is not None for unit in ("hours", "minutes", "seconds")
    ):
        raise SourceRecordError("duration time component cannot be empty")
    if parts["weeks"] is not None:
        seconds = Decimal(parts["weeks"]) * 7 * 24 * 60 * 60
    else:
        seconds = sum(
            Decimal(parts[unit] or "0") * factor
            for unit, factor in (
                ("days", 24 * 60 * 60),
                ("hours", 60 * 60),
                ("minutes", 60),
                ("seconds", 1),
            )
        )
    if seconds < 0:
        raise SourceRecordError("duration cannot be negative")
    return timedelta(microseconds=int(seconds * 1_000_000))


def _freeze(value):
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    return value


def _thaw(value):
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value


@dataclass(frozen=True, slots=True)
class SourceRecord:
    """A source event with validated, sink-independent fields."""

    startDate: datetime
    source_key: str
    endDate: datetime | None = None
    duration: str | None = None
    url: str | None = None
    name: str | None = None
    meta: Mapping = None

    def __post_init__(self):
        try:
            start_date = _as_datetime(self.startDate, "startDate")
            end_date = (
                None
                if self.endDate is None
                else _as_datetime(self.endDate, "endDate")
            )
            metadata = {} if self.meta is None else dict(self.meta)
        except (TypeError, ValueError) as error:
            if isinstance(error, SourceRecordError):
                raise
            raise SourceRecordError("meta must be a mapping") from error

        if not isinstance(self.source_key, str) or not self.source_key:
            raise SourceRecordError("source_key must be a non-empty string")
        if self.url is not None and not isinstance(self.url, str):
            raise SourceRecordError("url must be a string or None")
        if self.name is not None and not isinstance(self.name, str):
            raise SourceRecordError("name must be a string or None")

        if end_date is not None:
            try:
                if end_date < start_date:
                    raise SourceRecordError("endDate must not precede startDate")
            except TypeError as error:
                raise SourceRecordError(
                    "startDate and endDate must use compatible timezone awareness"
                ) from error

        if self.duration is not None:
            delta = _duration_delta(self.duration)
            if end_date is not None:
                try:
                    actual_delta = end_date - start_date
                except TypeError as error:
                    raise SourceRecordError(
                        "startDate and endDate must use compatible timezone awareness"
                    ) from error
                if actual_delta != delta:
                    raise SourceRecordError(
                        "duration must agree with endDate minus startDate"
                    )

        object.__setattr__(self, "startDate", start_date)
        object.__setattr__(self, "endDate", end_date)
        object.__setattr__(self, "meta", metadata)
        errors = sorted(
            _RECORD_VALIDATOR.iter_errors(self.to_dict()),
            key=lambda error: list(error.path),
        )
        if errors:
            raise SourceRecordError(errors[0].message)
        object.__setattr__(self, "meta", _freeze(metadata))

    def to_dict(self):
        """Return a JSON-compatible canonical representation."""
        return {
            "startDate": self.startDate.isoformat(),
            "endDate": self.endDate.isoformat() if self.endDate else None,
            "duration": self.duration,
            "url": self.url,
            "name": self.name,
            "meta": _thaw(self.meta),
            "source_key": self.source_key,
        }

    @classmethod
    def from_dict(cls, values):
        """Create a record from its canonical JSON-compatible mapping."""
        return cls(**values)