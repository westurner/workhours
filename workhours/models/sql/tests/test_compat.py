from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import clear_mappers


def test_cli_loads_registered_sources_and_reports(capsys):
    from workhours.climain import main

    assert main("--list-source-types") == 0
    source_output = capsys.readouterr().out
    assert "firefox.history" in source_output
    assert "webkit.history" in source_output

    assert main("--list-report-types") == 0
    report_output = capsys.readouterr().out
    assert "gap :=" in report_output
    assert "events :=" in report_output


def test_sqlite_schema_uses_explicit_engine():
    from workhours.models.sql import initialize_sql
    from workhours.models.sql import tables

    engine = create_engine("sqlite:///:memory:")
    meta = None
    try:
        clear_mappers()
        tables._MAPPED = False
        meta = initialize_sql(
            engine, tables.setup_mappers, create_tables_on_init=True
        )

        assert meta.engine is engine
        assert "events" in inspect(engine).get_table_names()
    finally:
        if meta is not None:
            meta.Session.remove()
        clear_mappers()
        tables._MAPPED = False
        engine.dispose()


def test_webkit_history_maps_reflected_tables():
    from sqlalchemy import text
    from sqlalchemy.orm import joinedload, sessionmaker

    from workhours.models.sqla_utils import clear_mappers as clear_registry
    from workhours.webkit.history import URL, Visit, setup_mappers

    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE urls (id INTEGER PRIMARY KEY, url TEXT, title TEXT)"
            )
        )
        connection.execute(
            text(
                "CREATE TABLE visits (id INTEGER PRIMARY KEY, url INTEGER, visit_time INTEGER)"
            )
        )
        connection.execute(
            text("INSERT INTO urls VALUES (1, 'https://example.test', 'Example')")
        )
        connection.execute(text("INSERT INTO visits VALUES (1, 1, 0)"))

    session = None
    try:
        setup_mappers(engine=engine)
        session = sessionmaker(bind=engine)()
        visit = session.query(Visit).options(joinedload(Visit._url)).one()

        assert visit._url.url == "https://example.test"
    finally:
        if session is not None:
            session.close()
        clear_registry((URL, Visit))
        engine.dispose()


def test_firefox_history_maps_reflected_tables():
    from sqlalchemy import text
    from sqlalchemy.orm import joinedload, sessionmaker

    from workhours.firefox.history import Bookmark, Place, Visit, setup_mappers
    from workhours.models.sqla_utils import clear_mappers as clear_registry

    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TABLE moz_places (id INTEGER PRIMARY KEY, url TEXT, title TEXT)"
            )
        )
        connection.execute(
            text(
                "CREATE TABLE moz_historyvisits (id INTEGER PRIMARY KEY, place_id INTEGER, visit_date INTEGER)"
            )
        )
        connection.execute(
            text(
                "CREATE TABLE moz_bookmarks (id INTEGER PRIMARY KEY, fk INTEGER, dateAdded INTEGER, title TEXT)"
            )
        )
        connection.execute(
            text("INSERT INTO moz_places VALUES (1, 'https://example.test', 'Example')")
        )
        connection.execute(
            text("INSERT INTO moz_historyvisits VALUES (1, 1, 1700000000000000)")
        )

    session = None
    try:
        setup_mappers(engine=engine)
        session = sessionmaker(bind=engine)()
        visit = session.query(Visit).options(joinedload(Visit.place)).one()

        assert visit.place.url == "https://example.test"
    finally:
        if session is not None:
            session.close()
        clear_registry((Bookmark, Place, Visit))
        engine.dispose()