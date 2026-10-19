from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import clear_mappers
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest


def test_cli_loads_registered_sources_and_reports(capsys):
    from workhours.climain import main

    config_file = Path(__file__).parents[4] / "cli.ini"
    assert main("--config", str(config_file), "--list-source-types") == 0
    configured_source_output = capsys.readouterr().out
    assert "firefox.history" in configured_source_output

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

        from workhours.models import TaskQueue

        session = meta.Session()
        queue = TaskQueue.get_or_create(
            TaskQueue.type,
            "test.queue",
            session=session,
            id="test-queue",
            type="test.queue",
        )
        session.add(queue)
        session.flush()
        assert session.query(TaskQueue).filter_by(type="test.queue").one() is queue
    finally:
        if meta is not None:
            meta.Session.remove()
        clear_mappers()
        tables._MAPPED = False
        engine.dispose()


def test_update_task_queues_uses_bound_session(tmp_path):
    from workhours.models import TaskQueue
    from workhours.models.sql import initialize_sql
    from workhours.models.sql import tables
    from workhours.tasks.events import update_task_queues

    database_url = f"sqlite:///{tmp_path / 'events.db'}"
    engine = create_engine(database_url)
    meta = None
    try:
        clear_mappers()
        tables._MAPPED = False
        meta = initialize_sql(
            engine, tables.setup_mappers, create_tables_on_init=True
        )

        update_task_queues(database_url, {"test.queue": []}, "tmp")

        session = meta.Session()
        assert session.query(TaskQueue).filter_by(type="test.queue").one()
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


def test_open_db_uses_default_mapper_and_recovers_sqlite():
    from workhours.models import sql
    from workhours.models.sql import tables

    engine = object()
    meta = mock.Mock()
    setup_mappers = mock.Mock()
    with (
        mock.patch.object(sql, "create_engine", side_effect=[RuntimeError(), engine]),
        mock.patch.object(sql, "initialize_sql", return_value=meta) as initialize,
        mock.patch.object(sql, "_clear_mappers") as clear_mappers,
        mock.patch.object(sql, "create_tables", return_value=meta) as create_tables,
        mock.patch("workhours.models.sqlite_utils.commit_uncommitted_transactions") as recover,
        mock.patch.object(tables, "setup_mappers", setup_mappers),
    ):
        result = sql.open_db(
            "sqlite:///events.db",
            destructive_recover=True,
            munge_mappers=[object()],
            create_tables_on_init=True,
        )

    assert result is meta
    recover.assert_called_once_with("sqlite:///events.db")
    initialize.assert_called_once_with(engine, setup_mappers)
    clear_mappers.assert_called_once()
    create_tables.assert_called_once_with(meta)


def test_open_db_propagates_nonrecoverable_errors():
    from workhours.models import sql

    with mock.patch.object(sql, "create_engine", side_effect=RuntimeError("bad database")):
        with pytest.raises(RuntimeError, match="bad database"):
            sql.open_db(
                "postgresql://example.test/database", destructive_recover=True
            )


def test_initialize_sql_creates_tables_and_binds_metadata():
    from workhours.models import sql

    engine = object()
    base = SimpleNamespace()
    with mock.patch.object(
        sql, "create_tables", side_effect=lambda metadata: metadata
    ) as create_tables:
        meta = sql.initialize_sql(
            engine,
            lambda **kwargs: kwargs["meta"],
            create_tables_on_init=True,
            Base=base,
        )

    create_tables.assert_called_once_with(meta)
    assert base.metadata is meta
    assert meta.engine is engine


def test_initialize_sql_test_sets_optional_base_metadata():
    from workhours.models import sql
    from workhours.models.sql import tables

    meta = mock.Mock()
    base = SimpleNamespace()
    with (
        mock.patch.object(sql, "initialize_sql", side_effect=[meta, meta]),
        mock.patch.object(sql, "drop_tables"),
        mock.patch.object(sql, "clear_mappers"),
        mock.patch.object(tables, "_MAPPED", True),
    ):
        result = sql._initialize_sql_test(engine=object(), Base=base)

    assert result is meta
    assert base.metadata is base