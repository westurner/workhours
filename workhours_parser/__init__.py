"""Database-neutral source parser contracts."""

from .records import SourceRecord, SourceRecordError
from .compat import normalize_record, normalize_records

__all__ = [
	"SourceRecord",
	"SourceRecordError",
	"normalize_record",
	"normalize_records",
]