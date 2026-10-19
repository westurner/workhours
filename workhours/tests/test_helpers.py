import io
import runpy
import unittest
from contextlib import redirect_stdout
from datetime import datetime
from types import SimpleNamespace
from unittest import mock

from deform import ValidationFailure
from markupsafe import Markup
from pyramid.httpexceptions import HTTPForbidden

from workhours.firefox import bookmarks
from workhours.forms import render
from workhours.security.csrf import csrf_validation
from workhours.site import templatefilters
from workhours.syslog import find as find_parser
from workhours.trac.timeline import parse_trac_timeline


class CsrfValidationTests(unittest.TestCase):
    def test_ignores_non_post_requests(self):
        request = SimpleNamespace(method="GET", POST={}, session=mock.Mock())

        csrf_validation(SimpleNamespace(request=request))

        request.session.get_csrf_token.assert_not_called()

    def test_rejects_missing_or_invalid_tokens(self):
        for post in ({}, {"_csrf": "invalid"}):
            request = SimpleNamespace(
                method="POST", POST=post, session=mock.Mock()
            )
            request.session.get_csrf_token.return_value = "valid"

            with self.subTest(post=post), self.assertRaises(HTTPForbidden):
                csrf_validation(SimpleNamespace(request=request))

    def test_removes_valid_token(self):
        request = SimpleNamespace(
            method="POST", POST={"_csrf": "valid", "value": "ok"},
            session=mock.Mock(),
        )
        request.session.get_csrf_token.return_value = "valid"

        csrf_validation(SimpleNamespace(request=request))

        self.assertEqual(request.POST, {"value": "ok"})


class FormRenderingTests(unittest.TestCase):
    def setUp(self):
        self.form = mock.Mock()
        self.form.get_widget_resources.return_value = {"css": [], "js": []}

    def test_renders_unsubmitted_form_with_readonly_flag(self):
        request = SimpleNamespace(POST={})
        self.form.render.return_value = "form html"

        result = render.render_form(request, self.form, readonly=True)

        self.form.render.assert_called_once_with(render.colander.null, readonly=True)
        self.assertEqual(str(result["form"]), "form html")
        self.assertEqual(result["captured"], "None")

    def test_renders_valid_submission_and_success_response(self):
        request = SimpleNamespace(POST={"submit": "submit", "value": "ok"})
        self.form.validate.return_value = {"value": "ok"}
        self.form.render.return_value = "submitted html"

        result = render.render_form(request, self.form)
        self.assertEqual(result["captured"], "{'value': 'ok'}")
        self.form.validate.assert_called_once_with(
            [("submit", "submit"), ("value", "ok")]
        )

        self.assertEqual(
            render.render_form(request, self.form, success=lambda: "response"),
            "response",
        )
        result = render.render_form(request, self.form, success=lambda: None)
        self.assertEqual(result["captured"], "{'value': 'ok'}")
        self.form.render.assert_called_with({"value": "ok"})

    def test_renders_validation_failure(self):
        request = SimpleNamespace(POST={"submit": "submit"})
        failure = ValidationFailure(self.form, {}, ValueError("invalid"))
        failure.render = mock.Mock(return_value="invalid html")
        self.form.validate.side_effect = failure

        result = render.render_form(request, self.form)

        failure.render.assert_called_once_with()
        self.assertEqual(str(result["form"]), "invalid html")


class ParserTests(unittest.TestCase):
    def test_trac_timeline_filters_authors_and_parses_dates(self):
        html = """
        <h2>Other section</h2><dl></dl>
        <h2>01/02/24: Changes</h2>
        <dl>
          <dt><span class="author">alice</span>
              <span class="time">09:30</span><a href="/changes/1">one</a></dt>
          <dt><span class="author">bob</span>
              <span class="time">10:00</span><a href="/changes/2">two</a></dt>
          <dt><span class="time">10:30</span><a href="/changes/3">three</a></dt>
        </dl>
        """
        with mock.patch("builtins.open", mock.mock_open(read_data=html)):
            events = list(parse_trac_timeline("timeline.html", ["alice"]))

        self.assertEqual(events, [(datetime(2024, 1, 2, 9, 30), "/changes/1")])

    def test_firefox_bookmark_cli_unquotes_only_quoted_titles(self):
        html = """
        <a href="https%3A%2F%2Fexample.com">\"Example+Title\"</a>
        <a>Unquoted title</a>
        """
        output = io.StringIO()
        with mock.patch("builtins.open", mock.mock_open(read_data=html)):
            with redirect_stdout(output):
                bookmarks.main()

        self.assertEqual(
            output.getvalue(), '== "Example Title" ==\nhttps://example.com\n\n'
        )

    def test_firefox_bookmark_script_entrypoint(self):
        html = '<a href="/bookmark">"Title"</a>'
        output = io.StringIO()
        with mock.patch("builtins.open", mock.mock_open(read_data=html)):
            with redirect_stdout(output):
                runpy.run_path(bookmarks.__file__, run_name="__main__")

        self.assertEqual(output.getvalue(), '== "Title" ==\n/bookmark\n\n')


class TemplateFilterTests(unittest.TestCase):
    def test_autoescape_filter(self):
        escaped = SimpleNamespace(autoescape=True)
        plain = SimpleNamespace(autoescape=False)

        self.assertIsInstance(templatefilters.skipautoescape(escaped, "<tag>"), Markup)
        self.assertEqual(templatefilters.skipautoescape(plain, "<tag>"), "<tag>")

    def test_json_filters_cover_empty_and_autoescaped_values(self):
        escaped = SimpleNamespace(autoescape=True)
        plain = SimpleNamespace(autoescape=False)

        self.assertIsNone(templatefilters.jsonify(escaped, {}))
        self.assertIsInstance(templatefilters.jsonify(escaped, {"key": 1}), Markup)
        self.assertEqual(templatefilters.jsonify(plain, {"key": 1}), '{"key":1}')

        self.assertIsNone(templatefilters.jsonify_indent(plain, {}))
        compact = templatefilters.jsonify_indent(plain, {"_private": 1, "key": 2})
        self.assertNotIn("_private", compact)
        self.assertIn('"key":2', compact)
        pretty = templatefilters.jsonify_indent(escaped, {"key": 2})
        self.assertIsInstance(pretty, Markup)


class FindParserTests(unittest.TestCase):
    def test_parses_find_record_and_formats_event(self):
        record = "0\t12\tuser\tf\t/tmp/file\n"

        events = list(find_parser._parse_find_printf([record], output=None))

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].date, datetime.fromtimestamp(0))
        self.assertEqual(events[0].size, "12")
        self.assertEqual(events[0].user, "user")
        self.assertEqual(events[0].type, "f")
        self.assertEqual(events[0].url, "/tmp/file")
        self.assertEqual(str(events[0]), f"{events[0].date}\t12\tuser\tf\t/tmp/file")

    def test_reraises_invalid_timestamp(self):
        with self.assertRaises(ValueError):
            list(
                find_parser._parse_find_printf(
                    ["invalid\t12\tuser\tf\t/tmp/file\n"], output=None
                )
            )

    def test_file_wrapper_parses_records(self):
        record = "1\t4\tuser\td\t/tmp\n"
        with mock.patch("builtins.open", mock.mock_open(read_data=record)):
            events = list(
                find_parser.parse_find_printf("unused", "find.out")
            )

        self.assertEqual(events[0].url, "/tmp")
