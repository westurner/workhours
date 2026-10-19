"""Parse timestamped records from a Netscape-format bookmarks HTML file."""

from datetime import datetime, timezone

from bs4 import BeautifulSoup


def parse_bookmarks_html(uri=None, **kwargs):
    """Yield dated bookmark mappings; bookmarks without ADD_DATE are omitted."""
    with open(uri, encoding="utf-8", errors="replace") as source:
        bookmarks = BeautifulSoup(source, "html.parser")

    for link in bookmarks.find_all("a"):
        added = link.get("add_date") or link.get("date_added")
        if added is None:
            continue
        try:
            start_date = datetime.fromtimestamp(float(added), timezone.utc)
        except (TypeError, ValueError, OverflowError, OSError):
            continue

        tags = link.get("tags", "")
        comment_node = link.find_next_sibling("dd")
        yield {
            "date": start_date,
            "url": link.get("href"),
            "title": link.get_text(" ", strip=True),
            "tags": [tag for tag in tags.split(",") if tag],
            "private": link.get("private", "0") in ("1", "true", "True"),
            "comment": (
                comment_node.decode_contents().strip()
                if comment_node is not None
                else None
            ),
        }
