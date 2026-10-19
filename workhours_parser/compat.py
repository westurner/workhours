"""Compatibility conversion for existing workhours parser outputs."""

from collections.abc import Mapping
from hashlib import sha256
import os

from .records import SourceRecord


_META_FIELDS = {
    "webkit.bookmarks": ("path",),
    "delicious.bookmarks": ("tags", "private", "comment"),
    "find": ("size", "user", "type"),
    "log.shell": ("session",),
    "log.auth": ("hostname", "process"),
    "bookmarks.json": ("path", "tags", "private", "comment"),
    "bookmarks.html": ("path", "tags", "private", "comment"),
}


def _decode(value):
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _legacy_values(source_type, record):
    if isinstance(record, SourceRecord):
        return record

    if isinstance(record, Mapping):
        return dict(record)

    if hasattr(record, "_asdict"):
        return dict(record._asdict())
    if hasattr(record, "to_event_row"):
        values = record.to_event_row()
    elif hasattr(record, "_to_event_row"):
        values = record._to_event_row()
    elif hasattr(record, "date"):
        values = (
            record.date,
            getattr(record, "url", None),
            getattr(record, "title", None),
        )
    elif isinstance(record, (tuple, list)):
        values = record
    else:
        raise TypeError(
            "unsupported legacy parser record: {}".format(type(record).__name__)
        )

    if source_type == "find" and len(values) == 5:
        return dict(zip(("date", "size", "user", "type", "url"), values))
    if source_type == "log.shell":
        return {
            "date": values[0],
            "name": values[1] if len(values) > 1 else None,
            "session": values[2] if len(values) > 2 else None,
        }
    if source_type in ("log.wtmp", "log.auth"):
        return {
            "date": values[0],
            "name": values[1] if len(values) > 1 else None,
        }
    return {
        "date": values[0],
        "url": values[1] if len(values) > 1 else None,
        "title": values[2] if len(values) > 2 else None,
    }


def normalize_record(source_type, record, source_identity, position):
    """Convert one existing parser row to a validated canonical record.

    When a parser exposes an underlying row ID, it is used as the key suffix.
    Otherwise the stable input identity and zero-based parser position are used.
    """
    values = _legacy_values(source_type, record)
    if isinstance(values, SourceRecord):
        return values
    start_date = values.get("startDate", values.get("date"))
    name = values.get("name", values.get("title"))
    url = values.get("url")
    if source_type == "find" and name is None:
        name = url

    source_record_id = values.get("source_record_id", values.get("id"))
    if source_record_id is None and not isinstance(record, Mapping):
        source_record_id = getattr(record, "id", None)

    metadata = dict(values.get("meta") or {})
    metadata.update({"source": source_type, "record_position": position})
    if source_record_id is not None:
        metadata["source_record_id"] = _decode(source_record_id)

    for field in _META_FIELDS.get(source_type, ()):
        if field in values:
            metadata[field] = values[field]
        elif hasattr(record, field):
            metadata[field] = getattr(record, field)

    if "private" in metadata:
        metadata["private"] = metadata["private"] in (True, 1, "1")
    if "tags" in metadata:
        metadata["tags"] = [_decode(tag) for tag in metadata["tags"]]
    if "size" in metadata:
        metadata["size"] = int(metadata["size"])
    if source_type == "log.auth" and name:
        components = name.split(" :: ", 2)
        if len(components) == 3:
            metadata.setdefault("hostname", components[0])
            metadata.setdefault("process", components[1])

    stable_source = os.fsdecode(source_identity) if source_identity is not None else ""
    source_digest = sha256(stable_source.encode("utf-8", errors="replace")).hexdigest()[:16]
    suffix = (
        "id:{}".format(source_record_id)
        if source_record_id is not None
        else "position:{}".format(position)
    )
    source_key = "{}:{}:{}".format(source_type, source_digest, suffix)

    return SourceRecord(
        startDate=start_date,
        endDate=values.get("endDate"),
        duration=values.get("duration"),
        source_key=values.get("source_key") or source_key,
        url=_decode(url),
        name=_decode(name),
        meta=metadata,
    )


def normalize_records(source_type, records, source_identity=None):
    """Yield normalized records from an existing source parser iterator."""
    for position, record in enumerate(records):
        yield normalize_record(source_type, record, source_identity, position)