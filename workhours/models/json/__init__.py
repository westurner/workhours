
import json
import datetime
datetime_types = (datetime.time, datetime.date, datetime.datetime)
import decimal
from sqlalchemy.util import NamedTuple as sqla_namedtuple
try:
    from collections import namedtuple
    tuple_types = (namedtuple, sqla_namedtuple)
except ImportError:
    tuple_types = (sqla_namedtuple)

#import networkx as nx
#graph_types = (nx.Graph, nx.DiGraph, nx.MultiGraph, nx.MultiDiGraph)
#from networkx.readwrite.json_graph import node_link_data

def default_json_encoder(self, obj):
    """Convert ``obj`` to something JSON encoder can handle."""
    if isinstance(obj, tuple_types):
        obj = dict((k, getattr(obj, k)) for k in obj.keys())
    elif isinstance(obj, decimal.Decimal):
        obj = str(obj)
    elif isinstance(obj, datetime_types):
        obj = str(obj)
    #elif isinstance(obj, graph_types):
    #    obj = node_link_data(obj)
    return obj


class DefaultJSONEncoder(json.JSONEncoder):
    default = default_json_encoder


from functools import wraps
def json_wrap_output(f):
    # if config.DEBUG: indent, prettyprint
    # else
    jsonkwargs = dict(
            cls=DefaultJSONEncoder,
            ensure_ascii=False,
            separators=(',',':'),
            encoding='utf-8',)
    @wraps(f)
    def wrapper(*args, **kwargs):
        kwargs.update(jsonkwargs)
        return f(*args, **kwargs)
    return wrapper

def json_wrap_input(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        kwargs['cls'] = DefaultJSONEncoder
        return f(*args, **kwargs)
    return wrapper

dump = json_wrap_output(json.dump)
dumps = json_wrap_output(json.dumps)
load = json_wrap_input(json.load)
loads = json_wrap_input(json.loads)

