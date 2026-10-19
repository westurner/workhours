#!/usr/bin/env python
"""
Grep Trac Timeline HTML
"""
import datetime
from bs4 import BeautifulSoup as BS


def parse_trac_date(date, time):
    """
    Parse a trac date into a mm/dd/yy datestring

    :param date: mm/dd/yy string
    :type date: str
    :param time: 24hr mm:dd string
    :type time: str

    :returns: datetime.datetime
    """

    fullstr = "{} {}".format(date, time)
    return datetime.datetime.strptime(fullstr, "%m/%d/%y %H:%M")


def parse_trac_timeline(timeline_file=None, users=None, uri=None):
    """
    Parse a trac timeline HTML file for timeline events

    :param timeline_file: Timeline to parse
    :type timeline_file: File-like object
    :param users: List of author names to include in the events list
    :type users: list(str)

    :returns: Generator of event tuples (datetime, url)
    """

    timeline_file = uri if uri is not None else timeline_file
    with open(timeline_file, encoding="UTF-8") as source:

        b = BS(source, "html.parser")
        days = [
            x
            for x in b.find_all("h2")
            if (x.text in ["Today", "Yesterday"] or ":" in x.text)
        ]
        for day in days:
            date = day.text.split(":")[0]
            for event in day.find_next("dl").find_all("dt"):
                authornode = event.find("span", class_="author")
                if authornode and (users is None or authornode.text in users):
                    time = event.find("span", class_="time").text
                    link = event.find("a").get("href")
                    yield (
                        parse_trac_date(date, time),
                        link,
                    )
