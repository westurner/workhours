#!/usr/bin/env python
"""
WebKit History
"""

from sqlalchemy import MetaData, Table, Column, Integer, ForeignKey
from sqlalchemy.orm import joinedload, registry, relationship

from workhours.webkit import longdate_to_datetime
from workhours.models import open_db

import logging

log = logging.getLogger("webkit.history")

from pytz import timezone

cst = timezone("US/Central")


class URL(object):
    """
    WebKit 'URL' in the ``urls`` table
    """

    def __repr__(self):
        return str(self)

    def __unicode__(self):
        return str(self.__dict__)


class Visit(object):
    """
    WebKit 'Visit' in the ``visits`` table
    """

    def _to_event_row(self):
        return (self._visit_date, self._url.url, self._url.title)

    @property
    def _visit_date(self):
        return longdate_to_datetime(self.visit_time)

    def __str__(self):
        return "%s, %s, %s" % (
            cst.localize(self._visit_date).ctime(),
            self._url.url,
            self.title,
        )


import warnings
from sqlalchemy import exc as sa_exc


def setup_mappers(meta=None, engine=None):
    """
    Setup SQLAlchemy mappings for the webkit urls.sqlite history file

    :params engine: SQLAlchemy engine
    :type engine: sqlalchemy engine

    :returns: SQLAlchemy meta
    """
    meta = meta or MetaData()
    mapper_registry = registry(metadata=meta)
    # reflect all tables into meta.tables[]

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=sa_exc.SAWarning)

        meta.reflect(bind=engine)

    # redefine url_id as a foreign key
    urls = meta.tables["urls"]
    visits = Table(
        "visits",
        meta,
        Column("url", Integer, ForeignKey("urls.id")),
        extend_existing=True,
    )

    mapper_registry.map_imperatively(URL, urls)
    mapper_registry.map_imperatively(
        Visit, visits, properties={"_url": relationship(URL)}
    )
    return meta


MAPPED_CLASSES = (URL, Visit)


def _Session(uri):
    meta = open_db(
        "sqlite:///%s" % uri,
        setup_mappers,
        destructive_recover=True,
        munge_mappers=MAPPED_CLASSES,
    )
    return meta.Session()


def parse_webkit_history(uri=None):
    """
    Parse a webkit urls.sqlite history file

    :param urls_filename: path to the urls.sqlite file
    :type urls_filename: str

    :returns: Generator of (datetime, url) tuples
    """
    log.info("Parse: %s" % uri)
    # s = _Session(uri)
    meta = open_db(
        "sqlite:///%s" % uri,
        setup_mappers=None,
        destructive_recover=True,  # TODO: pragma-journal[...]
        munge_mappers=MAPPED_CLASSES,
    )
    meta = setup_mappers(meta, meta.engine)
    s = meta.Session
    for v in s.query(Visit).options(joinedload(Visit._url)).order_by(Visit.id):
        yield {
            "date": v._visit_date,
            "url": v._url.url,
            "title": v._url.title,
            "source_record_id": v.id,
        }


if __name__ == "__main__":
    import sys

    path_ = sys.argv[1]
    print("# =========== Hist ", path_)
    for x in parse_webkit_history(path_):
        print(str(x[0]), "||", x[1], "||", x[2])
