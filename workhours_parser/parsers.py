"""Lazy registry that exposes every workhours queue as SourceRecord rows."""

from importlib import import_module

from .compat import normalize_records


PARSER_MODULES = {
    "firefox.bookmarks": ("workhours.firefox.history", "parse_firefox_bookmarks"),
    "firefox.history": ("workhours.firefox.history", "parse_firefox_history"),
    "webkit.bookmarks": ("workhours.webkit.bookmarks", "parse_webkit_bookmarks"),
    "webkit.history": ("workhours.webkit.history", "parse_webkit_history"),
    "delicious.bookmarks": ("workhours.delicious.bookmarks", "parse_delicious_bookmarks"),
    "trac.timelines": ("workhours.trac.timeline", "parse_trac_timeline"),
    "log.shell": ("workhours.syslog.sessionlog", "parse_sessionlog"),
    "find": ("workhours.syslog.find", "parse_find_printf"),
    "log.wtmp": ("workhours.syslog.wtmp", "parse_wtmp_glob"),
    "log.auth": ("workhours.syslog.authlog", "parse_authlog_glob"),
    "bookmarks.json": ("workhours.bookmarks.json", "parse_bookmarks_json"),
    "bookmarks.html": ("workhours.bookmarks.html", "parse_bookmarks_html"),
}


def iter_records(source_type, source, options=None):
    """Yield validated SourceRecord objects for a registered source.

    Record keys use a source database row ID when available; otherwise they
    combine the source type, a hash of the input path, and parser position.
    """
    try:
        module_name, function_name = PARSER_MODULES[source_type]
    except KeyError as error:
        raise ValueError("unsupported workhours source: {}".format(source_type)) from error

    parser = getattr(import_module(module_name), function_name)
    records = parser(uri=source, **(options or {}))
    yield from normalize_records(source_type, records, source_identity=source)