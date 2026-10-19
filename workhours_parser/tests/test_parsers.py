import json
import subprocess
import sys
from datetime import datetime, timezone

from workhours_parser.parsers import iter_records


def test_package_and_parser_registry_import_without_pyramid():
    subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys, workhours_parser.parsers; "
            "assert 'pyramid' not in sys.modules",
        ],
        check=True,
    )


def test_generic_json_source_returns_canonical_records(tmp_path):
    source = tmp_path / "source.json"
    source.write_text(
        json.dumps(
            [
                {
                    "date": "2024-01-02T00:00:00+00:00",
                    "url": "https://example.test",
                    "title": "Example",
                    "tags": ["work"],
                }
            ]
        ),
        encoding="utf-8",
    )

    records = list(iter_records("bookmarks.json", source))

    assert len(records) == 1
    assert records[0].startDate == datetime(2024, 1, 2, tzinfo=timezone.utc)
    assert records[0].url == "https://example.test"
    assert records[0].name == "Example"
    assert records[0].meta["source"] == "bookmarks.json"
    assert records[0].meta["tags"] == ("work",)
    assert records[0].source_key.startswith("bookmarks.json:")