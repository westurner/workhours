# AGENTS.md — `workhours`

## Project Overview

`workhours` is a Python event aggregation system and reporting web application created by Wes Turner (New BSD License). It consists of two primary components coupled by a shared SQLAlchemy data model and database:

1. **ETL System & CLI (`workhours`)**: Extracts, parses, and aggregates timestamped events from multiple local data sources into a file store (`fs.url`) and a SQL database (`db_main.url`), with optional Elasticsearch indexing (`esdb.url`).
2. **Reports Web Application**: A Pyramid-based WSGI web application with RESTful endpoints (`pyramid-restler`), Jinja2 templates (`pyramid-jinja2`), Deform forms (`pyramid-deform`), and DataTables views for browsing and analyzing aggregated events, places, domains, projects, and reports.

---

## Architecture & Directory Structure

- `workhours/` — Main Python package:
  - `__init__.py` — Pyramid WSGI application factory (`workhours:main`) and test app configurator (`configure_test_app`).
  - `climain.py` — CLI entry point (`workhours.climain:main`) for parsing sources and generating reports (`events`, `gap`).
  - `tasks/` — Task queue definitions (`QUEUES`) and ETL execution (`update_task_queues`, `parse_event_source`).
  - `models/` — Data layer:
    - `sql/` — SQLAlchemy tables, mappers, and ORM models (`Event`, `Place`, `TaskQueue`, `TaskSource`, `Task`, `User`).
    - `es/` — Elasticsearch integration (`pyes`).
    - `files.py` — Filestore / temporary task directory management.
    - `dataframes.py` — Data analysis helpers.
    - `fixtures/` — Test fixtures (`fixture` library) for database-backed unit tests.
  - **Source Parsers**:
    - `bookmarks/` — HTML and JSON bookmark parsers (`bookmarks.html`, `bookmarks.json`).
    - `delicious/` — Delicious bookmark exports (`delicious.bookmarks`).
    - `firefox/` — Firefox `places.sqlite` history and bookmarks (`firefox.history`, `firefox.bookmarks`).
    - `webkit/` — Chrome/WebKit SQLite history and JSON bookmarks (`webkit.history`, `webkit.bookmarks`).
    - `syslog/` — Unix system and shell logs (`log.shell`, `log.wtmp`, `log.auth`, `find`).
    - `trac/` — Trac timeline HTML (`trac.timelines`).
  - **Web Application Modules**:
    - `events/`, `places/`, `reports/` — Models, RESTful views (`EventsRESTfulView`, `PlacesRESTfulView`, `DomainsView`, `ProjectsView`, `WikipediaPagesView`), and templates.
    - `site/`, `security/`, `forms/` — Site views, authentication/CSRF, Colander/Deform schemas, and Jinja2 template filters.
    - `routes.py`, `resource.py`, `views.py`, `serve.py`, `pshell.py` — Routing (`add_restful_routes`), traversal root (`APIRoot`), and server helpers.
    - `templates/` & `static/` — Jinja2 templates and static frontend assets.
    - `client-src/` — Frontend build assets (Gulp, CoffeeScript, Sass).
    - `testing/` — `PyramidTestCase` and `PyramidFixtureTestCase` base classes for tests.
- `src/pyutmp/` — Vendored Cython/C extension wrapping Unix `utmp`/`wtmp` structures (`pyutmp`).
- `migration/` & `alembic.ini` — Alembic database migration scripts and configuration.
- `development.ini` & `cli.ini` — Pyramid WSGI configuration and CLI ETL configuration files.
- `pyproject.toml`, `setup.py`, `setup.cfg`, `tox.ini` — Setuptools packaging, dependencies, entry points, and test environment configuration.
- `Dockerfile` & `.devcontainer/devcontainer.json` — Python 3.14 Bookworm development container configuration.

---

## Entry Points

- **Console Script**: `workhours = workhours.climain:main`
- **Paste App Factory**: `main = workhours:main` (under `[paste.app_factory]`)

---

## Setup & Development Workflow

### Dev Container (`python:3.14-bookworm`)

Open the repository in VS Code Dev Containers (configured via `.devcontainer/devcontainer.json` and `Dockerfile`). The container provides Python 3.14, `gcc`/`build-essential`, `cython`, `pytest`, `pytest-cov`, `tox`, `uv`, and `pdbpp`, and automatically installs `src/pyutmp` and `workhours` on creation.

### Installing Dependencies

Build and install the bundled `pyutmp` Cython extension first, then install `workhours` in editable mode:

```bash
pip install --no-build-isolation -e src/pyutmp
pip install -e ".[test,docs]"
```

### Running Tests

Run the test suite in the devcontainer using `tox` or `pytest`:

```bash
# Run default py314 tox environment
tox

# Or target specific tox environments
tox -e py314
tox -e cover

# Or run pytest directly
pytest
```

Tests are located across subpackages (`workhours/*/tests/test_*.py` and `workhours/models/*/tests/test_*.py`) and use `unittest.TestCase` / `workhours.testing.PyramidFixtureTestCase`.

### Running the CLI

```bash
# Show CLI options
workhours --help

# List supported event source types and report types
workhours --list-source-types
workhours --list-report-types

# Parse configured sources and run an events report
workhours -c cli.ini --db sqlite:///events.db --fs ./tmpfs -P -r events
```

### Running the Web Application

```bash
pserve development.ini --reload
```

---

## Agent Guidelines

- **Python 3 Compatibility**: Ensure all code and configuration Changes are compatible with modern Python 3 (targeting Python 3.14). Avoid legacy Python 2 constructs or deprecated packaging APIs (such as `imp` or `pip.req`).
- **Database & Fixtures in Tests**: Tests using `PyramidFixtureTestCase` rely on SQLite test databases and the `fixture` package (`workhours/models/fixtures/data.py`). Ensure database sessions and transactions are properly cleaned up in `tearDown`.
- **Packaging**: Keep `pyproject.toml`, `setup.py`, and `tox.ini` synchronized when modifying dependencies, entry points, or test commands.
- **Native Extensions**: `src/pyutmp` requires `cython`, a C compiler (`gcc`), and Python development headers (`python3-dev`) to build from `pyutmp_linux.pyx`.
