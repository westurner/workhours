import unittest
from types import SimpleNamespace
from unittest import mock
from pyramid import testing

from workhours.models.html import datatables
from workhours.testing import PyramidFixtureTestCase
from workhours.models.html.datatables import datatables_view, read_datatables_params


class Test_datatables(PyramidFixtureTestCase):
    # def setUp(self):
    # self.meta = _initialize_sql_test()
    # self.session = self.meta.Session
    # self.config = testing.setUp()

    def _get_test_request(self, *args, **kwargs):
        request = testing.DummyRequest(*args, **kwargs)
        request.db_session = self.session
        return request

    # def tearDown(self):
    # import transaction
    # transaction.abort()
    # testing.tearDown()

    def test_about_view(self):
        # from workhours.site.views.about import about_view
        request = self._get_test_request()
        datatables_view(request)

    def test_read_datatables_params_modern_protocol(self):
        request = self._get_test_request(
            params={
                "start": "20",
                "length": "50",
                "order[0][column]": "2",
                "order[0][dir]": "desc",
                "search[value]": "workhours",
            }
        )

        self.assertEqual(
            read_datatables_params(request),
            {
                "offset": 20,
                "limit": 50,
                "order_by": 2,
                "sort_dir": "desc",
                "search": "workhours",
            },
        )

    def test_read_datatables_params_legacy_protocol(self):
        request = self._get_test_request(
            params={
                "iDisplayStart": "10",
                "iDisplayLength": "25",
                "iSortCol_0": "1",
                "sSortDir_0": "asc",
                "sSearch": "legacy",
            }
        )

        self.assertEqual(
            read_datatables_params(request),
            {
                "offset": 10,
                "limit": 25,
                "order_by": 1,
                "sort_dir": "asc",
                "search": "legacy",
            },
        )

    def test_read_datatables_params_missing_and_invalid_values(self):
        request = self._get_test_request(params={"start": "invalid"})
        self.assertEqual(read_datatables_params(request), {})

        class BrokenParams:
            def get(self, name):
                raise ValueError(name)

        self.assertIsNone(
            datatables._get_param(SimpleNamespace(params=BrokenParams()), "start", int)
        )

    def test_build_query_with_and_without_filters(self):
        class Query:
            def __init__(self):
                self.calls = []

            def order_by(self, value):
                self.calls.append(("order_by", value))
                return self

            def offset(self, value):
                self.calls.append(("offset", value))
                return self

            def limit(self, value):
                self.calls.append(("limit", value))
                return self

            def filter(self, value):
                self.calls.append(("filter", value))
                return self

        class Session:
            def __init__(self):
                self.query_result = Query()

            def query(self, model):
                return self.query_result

        session = Session()
        empty_request = SimpleNamespace(db_session=session, params={})
        self.assertIs(datatables.build_query(empty_request), session.query_result)
        self.assertEqual(session.query_result.calls, [])

        filtered_request = SimpleNamespace(
            db_session=session,
            params={
                "iSortCol_0": "1",
                "iDisplayStart": "10",
                "iDisplayLength": "20",
                "sSearch": "needle",
            },
        )
        datatables.build_query(filtered_request)
        self.assertEqual(
            [call[0] for call in session.query_result.calls],
            ["order_by", "offset", "limit", "filter"],
        )

    def test_datatables_view_renders_query_results(self):
        query = mock.Mock()
        query.all.return_value = ["row"]
        request = object()
        with mock.patch.object(datatables, "build_query", return_value=query):
            with mock.patch.object(datatables, "render", return_value="rendered") as render:
                self.assertEqual(datatables.datatables_view(request), "rendered")

        render.assert_called_once_with(
            "models/templates/_table.jinja2", dict(value=["row"]), request
        )
