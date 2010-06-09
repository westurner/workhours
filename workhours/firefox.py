#!/usr/bin/env python

import csv
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker, mapper, relation, eagerload
from datetime import datetime, timedelta
from pytz import timezone
from workhours import setup_engine

cst = timezone('US/Central')

# decode dates
def _epoch_to_datetime(time):
    """
    Convert a firefox datetime to a datetime.datetime

    :param time: seconds since the epoch
    :type time: long

    :returns: datetime.datetime
    """
    return cst.localize(datetime.fromtimestamp(time/1000000.0))

def _datetime_to_epoch(dt):
    """
    Convert a datetime.datetime to a firefox datetime

    :param dt: datetime
    :type dt: datetime.datetime

    :returns: long
    """
    return long(dt.strftime('%s'))*1000000.0

class Place(object):
    """
    Firefox 'Place' in the ``moz_places`` table
    """
    pass

class Visit(object):
    """
    Firefox 'Visit' in the ``moz_historyvisits`` table
    """
    def _to_event_row(self):
	return (self._visit_date, self.place.url)

    @property
    def _visit_date(self):
	return _epoch_to_datetime(self.visit_date)

    def __str__(self):
	return '%s, %s' % (self._visit_date.ctime(), self.place.url)

def setup_mappers(engine):
    """
    Setup SQLAlchemy mappings for the firefox places.sqlite history file

    :params engine: SQLAlchemy engine
    :type engine: sqlalchemy engine

    :returns: SQLAlchemy meta
    """
    meta = MetaData()
    # reflect all tables into meta.tables[]
    meta.reflect(bind=engine)

    # redefine place_id as a foreign key
    places = meta.tables['moz_places']
    visits = Table('moz_historyvisits',meta,
	Column('place_id', Integer, ForeignKey('moz_places.id')),
	useexisting=True,
    )

    mapper(Place, places)
    mapper(Visit, visits, properties={
	'place':relation(Place)
	}
    )
    return meta

FF_MAPPED_CLASSES = ['Mapper|Place|moz_places', 'Mapper|Visit|moz_historyvisits']
def clear_ff_mappers():
    """
    Remove any existing Firefox mappings
    """
    from sqlalchemy import orm
    orm.mapperlib._COMPILE_MUTEX.acquire()
    try:
        for mapper in list(orm._mapper_registry):
            if str(mapper) in FF_MAPPED_CLASSES:
                mapper.dispose()
    finally:
        orm.mapperlib._COMPILE_MUTEX.release()



def parse_firefox_history(places_filename):
    """
    Parse a firefox places.sqlite history file

    :param places_filename: path to the places.sqlite file
    :type places_filename: str

    :returns: Generator of (datetime, url) tuples
    """
    engine = setup_engine(places_filename)

    clear_ff_mappers()
    setup_mappers(engine)
    Session = sessionmaker(bind=engine)
    s = Session()

    for v in s.query(Visit). \
        options(eagerload(Visit.place)). \
        all():
        yield v._to_event_row()

if __name__=="__main__":
    import sys
    for x in parse_firefox_history(sys.argv[1]):
        print ', '.join(map(str, x))