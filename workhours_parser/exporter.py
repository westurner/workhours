"""sqlite-utils persistence adapter for canonical source records."""

import json

from .records import SourceRecord


TABLE_COLUMNS = {
    "source_key": str,
    "startDate": str,
    "endDate": str,
    "duration": str,
    "url": str,
    "name": str,
    "meta": str,
}
EXPORT_MODES = ("append", "upsert", "rebuild")


def _export_row(record):
    if not isinstance(record, SourceRecord):
        raise TypeError("SQLite export requires validated SourceRecord objects")
    row = record.to_dict()
    row["meta"] = json.dumps(
        row["meta"], ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return row


def export_records(database, records, table_name="events", mode="append"):
    """Write records to sqlite-utils using source_key as the primary key.

    Append fails on duplicate keys, upsert replaces matching rows, and rebuild
    drops and recreates only the selected table. All writes are atomic.
    """
    if mode not in EXPORT_MODES:
        raise ValueError("mode must be one of: {}".format(", ".join(EXPORT_MODES)))
    if not isinstance(table_name, str) or not table_name.strip():
        raise ValueError("table_name must be a non-empty string")

    exported = 0

    def rows():
        nonlocal exported
        for record in records:
            exported += 1
            yield _export_row(record)

    with database.atomic():
        table = database[table_name]
        if mode == "rebuild" and table.exists():
            table.drop()
            table = database[table_name]

        if not table.exists():
            table.create(TABLE_COLUMNS, pk="source_key")
        elif table.pks != ["source_key"]:
            raise ValueError(
                "existing table must use source_key as its sole primary key"
            )

        table = database.table(table_name, alter=True)
        if mode == "upsert":
            table.upsert_all(rows(), pk="source_key", batch_size=1000)
        elif mode == "append":
            table.insert_all(rows(), pk="source_key", batch_size=1000)
        elif records:
            table.insert_all(rows(), pk="source_key", batch_size=1000)

    return exported