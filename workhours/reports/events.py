import datetime
from workhours.models import Event, Session


def dump_events_table(dburi, session=None):
    """
    Print Events Table to stdout

    :param dburi: SQLAlchemy database URI
    :type dburi: str
    """
    s = session or Session(dburi)
    for e in s.query(Event).order_by(Event.date):
        try:
            print e._to_txt_row()
        except UnicodeEncodeError, error:
            print type(error.object), error.encoding
            print error.object.encode('utf8','replace')
            raise

YEARLY=1
MONTHLY=2
DAILY=3
HOURLY=4
MINUTELY=5

from sqlalchemy.sql import func
def histogram(cls,
        resolution=YEARLY,
        date_range=None,
        date_attrname='date'):
    """
    Group by
    year
    month
    day
    hour
    """
    s = Session(dburi)
    count, mindate, maxdate = ( s.query(
            func.count('*'),
            func.min('date'),
            func.max('date'),
            ).first() )

    dateattr = date_attrname
    query = (s.query( func.count('*').label('row_count') ).order_by(dateattr))

    if date_range:
        start , end = date_range
        query = (query
                    .filter(dateattr >= start)
                    .filter(dateattr <= end))

    if resolution == YEARLY:
        bin_generator = yearly_bins(mindate.year, maxdate.year)

    for label, start, end in bin_generator:
        yield (label,
                (query
                    .filter(dateattr >= start)
                    .filter(dateattr <= end)
                    .first()))  # TODO:


def yearly_bins(start, end):
    onesec = datetime.timedelta(microseconds=-1)
    for year in xrange(start.year, end.year+1):
        d1 = datetime.datetime(year,1,1)
        d2 = datetime.datetime(year+1,1,1)-onesec
        yield (year, d1, d2)


def weekly_bins(start, end):
    pass
    # TODO: pandas DateRange?


def daily_bins(start, end):
    offset = datetime.timedelta(days=1,microseconds=-1)
    d1 = datetime.datetime(start.year, start.month, start.day)
    for n in xrange((end-start).days):
        d2 = d1 + offset
        yield (start, d1, d2)
        d1 = d2
    return


def hourly_bins(start, end):
    offset = datetime.timedelta(hours=1,microseconds=-1)
    for diff in xrange((end-start).hours):
        d1 = datetime.datetime(start.year, start.month, start.day, start.hour)
        d2 = d1 + offset
        yield (start, d1, d2)


def minutely_bins(start, end, minutes=15):
    offset = datetime.timedelta(minutes=minutes)
    for diff in xrange( ((end-start).days*60) / minutes):
        d1 = datetime.datetime(start.year, start.month, start.day, start.hour, start.minute)
        d2 = d1 + offset
        yield (start, d1, d2)

def groupby():
    from itertools import groupby

    def grouper( item ):
        return item.date.year, item.date.month
    for ( (year, month), items ) in groupby( query_result, grouper ):
        for item in items:
            yield item
