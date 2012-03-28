#!/usr/bin/env python
"""
WebKit History
"""

from sqlalchemy import MetaData, Table, Column, Integer, ForeignKey
from sqlalchemy.orm import mapper, relationship, eagerload

from workhours.webkit import longdate_to_datetime
from workhours.models import open_db

import logging
log = logging.getLogger('webkit.history')

from pytz import timezone
cst = timezone('US/Central')

class URL(object):
    """
    WebKit 'URL' in the ``urls`` table
    """

    def __repr__(self):
        return unicode(self)

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
        return '%s, %s, %s' % (cst.localize(self._visit_date).ctime(), self._url.url, self.title)


def setup_mappers(engine):
    """
    Setup SQLAlchemy mappings for the webkit urls.sqlite history file

    :params engine: SQLAlchemy engine
    :type engine: sqlalchemy engine

    :returns: SQLAlchemy meta
    """
    meta = MetaData()
    # reflect all tables into meta.tables[]
    meta.reflect(bind=engine)

    # redefine url_id as a foreign key
    urls = meta.tables['urls']
    visits = Table('visits',meta,
        Column('url', Integer, ForeignKey('urls.id')),
        useexisting=True,
    )

    mapper(URL, urls)
    mapper(Visit, visits, properties={
        '_url':relationship(URL)
        }
    )
    return meta


MAPPED_CLASSES = ['Mapper|URL|urls', 'Mapper|Visit|visits']
def _Session(uri):
    meta = open_db('sqlite:///%s' % uri,
                    setup_mappers,
                    destructive_recover=True,
                    munge_mappers=MAPPED_CLASSES)
    return meta.Session()

def parse_webkit_history(uri=None):
    """
    Parse a webkit urls.sqlite history file

    :param urls_filename: path to the urls.sqlite file
    :type urls_filename: str

    :returns: Generator of (datetime, url) tuples
    """
    log.info("Parse: %s" % uri)
    s = _Session(uri)
    for v in (s.query(Visit).
                options(
                    eagerload(Visit._url))):
        yield v._to_event_row()


if __name__=="__main__":
    import sys
    path_=sys.argv[1]
    print '# =========== Hist ', path_
    for x in parse_webkit_history(path_):
        print str(x[0]),'||', x[1], '||', x[2]

