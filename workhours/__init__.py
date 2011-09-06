from sqlalchemy import create_engine


class Namespace(object):
    pass


def setup_engine(dsn=None):
    dsn = 'sqlite:///%s' % dsn
    # create engine
    return create_engine(dsn)
