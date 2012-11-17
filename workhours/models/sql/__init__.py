from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from zope.sqlalchemy import ZopeTransactionExtension

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()


engine = None
meta = None

def initialize_sql(_engine):
    # uhm
    global engine
    engine = _engine
    DBSession.configure(bind=engine)

    # setup both declarative base...
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)

    # and explicit mappings
    global meta
    from workhours.models import setup_mappers
    meta = setup_mappers(engine)
    meta.bind = engine

    # Create tables
    meta.create_all()
    meta.Session = DBSession
    #sessionmaker(bind=engine)


def _initialize_sql_test(self=None):
    from sqlalchemy import create_engine
    engine = create_engine('sqlite://')
    session = DBSession()
    session.configure(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)
    return session

