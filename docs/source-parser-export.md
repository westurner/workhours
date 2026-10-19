# Source Parser Export

`workhours_parser` provides the canonical record contract and a lazy iterator for
all source types registered by workhours. Importing `workhours_parser` or its
registry does not initialize Pyramid. Source implementations and their optional
runtime dependencies are loaded only when that source type is selected.

Install the parser and sqlite-utils workflow without the web application:

```bash
pip install "workhours[sqlite]"
```

Install the Pyramid application and ETL CLI with `pip install
"workhours[app]"`. For development and the complete test suite, install
`pip install -e ".[app,sqlite,test,docs]"`.

## Record Contract

Every iterator yields an immutable `SourceRecord` with required `startDate`,
`source_key`, and validated `meta`, plus optional `endDate`, `duration`, `url`,
and `name`. Point events carry only `startDate`; parsers do not invent interval
values. A duration is fixed-unit ISO 8601 and must agree with `endDate` when both
are present. Timezone-aware timestamps are serialized as ISO 8601. Naive source
timestamps remain naive because the source has not established a timezone.

The versioned metadata schema is
[`workhours_parser/schemas/source-record-v1.json`](../workhours_parser/schemas/source-record-v1.json).
Common metadata includes the parser identifier, zero-based output position,
and source database row ID when available. Source IDs are used for stable keys;
otherwise the key combines the source type, a SHA-256 prefix of the input path,
and parser position. Database-backed history is ordered by source row ID.

Known source-specific metadata includes bookmark `tags`, `private`, `comment`,
and `path`; shell-log `session`; auth-log `hostname` and `process`; and `find`
file `size` in bytes, owner `user`, and file `type`. Unknown metadata properties
are rejected. Generic bookmarks with no usable creation timestamp are skipped
rather than assigned a fabricated date. Malformed shell-log lines are dropped;
malformed JSON and invalid `find` timestamps raise errors.

## SQLite Export

The sqlite-utils plugin registers `sqlite-utils workhours`:

```bash
sqlite-utils workhours events.db bookmarks.json bookmarks.json --table events --mode upsert
```

The table uses `source_key` as its primary key and stores canonical timestamp,
duration, URL, name, and JSON-encoded `meta` columns. `append` is the default and
fails on duplicate keys, `upsert` replaces matching source keys, and `rebuild`
drops and recreates only the selected table. Writes are atomic. Existing tables
must have `source_key` as their sole primary key; their other columns are kept.

The same iterator is available in Python:

```python
from sqlite_utils import Database
from workhours_parser import iter_records
from workhours_parser.exporter import export_records

with Database("events.db") as database:
    export_records(
        database,
        iter_records("bookmarks.json", "bookmarks.json"),
        mode="upsert",
    )
```

## Dogsheep Beta

Dogsheep Beta is downstream of the exported table. Its query can map the
canonical record fields to the expected index fields while constructing
searchable text:

```sql
select
    source_key as key,
    name as title,
    startDate as timestamp,
    trim(coalesce(name, '') || ' ' || coalesce(url, '')) as search_1
from events;
```

The legacy workhours ETL remains available with `workhours[app]`. It maps
`startDate` and `name` to `Event.date` and `Event.title`, and persists
`end_date`, `duration`, and `source_key` as additional nullable columns. Run
`alembic upgrade head` against an existing workhours database before using the
new fields.

The Python record contract and SQLite adapter are implemented. Rust parser
ports, Rust/Python parity, complete coverage gates, and end-to-end Dogsheep
index verification remain separate follow-up phases.