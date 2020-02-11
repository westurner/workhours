#!/usr/bin/env python

from datetime import datetime
from sqlalchemy import MetaData, Table, Column, Integer, ForeignKey
from sqlalchemy.orm import mapper, relationship, eagerload
from pytz import timezone
from workhours.models.sql import open_db

import logging

log = logging.getLogger("firefox.history")

cst = timezone("US/Central")

# decode dates
def _epoch_to_datetime(time):
    """
    Convert a firefox datetime to a datetime.datetime

    :param time: seconds since the epoch
    :type time: long

    :returns: datetime.datetime
    """
    return datetime.fromtimestamp(time / 1000000.0)


def _datetime_to_epoch(dt):
    """
    Convert a datetime.datetime to a firefox datetime

    :param dt: datetime
    :type dt: datetime.datetime

    :returns: long
    """
    return long(dt.strftime("%s")) * 1000000.0


class Bookmark(object):
    """
    Firefox 'Bookmark' in the ``moz_places`` table
    """

    def to_event_row(self):
        return (
            self._date_added,
            self.place is not None and self.place.url or None,
            self.title,
        )

    @property
    def _date_added(self):
        return _epoch_to_datetime(self.dateAdded)

    def __str__(self):
        return u"%s||%s||%s" % (self.to_event_row())
        return u"||".join(
            unicode(x).decode("utf-8", errors="xmlcharref")
            for x in self.to_event_row()
        )


class Place(object):
    """
    Firefox 'Place' in the ``moz_places`` table
    """

    def __repr__(self):
        return unicode(self)

    def __unicode__(self):
        return str(self.__dict__)


class Visit(object):
    """
    Firefox 'Visit' in the ``moz_historyvisits`` table
    """

    def to_event_row(self):
        return (self._visit_date, self.place.url, self.place.title)

    @property
    def _visit_date(self):
        return _epoch_to_datetime(self.visit_date)

    @property
    def title(self):
        return self.place.title.encode("utf8", "replace")

    @property
    def url(self):
        return self.place.url

    def __str__(self):
        return u"%s || %s || %s" % (
            self._visit_date.ctime(),
            self.place.url,
            self.place.title,
        )


import warnings
from sqlalchemy import exc as sa_exc


def setup_mappers(meta=None, engine=None):
    """
    Setup SQLAlchemy mappings for the firefox places.sqlite history file

    :params engine: SQLAlchemy engine
    :type engine: sqlalchemy engine

    :returns: SQLAlchemy meta
    """
    meta = meta or MetaData()
    # if meta.is_bound:
    #    return meta

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=sa_exc.SAWarning)

        meta.reflect(bind=engine)

    # redefine place_id as a foreign key
    places = meta.tables["moz_places"]
    visits = Table(
        "moz_historyvisits",
        meta,
        Column("place_id", Integer, ForeignKey("moz_places.id")),
        useexisting=True,
    )
    bookmarks = Table(
        "moz_bookmarks",
        meta,
        Column("fk", Integer, ForeignKey("moz_places.id")),
        useexisting=True,
    )

    mapper(Place, places)
    mapper(Visit, visits, properties={"place": relationship(Place)})
    mapper(
        Bookmark,
        bookmarks,
        properties={
            "place": relationship(
                Place, primaryjoin=(bookmarks.c.fk == places.c.id)
            ),
        },
    )
    return meta


MAPPED_CLASSES = [
    "Mapper|Place|moz_places",
    "Mapper|Visit|moz_historyvisits",
    "Mapper|Bookmark|moz_bookmarks",
]


def _Session(uri):
    meta = open_db(
        "sqlite:///%s" % uri,
        setup_mappers,
        destructive_recover=False,  # TODO: pragma-journal[...]
        munge_mappers=MAPPED_CLASSES,
    )
    meta = setup_mappers(meta, meta.bind)
    return meta
    # .Session()


def parse_firefox_history(uri=None):
    """
    Parse a firefox places.sqlite history file

    :param places_filename: path to the places.sqlite file
    :type places_filename: str

    :returns: Generator of (datetime, url) tuples
    """
    log.info("Parse: %s" % uri)
    meta = open_db(
        "sqlite:///%s" % uri,
        setup_mappers=None,
        destructive_recover=True,  # TODO: pragma-journal[...]
        munge_mappers=MAPPED_CLASSES,
    )
    meta = setup_mappers(meta, meta.bind)
    s = meta.Session
    for v in s.query(Visit).options(eagerload(Visit.place)):
        yield v


def parse_firefox_bookmarks(uri=None):
    """
    Parse a firefox places.sqlite history file

    :param places_filename: path to the places.sqlite file
    :type places_filename: str

    :returns: Generator of (datetime, url, title) tuples
    """
    log.info("Parse: %s" % uri)
    meta = open_db(
        "sqlite:///%s" % uri,
        setup_mappers=None,
        destructive_recover=True,  # TODO: pragma-journal[...]
        munge_mappers=MAPPED_CLASSES,
    )
    meta = setup_mappers(meta, meta.bind)
    s = meta.Session

    for v in s.query(Bookmark).options(eagerload(Bookmark.place)):
        yield v


if __name__ == "__main__":
    import sys

    print "# =========== Hist "
    for x in parse_firefox_history(sys.argv[1]):
        print x

    print "# =========== Bookmarks "
    for x in parse_firefox_bookmarks(sys.argv[1]):
        print x
