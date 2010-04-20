#!/usr/bin/env python

import csv
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker, mapper, relation
from datetime import datetime, timedelta
from pytz import timezone

cst = timezone('US/Central')

engine = None
meta = None
Session = None

class Air(object):
    pass

tables = Air()

def setup_engine(dsn=None):
    dsn = 'sqlite:///%s' % dsn
    # create engine
    engine = create_engine(dsn)

    meta = MetaData()

    global Session
    Session = sessionmaker(bind=engine)

    # reflect all tables into meta.tables[]
    meta.reflect(bind=engine)

    # redefine place_id as a foreign key
    tables.places = meta.tables['moz_places']
    tables.visits = Table('moz_historyvisits',meta,
	Column('place_id', Integer, ForeignKey('moz_places.id')),
	useexisting=True,
    )


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
    pass

class Visit(object):
    def _to_row(self):
	return (self._visit_date, self.place.url)
    
    @property
    def _visit_date(self):
	return _epoch_to_datetime(self.visit_date)

    def __str__(self):
	return '%s, %s' % (self._visit_date.ctime(), self.place.url)

def setup_mappers():
    mapper(Place, tables.places)
    mapper(Visit, tables.visits, properties={
	'place':relation(Place)
	}
    )


def do_it(output_filename,minutes=10):
    s = Session()

    ltime = None
    with open(output_filename,'w+') as f:
	cw = csv.writer(f)
	cw.writerow(('url','visit_date'))

	for v in s.query(Visit).all():
	    ctime,url = cur_row = v._to_row()
	    if ltime and (ltime + timedelta(minutes=minutes)) < ctime:
		cw.writerow(('--------','-------'))
	    cw.writerow(cur_row)
	    ltime = ctime

def main():
    from optparse import OptionParser

    prs = OptionParser()

    prs.add_option('-f','--ffdb',dest='ffdb',action='store',
	help='Location of the places.sqlite database to parse')
    prs.add_option('-o','--output-csv',dest='output_csv',action='store',
	default='workhours.csv', help='File to write output csv into')
    prs.add_option('-g','--timegap',dest='timegap',action='store',
	default=15, help="Minute gap to detect between entries")

    (options, args) = prs.parse_args()

    if not options.ffdb:
	print "A places.sqlite file must be specified"
	exit()

    setup_engine(options.ffdb)
    setup_mappers()
    do_it(options.output_csv, options.timegap)

if __name__=="__main__":
    main()
