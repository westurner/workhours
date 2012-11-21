import sqlalchemy.exc
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from zope.sqlalchemy import ZopeTransactionExtension

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()

import logging
log = logging.getLogger('workhours.models.sql')

#engine = None
#meta = None

def initialize_sql(_engine):
    log.debug(_engine)
    # uhm
    #global engine
    engine = _engine
    DBSession.configure(bind=engine)

    # setup both declarative base...
    Base.metadata.bind = engine

    #try:
    #    Base.metadata.create_all(engine)
    #except sqlalchemy.exc.OperationalError, e:
    #    log.error(engine)
    #    log.exception(e)
    #    raise

    # and explicit mappings
    #global meta
    from workhours.models import setup_mappers
    meta = setup_mappers(engine)
    meta.bind = engine

    # Create tables
    meta.create_all()
    meta.Session = DBSession
    sessionmaker(bind=engine)

    return meta


def _initialize_sql_test(url='sqlite:///:memory:', self=None):
    from sqlalchemy import create_engine
    engine = create_engine(url)
    session = DBSession()
    session.configure(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)
    return session

