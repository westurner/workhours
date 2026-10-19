from datetime import datetime, timedelta, timezone

import pytest

from workhours_parser import (
    SourceRecord,
    SourceRecordError,
    normalize_record,
    normalize_records,
)


def test_record_is_immutable_and_serializes_timezone():
    record = SourceRecord(
        startDate=datetime(2024, 1, 2, 3, tzinfo=timezone.utc),
        source_key="firefox.history:visit-7",
        meta={"source": "firefox.history", "source_record_id": 7},
    )

    assert record.to_dict()["startDate"] == "2024-01-02T03:00:00+00:00"
    assert record.to_dict()["meta"]["source_record_id"] == 7
    with pytest.raises(TypeError):
        record.meta["source_record_id"] = 8
    with pytest.raises(AttributeError):
        record.name = "changed"


def test_record_accepts_agreeing_interval_and_round_trips():
    record = SourceRecord(
        startDate="2024-01-02T03:00:00+00:00",
        endDate="2024-01-02T04:30:00+00:00",
        duration="PT1H30M",
        source_key="log.shell:1",
        name="command",
        meta={"source": "log.shell", "session": "abc"},
    )

    assert SourceRecord.from_dict(record.to_dict()) == record
    assert record.endDate - record.startDate == timedelta(hours=1, minutes=30)


@pytest.mark.parametrize(
    "values",
    [
        {"startDate": "2024-01-02T03:00:00", "source_key": "x", "meta": {}},
        {
            "startDate": "2024-01-02T03:00:00",
            "endDate": "2024-01-02T04:00:00",
            "duration": "PT30M",
            "source_key": "x",
            "meta": {"source": "log.shell"},
        },
        {
            "startDate": "2024-01-02T03:00:00",
            "source_key": "x",
            "meta": {"source": "delicious.bookmarks", "private": "false"},
        },
        {
            "startDate": "2024-01-02T03:00:00",
            "source_key": "x",
            "meta": {"source": "firefox.history", "unregistered": "value"},
        },
        {
            "startDate": "2024-01-02T03:00:00",
            "duration": "P1DT",
            "source_key": "x",
            "meta": {"source": "log.shell"},
        },
    ],
)
def test_record_rejects_invalid_metadata_and_intervals(values):
    with pytest.raises(SourceRecordError):
        SourceRecord(**values)


def test_legacy_dictionary_preserves_delicious_metadata_and_stable_key():
    row = {
        "date": datetime(2024, 1, 2),
        "url": "https://example.test/",
        "title": "Example",
        "tags": ["reference", "work"],
        "private": 0,
        "comment": "saved for later",
    }

    first = normalize_record("delicious.bookmarks", row, "/data/bookmarks.html", 2)
    again = normalize_record("delicious.bookmarks", row, "/data/bookmarks.html", 2)

    assert first == again
    assert first.meta["tags"] == ("reference", "work")
    assert first.meta["private"] is False
    assert first.meta["comment"] == "saved for later"
    assert first.meta["record_position"] == 2


def test_legacy_find_record_preserves_fields_and_duplicate_positions():
    row = (datetime(2024, 1, 2), "18", "alice", "f", "/tmp/a.txt")
    records = list(normalize_records("find", [row, row], "/tmp/find.tsv"))

    assert records[0].url == "/tmp/a.txt"
    assert records[0].meta["size"] == 18
    assert records[0].meta["user"] == "alice"
    assert records[0].meta["type"] == "f"
    assert records[0].source_key != records[1].source_key


def test_private_string_and_find_size_are_normalized():
    bookmark = normalize_record(
        "delicious.bookmarks",
        {
            "date": datetime(2024, 1, 2),
            "private": "0",
            "tags": [],
        },
        "bookmarks.html",
        0,
    )

    assert bookmark.meta["private"] is False


def test_log_rows_keep_command_session_and_auth_context():
    session_record = normalize_record(
        "log.shell",
        (datetime(2024, 1, 2), "session-1 ::: echo hi", "session-1"),
        "/logs/session.log",
        0,
    )
    auth_record = normalize_record(
        "log.auth",
        (datetime(2024, 1, 2), "host-a :: sshd[12] :: login accepted"),
        "/logs/auth.log",
        0,
    )

    assert session_record.url is None
    assert session_record.name == "session-1 ::: echo hi"
    assert session_record.meta["session"] == "session-1"
    assert auth_record.name == "host-a :: sshd[12] :: login accepted"
    assert auth_record.meta["hostname"] == "host-a"
    assert auth_record.meta["process"] == "sshd[12]"