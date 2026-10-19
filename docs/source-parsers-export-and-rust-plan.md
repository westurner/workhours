# Source Parser Export and Rust Port Plan

**Status:** Proposed

## Objectives

- Refactor every supported source parser to yield database-neutral records.
- Use those records from both workhours' SQLAlchemy ETL and `sqlite-utils` exports.
- Provide a complete pure-Python implementation and an optional Rust implementation built with PyO3 and maturin.
- Reach 100% statement and branch coverage for supported Python parsers and verify equivalent Rust behavior.
- Keep both user workflows supported: `workhours` and `sqlite-utils`.

## Current Baseline

`QUEUES` in [workhours/tasks/events.py](../workhours/tasks/events.py) registers 12 parsers for Firefox, WebKit, Delicious, Trac, session/shell logs, `find`, `wtmp`, auth logs, and generic HTML/JSON bookmarks. Their outputs vary between ORM instances, tuples, and dictionaries. `Event.from_uhm()` in [workhours/models/__init__.py](../workhours/models/__init__.py) adapts those legacy shapes.

The current coverage baseline for the 12 registered parser modules is **214/491 statements (43.58%)** and **22/124 branches (17.74%)**. The registered generic bookmark parsers are stubs and must be implemented or explicitly retired before declaring completion.

The repository's `src/` is already untracked and contains user work. Preserve it, especially `src/pyutmp`. Add upstream checkouts only as distinct reference directories; do not treat them as runtime dependencies or package them with workhours. The setuptools configuration currently excludes `src*`.

## Target Design

### Neutral parser contract

Introduce a lightweight immutable `SourceRecord` contract with the normalized fields needed by both sinks:

```text
startDate   required event start timestamp
endDate     optional event end timestamp
duration    optional ISO 8601 duration
url         optional URL or source location
name        optional short description (schema.org/Event name)
meta        object validated against the master metadata schema
source_key  stable identity within the source
```

Use `startDate` for point events when a source has only one timestamp; set `endDate` and `duration` only when the source represents an interval. Do not invent an end time or duration. When both end and duration are supplied, require them to agree. Preserve timezone information and serialize timestamps as ISO 8601. `name` replaces the proposed `title` field; keep `url` optional.

The current `Event.meta` is an unrestricted mapping, and the parser modules do not define shared metadata schemas. Phase 0 must inventory every parser's auxiliary output and existing `.meta` shape, then distill them into one versioned JSON Schema for `meta`. Put shared, typed properties in common definitions and source-specific properties in named definitions, documenting types, units, optionality, and provenance. Validate records against that master schema; do not silently discard fields or leave parser outputs as unvalidated arbitrary objects.

Each parser should expose an iterator such as `iter_records(source, options)`. Define deterministic `source_key` rules: prefer stable source identifiers; otherwise use a documented source identity plus record position. Do not generate random keys or collapse legitimate duplicates. Document naive-datetime interpretation, byte decoding, ordering, and malformed-input behavior. Keep the parser core independent of ORM, Pyramid, sqlite-utils, and Rust.

### Two persistence adapters

- **SQLAlchemy:** Adapt `SourceRecord` to `Event` in the existing ETL path. Preserve queue names, task/source IDs, place lookup, transactions, and current CLI behavior. Map `startDate`/`name` to the legacy `Event.date`/`Event.title` fields during compatibility, and add persistence plus a migration for `endDate` and `duration` so interval data is not lost.
- **SQLite:** Insert records using sqlite-utils APIs into a documented schema using the canonical field names and master `meta` schema, with a stable primary key and explicit append/upsert/rebuild semantics. Make table naming configurable and handle existing tables predictably.

The adapters consume the same parser iterator; parsers must not contain sink-specific logic. Dogsheep Beta is a downstream indexer and Datasette search plugin, not an exporter. Include an example Dogsheep query mapping `source_key` to `key`, `name` to `title`, and `startDate` to `timestamp`, plus searchable text to `search_1`.

### CLI and packaging

Provide a sqlite-utils CLI plugin using its `register_commands(cli)` entry point, with commands under a namespace such as `sqlite-utils workhours ...`. Keep the existing `workhours` CLI as the ETL interface; add a direct export command only if it avoids duplicate logic.

Prototype clean installation before choosing distribution boundaries. The parser import path must not require Pyramid: importing `workhours` currently imports the application stack in [workhours/__init__.py](../workhours/__init__.py). If necessary, separate a lightweight parser package from the app and plugin packages, all sharing one parser contract. Do not make sqlite-utils users install the full web application unnecessarily.

## Python and Rust Backends

The pure-Python parser is the required baseline and remains independently installable without Rust tooling. Port parsing logic to Rust through PyO3, build with maturin, and expose it as an optional backend behind the same `iter_records` contract. Keep explicit backend selection (`python` or `rust`); automatic native selection should wait until parity and wheel installation are reliable. Translate Rust errors into stable Python exceptions without losing useful source context.

Interpret “O3” as Rust release optimization level 3 (`opt-level = 3`) unless the project owner means something else. Confirm this in the build prototype. Benchmark representative inputs before claiming a speedup, including end-to-end export where SQLite insertion may dominate. Native wheels should be provided for supported platforms; unsupported platforms must still have a documented Python-only path.

