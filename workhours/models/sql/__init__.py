import sqlalchemy.exc
from sqlalchemy import create_engine
from sqlalchemy import MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from zope.sqlalchemy import ZopeTransactionExtension

from workhours.models.sqla_utils import clear_mappers as _clear_mappers

from sqlalchemy.orm import clear_mappers, configure_mappers

import logging
log = logging.getLogger('workhours.models.sql')

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()

#engine = None
#meta = None

def open_db(dburi,
            setup_mappers,
            destructive_recover=False,
            munge_mappers=[],
            create_tables_on_init=False):
    """
    Open a single session
    """
    try:
        engine = create_engine(dburi)
        meta = initialize_sql(engine, setup_mappers)
        meta.bind = engine
    except Exception:
        if dburi.startswith('sqlite') and destructive_recover:
            from workhours.models.sqlite_utils import commit_uncommitted_transactions
            commit_uncommitted_transactions(dburi)
            engine = create_engine(dburi)
        else:
            raise

    if munge_mappers:
        _clear_mappers(munge_mappers)

    if create_tables_on_init:
        create_tables(meta)
    #meta = setup_mappers(engine)
    #meta.Session = sessionmaker(bind=engine)
    return meta


def Session(uri):
    from workhours.models.sql.tables import setup_mappers
    meta = open_db(uri,
                    setup_mappers,
                    destructive_recover=False)
    return meta.Session()


def initialize_sql(engine, setup_mappers, create_tables_on_init=False):
    log.debug("initialize_sql: %r" % engine)
    # uhm
    try:

        # and explicit mappings
        from workhours.models.sql.tables import setup_mappers

        meta = MetaData()
        meta.bind = engine

        meta = setup_mappers(meta=meta, engine=engine)
        if create_tables_on_init:
            meta = create_tables(meta)

        Base.metadata = meta #.bind = engine
        meta.Session = scoped_session(
                        sessionmaker(
                            extension=ZopeTransactionExtension(),
                            bind=engine))
        #meta.Session.configure(bind=engine)
        #sessionmaker(bind=engine)

        assert meta is not None
        return meta
    except Exception, e:
        log.error(engine)
        log.error(DBSession)
        log.exception(e)
        raise
    #except sqlalchemy.exc.OperationalError:

def create_tables(meta):
    # Create tables
    try:
        log.debug("meta.create_all()")
        meta.create_all()
    except Exception, e:
        log.error(meta)
        log.exception(e)
        raise
    return meta

    #for SQLALchemy Declarative Base
    #engine = meta.bind
    #try:
    #    log.debug("Base.metadata.create_all(%r)" % engine)
    #    Base.metadata.create_all(engine)
    #except Exception, e:
    #    #sqlalchemy.exc.OperationalError, e:
    #    log.error(engine)
    #    log.exception(e)
    #    raise
    # return meta

def drop_tables(meta):
    try:
        log.info('DROP all (%r)' % meta) # FIXME:
        meta.drop_all()
    except Exception, e:
        log.error(meta)
        log.exception(e)
        raise
    return meta

from pyramid.paster import get_appsettings
import os
def get_test_engine():
    conf = get_appsettings(os.environ.get('_CFG')+"#workhours_test")
    engine = sqlalchemy.engine_from_config(conf, 'db_main.')
    return engine

def _initialize_sql_test(engine=None, url=None):
    if engine is None:
        if url is None:
            engine = get_test_engine()
        else:
            engine = create_engine(url)

    meta = initialize_sql(engine, create_tables_on_init=False)
    drop_tables(meta)
    clear_mappers()
    import workhours.models
    workhours.models.sql.tables._MAPPED = False
    meta = initialize_sql(engine, create_tables_on_init=True)
    #session = DBSession()
    #session.configure(bind=engine)
    #Base.metadata.bind = engine
    #Base.metadata.create_all(engine)
    return meta


