from workhours.models.sql import engine
from workhours.models.sql import initialize_sql
from workhours.models import setup_mappers

def setup(*args, **kwargs):
    setup_mappers(engine)
    initialize_sql(engine)

