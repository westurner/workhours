import json
from datetime import datetime, timezone

import pytest
from click.testing import CliRunner
from sqlite_utils import Database

from workhours_parser import SourceRecord
from workhours_parser.exporter import export_records
from workhours_parser.sqlite_utils_plugin import register_commands


def record(key, name):
    return SourceRecord(
        startDate=datetime(2024, 1, 2, tzinfo=timezone.utc),
        source_key=key,
        name=name,
        meta={"source": "firefox.history"},
    )


def test_export_append_upsert_and_rebuild():
    database = Database(memory=True)
    first = record("source:1", "first")

    assert export_records(database, [first]) == 1
    with pytest.raises(Exception):
        export_records(database, [first], mode="append")

    assert export_records(database, [record("source:1", "updated")], mode="upsert") == 1
    saved = database["events"].get("source:1")
    assert saved["name"] == "updated"
    assert json.loads(saved["meta"]) == {"source": "firefox.history"}
    assert database["events"].pks == ["source_key"]

    assert export_records(database, [record("source:2", "rebuilt")], mode="rebuild") == 1
    assert [row["source_key"] for row in database["events"].rows] == ["source:2"]


def test_export_rejects_existing_table_with_other_primary_key():
    database = Database(memory=True)
    database["events"].insert({"id": 1, "name": "legacy"}, pk="id")

    with pytest.raises(ValueError, match="source_key"):
        export_records(database, [record("source:1", "value")])


def test_plugin_registers_workhours_command():
    import click

    cli = click.Group()
    register_commands(cli)

    assert "workhours" in cli.commands


def test_plugin_exports_json_source(tmp_path):
    import click

    source = tmp_path / "bookmarks.json"
    source.write_text(
        json.dumps(
            [
                {
                    "date": "2024-01-02T00:00:00+00:00",
                    "url": "https://example.test",
                    "title": "Example",
                }
            ]
        ),
        encoding="utf-8",
    )
    database_path = tmp_path / "export.db"
    cli = click.Group()
    register_commands(cli)

    result = CliRunner().invoke(
        cli,
        [
            "workhours",
            str(database_path),
            "bookmarks.json",
            str(source),
            "--mode",
            "upsert",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Exported 1 records" in result.output
    database = Database(database_path)
    exported = next(database["events"].rows)
    assert exported["name"] == "Example"
    assert exported["startDate"] == "2024-01-02T00:00:00+00:00"