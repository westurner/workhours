
import datetime
import decimal
import json
datetime_types = (datetime.time, datetime.date, datetime.datetime)

#from collections import namedtuple
#from sqlalchemy.util import NamedTuple as sqla_namedtuple
#named_tuple_types = (namedtuple, sqla_namedtuple, )

#import networkx as nx
#graph_types = (nx.Graph, nx.DiGraph, nx.MultiGraph, nx.MultiDiGraph)
#from networkx.readwrite.json_graph import node_link_data

class DefaultJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        """Convert ``obj`` to something JSON encoder can handle."""
        if hasattr(obj, '_asdict'):
            obj = obj._asdict()
        elif hasattr(obj, '_fields'): #isinstance(obj, named_tuple_types):
            obj = dict((k, getattr(obj, k)) for k in list(obj.keys()))
        elif isinstance(obj, decimal.Decimal):
            obj = str(obj)
        elif isinstance(obj, datetime_types):
            obj = str(obj)
        #elif isinstance(obj, graph_types):
        #    obj = node_link_data(obj)
        return obj

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
        kwargs['cls'] = json.JSONDecoder
        return f(*args, **kwargs)
    return wrapper

dump = json_wrap_output(json.dump)
dumps = json_wrap_output(json.dumps)
load = json_wrap_input(json.load)
loads = json_wrap_input(json.loads)

