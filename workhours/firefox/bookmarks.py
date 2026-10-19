#!/usr/bin/python


def main():
    from bs4 import BeautifulSoup
    from urllib.parse import unquote_plus

    with open("bookmarks.html", encoding="utf-8") as bookmarks_file:
        bookmarks = BeautifulSoup(bookmarks_file.read(), "html.parser")

    for link in bookmarks.find_all("a"):
        title = link.get_text()
        if title.startswith('"'):
            print(
                "== {} ==\n{}\n".format(
                    unquote_plus(title),
                    unquote_plus(link.get("href", "")),
                )
            )


if __name__ == "__main__":
    main()
