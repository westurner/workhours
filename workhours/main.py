import csv
import datetime
from sqlalchemy import *
from sqlalchemy.orm import sessionmaker, mapper, relation, eagerload
from datetime import datetime, timedelta
from workhours import setup_engine

class Event(object):
    def __init__(self, source, datetime, url):
        self.source = source
        self.datetime = datetime
        self.url = url

    def _to_event_row(self):
        return (self.datetime, self.source, self.url)

def setup_mappers(engine):
    """
    Setup SQLAlchemy mappers for the aggregate events database

    :param engine: SQLAlchemy engine
    :type engine: SQLAlchemy engine

    :returns: SQLAlchemy meta
    """
    meta = MetaData()

    events_tbl = Table('events', meta,
        Column(u'id', Integer(), primary_key=True, nullable=False),
        Column(u'source', Unicode(length=255), index=True),
        Column(u'datetime', DateTime(), index=True),
        Column(u'url', UnicodeText()),
    )

    mapper(Event, events_tbl)

    return meta

# TODO: more elegant generalization
def populate_events_table(database_filepath, ffplaces_filepaths, timeline_filepath, trac_usernames, output_filename, gaptime):
    engine = setup_engine(database_filepath)
    meta = setup_mappers(engine)
    meta.bind = engine

    # Create tables
    meta.create_all()
    meta.Session = sessionmaker(bind=engine)

    s = meta.Session()

    from workhours.firefox import parse_firefox_history
    for ffpath in ffplaces_filepaths:
        for e in parse_firefox_history(ffpath):
            s.add(Event('firefox', *e))
        s.flush()

    from workhours.tractimeline import parse_trac_timeline
    for e in parse_trac_timeline(open(timeline_filepath,'rb'), trac_usernames):
        s.add(Event('trac', *e))
    s.flush()

    s.commit()

    create_gap_csv(meta, output_filename, gaptime)

def create_gap_csv(meta, output_filename, gaptime=15):
    """
    Generate a CSV with '----' lines where the gap between entries is
    greater than the specified gaptime

    :param meta: SQLAlchemy meta (with meta.Session)
    :type meta: SQLAlchemy meta
    :param output_filename: path to the CSV output file
    :type output_filename: str
    :param gaptime: Minimum gap size
    :type gaptime: int

    :returns: None
    """
    s = meta.Session()
    with open(output_filename,'w+') as f:
	cw = csv.writer(f)
	cw.writerow(('datetime','source','visit_date'))

        ltime = None
	for e in s.query(Event). \
            order_by(Event.datetime). \
            all():
	    ctime, source, url = cur_row = e._to_event_row()
	    if ltime and (ltime + timedelta(minutes=gaptime)) < ctime:
		cw.writerow(('--------','-------','------'))
	    cw.writerow(cur_row)
	    ltime = ctime

def main():
    from optparse import OptionParser
    import datetime
    datestr = datetime.datetime.now().strftime('%y-%m-%d-%H%M')

    prs = OptionParser()

    prs.add_option('-f','--ffdb',dest='ffdb',action='append',
	help='Location of the places.sqlite database to parse '
             '(may be specified more than once)')
    prs.add_option('-t','--tratimeline',dest='tractimeline',action='store',
        help='Location of the trac timeline html file')
    prs.add_option('-u','--username',dest='tracusernames',action='append',
        help='Trac usernames to include '
             '(may be specified more than once)')
    prs.add_option('-e','--eventsdb',dest='eventsdb',action='store',
        default='events-%s.sqlite' % datestr,
        help='Filepath for the aggregate events database')
    prs.add_option('-o','--output-csv',dest='output_csv',action='store',
	default='workhours-%s.csv' % datestr,
        help='File to write output csv into')
    prs.add_option('-g','--gaptime',dest='gaptime',action='store',
	default=15, help="Minute gap to detect between entries")


    (options, args) = prs.parse_args()

    if not options.ffdb:
	print "A places.sqlite file must be specified"
	exit()

    if not options.tractimeline:
        print "A trac timeline file must be specified"
        exit()

    populate_events_table(
        options.eventsdb,
        options.ffdb,
        options.tractimeline,
        options.tracusernames,
        options.output_csv,
        int(options.gaptime)
    )


if __name__=="__main__":
    main()