import unittest
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest import mock

from workhours.reports import gaps
from workhours.reports import places as report_places


class GapReportTests(unittest.TestCase):
    def test_add_gap_tuples_empty_close_and_wide_gaps(self):
        start = datetime(2024, 1, 1)
        rows = [
            (start, "first"),
            (start + timedelta(minutes=15), "close"),
            (start + timedelta(minutes=31), "wide"),
        ]

        self.assertEqual(
            list(gaps.add_gap_tuples([], ("date", "url"))), []
        )
        self.assertEqual(
            list(
                gaps.add_gap_tuples(
                    rows, ("date", "url"), date_attr=lambda row: row[0]
                )
            ),
            [rows[0], rows[1], ("--------", "--------"), rows[2]],
        )

    def test_create_gap_csv_delegates_selected_rows(self):
        class Selection:
            @classmethod
            def select_columns(cls, attrs, order_by):
                return [("row", attrs, order_by)]

        with mock.patch.object(gaps, "write_csv", return_value="written") as writer:
            result = gaps.create_gap_csv(Selection, "events.csv")

        self.assertEqual(result, "written")
        args, kwargs = writer.call_args
        self.assertEqual(args[0], "events.csv")
        self.assertTrue(list(args[1]))
        self.assertEqual(kwargs, {"unicode_mangle": True})


class PlaceReportTests(unittest.TestCase):
    def setUp(self):
        self.query = mock.MagicMock()
        self.query.filter.return_value = self.query
        self.request = SimpleNamespace(
            db_session=mock.Mock(return_value=SimpleNamespace(query=mock.Mock(return_value=self.query)))
        )

    @staticmethod
    def place(netloc, path, url, eventcount=1, events=None):
        return SimpleNamespace(
            netloc=netloc,
            path=path,
            url=url,
            eventcount=eventcount,
            events=events or [],
        )

    def test_projects_filter_reserved_and_group_repository_urls(self):
        rows = [
            self.place("github.com", "/owner/repo/issues", "https://github.com/owner/repo/issues", None),
            self.place("github.com", "/owner/repo/pulls", "https://github.com/owner/repo/pulls", 2),
            self.place("bitbucket.org", "/team/project", "https://bitbucket.org/team/project", 0),
            self.place("github.com", "/settings/repo", "https://github.com/settings/repo"),
            self.place("code.google.com", "/p/legacy/trunk", "https://code.google.com/p/legacy"),
            self.place("code.google.com", "/project/legacy", "https://code.google.com/project/legacy"),
            self.place("example.com", "/owner/repo", "https://example.com/owner/repo"),
            self.place("github.com", "/owner", "https://github.com/owner"),
        ]
        self.query.__iter__.return_value = iter(rows)
        model = SimpleNamespace(netloc=mock.Mock())

        with mock.patch.object(report_places, "Place", model):
            reports = list(report_places.ProjectsContext(self.request).generate_report())

        self.assertEqual(
            reports,
            [
                (
                    "github.com/owner/repo",
                    ["https://github.com/owner/repo/issues", "https://github.com/owner/repo/pulls"],
                    3,
                ),
                ("bitbucket.org/team/project", ["https://bitbucket.org/team/project"], 1),
                ("code.google.com/p/legacy", ["https://code.google.com/p/legacy"], 1),
            ],
        )

    def test_wikipedia_report_handles_single_and_multiple_urls(self):
        rows = [
            self.place("en.wikipedia.org", "/wiki/Article", "https://en.wikipedia.org/wiki/Article", events=["one"]),
            self.place("en.wikipedia.org", "/wiki/Article", "https://en.wikipedia.org/wiki/Article?old", events=["two", "three"]),
            self.place("fr.wikipedia.org", "/wiki/Other", "https://fr.wikipedia.org/wiki/Other"),
            self.place("en.wikipedia.org", "/w/index.php", "https://en.wikipedia.org/w/index.php"),
        ]
        self.query.all.return_value = rows
        model = SimpleNamespace(netloc=mock.Mock())

        with mock.patch.object(report_places, "Place", model):
            reports = list(report_places.WikipediaPagesContext(self.request).generate_report())

        self.assertEqual(len(reports), 2)
        self.assertEqual(reports[0]["url"], "en.wikipedia.org/wiki/Article")
        self.assertEqual(
            reports[0]["urls"],
            [
                "https://en.wikipedia.org/wiki/Article",
                "https://en.wikipedia.org/wiki/Article?old",
            ],
        )
        self.assertEqual(reports[0]["count"], 3)
        self.assertEqual(reports[1]["url"], "fr.wikipedia.org/wiki/Other")
        self.assertFalse(reports[1]["urls"])
        self.assertEqual(reports[1]["count"], 1)