## Parser Scope

The minimum scope is every callable registered in `QUEUES`:

| Family | Modules |
| --- | --- |
| Firefox bookmarks/history | `workhours/firefox/history.py` |
| WebKit bookmarks/history | `workhours/webkit/bookmarks.py`, `workhours/webkit/history.py` |
| Delicious bookmarks | `workhours/delicious/bookmarks.py` |
| Trac timeline | `workhours/trac/timeline.py` |
| Session/shell logs | `workhours/syslog/sessionlog.py` |
| Find output | `workhours/syslog/find.py` |
| Wtmp/auth logs | `workhours/syslog/wtmp.py`, `workhours/syslog/authlog.py` |
| Generic bookmarks | `workhours/bookmarks/json.py`, `workhours/bookmarks/html.py` |

Inventory other supported parser callables too.

Decide explicitly whether `workhours/firefox/merge-bookmarks.py` is in scope; if supported, include its parsing logic in parity and coverage tests. CLI glue need not be ported to Rust, but parser logic must not be hidden there. Retire unsupported callables explicitly rather than excluding them silently.

## Phases and Exit Criteria

### Phase 0: Inventory and spike

- Inventory inputs, options, output semantics, encodings, timestamps, ordering, errors, and all existing parser `.meta` shapes for supported parsers; produce the versioned master metadata JSON Schema.
- Clone Datasette, Dogsheep Beta, and sqlite-utils into distinct `src/` reference directories; record revisions and preserve existing files.
- Prototype importing the parser core and installing the sqlite-utils command without Pyramid setup.
- **Exit:** Every parser has fixtures and a documented output mapping; plugin discovery works in a clean environment.

### Phase 1: Normalize Python parsers

- Add `SourceRecord` and migrate parsers in source-family batches.
- Use temporary compatibility adapters only where needed, then remove them.
- Preserve `QUEUES` identifiers, input file handling, and workhours event behavior.
- Validate parser metadata against the master schema; add SQLAlchemy persistence and a migration for interval end/duration while maintaining legacy `date`/`title` compatibility.
- Implement or explicitly retire the generic bookmark stubs.
- **Exit:** Fixture tests verify normalized records; ETL tests verify unchanged event fields and task/source associations.

### Phase 2: SQLite exporter and Dogsheep integration

- Implement the sqlite-utils exporter, plugin entry point, schema, deterministic re-import behavior, and clear error handling.
- Add Dogsheep Beta example configuration and verify indexing/search against an exported fixture database.
- **Exit:** Export works without Pyramid/SQLAlchemy setup, repeated exports are predictable, and the same source still works through workhours.

### Phase 3: Python coverage gate

- Add parser fixtures for valid, empty, malformed, boundary-time, duplicate, encoding, compressed, and database-backed inputs as applicable.
- Add a dedicated parser-only coverage command with branch coverage and a 100% threshold; report coverage per module and add no exclusions to reach the target.
- Test both persistence adapters against the same records.
- **Exit:** Every supported Python parser reaches 100% statements and branches; both sinks preserve normalized fields and key semantics.

### Phase 4: Rust foundation and ports

- Add the PyO3/maturin crate, backend selection, error mapping, and Python fallback.
- Port one parser each from SQLite, structured text (HTML/JSON), and line-oriented logs; validate the build and parity approach before porting the rest.
- Run the same fixtures against both backends and compare ordered records, timestamps, metadata, and failures.
- **Exit:** All supported parsers run through both backends; parity passes; Python-only install needs no compiler; native wheels install on supported platforms.

### Phase 5: Benchmarks and release

- Benchmark representative small and large inputs on both backends, including export time; document toolchain, platform, and input size.
- Keep Rust optional unless results and wheel coverage justify making it the default.
- Document installation, backend selection, source limitations, schema, Dogsheep setup, and migration from legacy parser outputs.
- **Exit:** Users can choose either workflow and receive the same parser records through supported installation paths.

## Verification Policy

- Python: 100% statement and branch coverage per supported parser module, enforced by a dedicated command.
- Rust: cover each parser's success and error paths with the same fixtures; enforce native branch/line coverage where tooling permits, and document any unsupported metric per module.
- Parity: compare Python and Rust output for every fixture, preserving order and validating `meta` against the master schema; test timezone, Unicode/bytes, malformed input, and duplicates.
- Integration: separately test workhours SQLAlchemy persistence, sqlite-utils export, repeated export semantics, and Dogsheep Beta indexing.
- Performance: benchmark as evidence, not as a substitute for parity, correctness, or coverage.

## Decisions and Risks

- Existing parser outputs encode implicit event semantics; capture interval boundaries, URLs, names, metadata, and filtering before replacing adapters. Preserve old `date`/`title` consumers during migration.
- The current `workhours` package import path brings in the app stack; establish a parser-only boundary before promising standalone installation.
- Optional native packaging brings compiler and platform-wheel support costs; Python must remain complete and usable.
- Confirm whether “O3” means Rust `opt-level = 3` before tuning.
- The 12 registered parsers are the minimum scope; inventory and disposition all other supported callables before claiming all parsers are covered.
- Upstream clones are references for APIs/tests only and must not enter the runtime package.