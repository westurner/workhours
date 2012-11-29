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

def initialize_sql(engine):
    log.debug("initialize_sql: %r" % engine)
    # uhm
    #global engine
    try:

        # and explicit mappings
        #global meta
        from workhours.models import setup_mappers
        meta = setup_mappers(engine)
        meta.bind = engine

        DBSession.configure(bind=engine)

        Base.metadata.bind = engine
        meta.Session = DBSession
        sessionmaker(bind=engine)

        # Create tables
        return initialize_sql_db(meta)
    except Exception, e:
        log.error(engine)
        log.error(DBSession)
        log.exception(e)
        raise
    #except sqlalchemy.exc.OperationalError:

def initialize_sql_db(meta):
    log.info("initialize_sql_db(%r)" % meta)
    engine = meta.bind
    # Create tables
    try:
        log.debug("meta.create_all()")
        meta.create_all()
    except Exception, e:
        log.error(engine)
        log.exception(e)
        raise

    try:
        log.debug("Base.metadata.create_all(%r)" % engine)
        Base.metadata.create_all(engine)
    except Exception, e:
        #sqlalchemy.exc.OperationalError, e:
        log.error(engine)
        log.exception(e)
        raise

    return meta

def _initialize_sql_test(url='sqlite:///test.db', self=None):
    from sqlalchemy import create_engine
    engine = create_engine(url)
    meta = initialize_sql(engine)
    #session = DBSession()
    #session.configure(bind=engine)
    #Base.metadata.bind = engine
    #Base.metadata.create_all(engine)
    return meta

