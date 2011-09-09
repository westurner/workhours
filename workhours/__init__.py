__ALL__=[
    'log',
    'setup_engine',
    ]

from sqlalchemy import create_engine

import logging
log = logging.getLogger()

class Namespace(object):
    pass


def setup_engine(dsn=None):
    dsn = 'sqlite:///%s' % dsn
    log.debug("Creating engine: %s" % dsn)
    # create engine
    return create_engine(dsn)
