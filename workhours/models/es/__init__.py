
import logging
log = logging.getLogger('workhours.models.es')

import pyes
import pyes.es

import workhours.models
from collections import OrderedDict

INDEXES = []
MAPPINGS = OrderedDict()

def initialize_esdb(url, *args, **kwargs):
   log.debug('initialize_esdb:(%r, %r , %r)' % (url, args, kwargs))
   return ESSession(url)

class ESSession(pyes.es.ES):
   def get_indexes(conn):
      return conn.index_stats()['_all']['indices'].keys()

   def refresh_indexes(conn, indexes=INDEXES):
      return conn.refresh(indexes)

   def setup_indexes(conn, indexes=INDEXES, mappings=MAPPINGS):
      for index in indexes:
         conn.create_index_if_missing(index)

      for key, mapping in mappings.iteritems():
         conn.put_mapping(key, {'properties': mappping,}, indexes=[])

      refresh_indexes(conn, indexes)

   def put(conn, obj, index='test-index', type='test-type'):
      return conn.index(obj , index, type, 1)

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

def _get_indexes_from_models(models=workhours.models):
   log.debug("get_indexes_from_models")
   indexes = []
   mappings = []
   for model in models:
      log.debug(repr(model))
      if isinstance(models._Base):
         if hasattr(model, '_pyes_schema'):
            modelname = model.__class__.__name__ # TODO
            indexes.append(name)
            mappings.append( {'properties': model._pyes_schema} )
            yield (
               model,
               model._pyes_schema,
               getattr(model, '_pyes_version'),
            )


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
