"""Parse dated bookmark JSON records and Chrome's nested bookmark format."""

from datetime import datetime, timedelta, timezone
import json


_CHROME_EPOCH = datetime(1601, 1, 1, tzinfo=timezone.utc)


def _date_for(item):
    value = item.get("startDate", item.get("date"))
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value, timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None

    chrome_added = item.get("date_added")
    if chrome_added is None:
        return None
    try:
        return _CHROME_EPOCH + timedelta(microseconds=int(chrome_added))
    except (OverflowError, TypeError, ValueError):
        return None


def _walk_chrome_nodes(nodes, path=()):
    for node in nodes:
        if node.get("type") == "folder":
            folder_path = path + (node.get("name", ""),)
            yield from _walk_chrome_nodes(node.get("children", ()), folder_path)
        elif node.get("url"):
            yield node, "/".join(part for part in path if part)


def _items(document):
    if isinstance(document, list):
        yield from ((item, item.get("path", "")) for item in document)
    elif isinstance(document, dict) and isinstance(document.get("roots"), dict):
        roots = document["roots"]
        for root_name in sorted(roots):
            root = roots[root_name]
            yield from _walk_chrome_nodes(
                root.get("children", ()), (root.get("name", root_name),)
            )
    elif isinstance(document, dict):
        items = document.get("bookmarks", document.get("records"))
        if isinstance(items, list):
            yield from ((item, item.get("path", "")) for item in items)
        else:
            yield from _walk_chrome_nodes(document.get("children", ()))


def parse_bookmarks_json(uri=None, **kwargs):
    """Yield timestamped bookmark mappings; records without dates are omitted."""
    with open(uri, encoding="utf-8") as source:
        document = json.load(source)

    for item, path in _items(document):
        start_date = _date_for(item)
        if start_date is None:
            continue
        yield {
            "date": start_date,
            "url": item.get("url"),
            "title": item.get("name", item.get("title")),
            "path": item.get("path", path),
            "tags": item.get("tags", []),
            "private": item.get("private", False),
            "comment": item.get("comment"),
        }
