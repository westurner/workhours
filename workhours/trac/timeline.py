#!/usr/bin/env python
"""
Grep Trac Timeline HTML
"""
import codecs
import datetime
from BeautifulSoup import BeautifulSoup as BS


def parse_trac_date(date, time):
    """
    Parse a trac date into a mm/dd/yy datestring

    :param date: mm/dd/yy string
    :type date: str
    :param time: 24hr mm:dd string
    :type time: str

    :returns: datetime.datetime
    """

    fullstr = "%s %s" % (date, time)
    return datetime.datetime.strptime(fullstr, "%m/%d/%y %H:%M")


def parse_trac_timeline(timeline_file, users):
    """
    Parse a trac timeline HTML file for timeline events

    :param timeline_file: Timeline to parse
    :type timeline_file: File-like object
    :param users: List of author names to include in the events list
    :type users: list(str)

    :returns: Generator of event tuples (datetime, url)
    """

    with codecs.open(path, "rb", encoding="UTF-8") as timeline_file:

        b = BS(timeline_file)
        days = [
            x
            for x in b.findAll("h2")
            if (x.text in ["Today", "Yesterday"] or ":" in x.text)
        ]
        for day in days:
            date = day.text.split(":")[0]
            for event in day.findNext("dl").findAll("dt"):
                authornode = event.findChild("span", {"class": "author"})
                if authornode and authornode.text in users:
                    time = event.findChild("span", {"class": "time"}).text
                    link = event.findChild("a").get("href")
                    yield (
                        parse_trac_date(date, time),
                        link,
                    )
