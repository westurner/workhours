
import logging
log = logging.getLogger('workhours.models.es')

import pyes
import pyes.es

from workhours.future import OrderedDict
from workhours.models import json
from workhours.models import ALL_MODELS

INDEXES = []
MAPPINGS = OrderedDict()

import sys

def initialize_esdb(url, *args, **kwargs):
    log.debug('initialize_esdb:(%r, %r , %r)' % (url, args, kwargs))
    return ESSession(url,
            encoder=json.DefaultJSONEncoder,
            #decoder=json.DefaultJSONDecoder,
            #dump_curl=sys.stdout) # TODO
            )

class ESSession(pyes.es.ES):
    indexes = []
    mappings = []
    def __init__(self, *args, **kwargs):
        super(ESSession, self).__init__(*args, **kwargs)

        self.indexes, self.mappings = self.get_indexes_from_models()
        self.setup_indexes()

    @classmethod
    def get_indexes_from_models(cls, models=ALL_MODELS):
        log.debug("get_indexes_from_models")

        # TODO: OrderedDict?
        indexes = []
        mappings = OrderedDict()
        for model in models:
            log.debug(repr(model))
            if hasattr(model, '_pyes_schema'):
                _index  = getattr(model, '_pyes_index',
                                    model.__class__.__name__) # TODO: naming prefix
                _type   = getattr(model, '_pyes_type',
                                    model.__class__.__name__)
                indexes.append(_index)
                mappings[_type] = model._pyes_schema
                #yield (
                #    model,
                #    model._pyes_schema,
                #    getattr(model, '_pyes_version'),
                #)
        return indexes, mappings

    def get_indexes(self):
        return self.index_stats()['_all']['indices'].keys()

    def refresh_indexes(self, indexes=INDEXES):
        return self.refresh(indexes)

    def setup_indexes(self, indexes=None, mappings=None, refresh=False):
        if indexes is None:
            indexes = self.indexes
        if mappings is None:
            mappings = self.mappings

        for index in indexes:
            import warnings
            warnings.warn(index)
            #TODO: self.create_index_if_missing(index)

        for key, mapping in mappings.iteritems():
            self.put_mapping(key, {'properties': mapping,}, indices=[])

        if refresh:
            self.refresh_indexes(indexes)


    def put(self, obj, index=None, type=None, version=None, **kwargs):

        if index is None:
            index = getattr(obj, '_pyes_index', obj.__class__.__name__)

        if type is None:
            type = getattr(obj, '_pyes_type', obj.__class__.__name__)

        if version is None:
            version = getattr(obj, '_pyes_version', 1)

        # TODO: ESJSONEncoder
        _obj = None
        if hasattr(obj, '_asdict'): # TODO: json?
            _obj = obj._asdict()
        elif hasattr(obj, '_fields'):
            _obj = {f:getattr(obj,f) for f in _fields}
        else:
            _obj = obj # TODO

        return self.index(_obj ,
                            index,
                            type,
                            #version=version,
                            **kwargs)


    def put_all(self, objects, index=None, type=None, version=None, **kwargs):

        if version is None:
            version = 1

        return self.index(objects,
                            index,
                            type,
                            bulk=True,
                            #version=version,
                            **kwargs)

   #def index(self,
                  #doc,
                  #index,
                  #doc_type,
                  #id=None,
                  #parent=None,
                  #force_insert=False,
                  #op_type=None,
                  #bulk=False,
                  #version=None,
                  #querystring_args=None):
      ## ... pyes.es.ES




import urllib
def setup_couchdb_river(conn, kwargs):
    """

    ::

        plugin -install river-couchdb

    http://code/docs/pyes/guide/reference/river/couchdb.html

    """
    db = kwargs.get('db')
    host = kwargs.get('host','localhost')
    port = kwargs.get('port', 5984)

    river = {
        "type": "couchdb",
        "couchdb": {
            "host": host,
            "port": port,
            "db": db,
        },
        "index": {
            "index": db,
            "type": db,
            "bulk_size": "100",
            "bulk_timeout": "10ms",
        },
    }

    conn.create_river(river, river_name=db)

    #req = Request(
    #     urllib.join(esdb_url, '_river/%s/_meta' % river_name))
    #resp = req.put(river)
    return resp # TODO
