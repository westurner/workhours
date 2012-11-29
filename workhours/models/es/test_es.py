
test_es_url = 'http://localhost:9200'

import logging
log = logging.getLogger('workhours.models.es.tests.TestESSession')

import workhours.models.json as json

dumps = lambda obj: json.dumps(obj, indent=2)

import unittest
import workhours.models.es
from workhours.models.es import ESSession

class TestESSession(unittest.TestCase):
    def test_es_session(self):

        log.debug("ESSession: %s" % test_es_url)
        s = ESSession(test_es_url)
        log.debug("get_indexes: %s" % s.get_indexes()) # TODO
        index = 'test-index'
        obj_type = 'test-type'
        obj = {'test': True, 'one': 'two'}
        result = s.put(obj, index=index, type=obj_type)
        log.debug('result: %r' % result)

        self.assertTrue(result['ok'])
        self.assertEqual(result['_type'], obj_type)
        self.assertEqual(result['_id'], u'1')
        self.assertEqual(result['_index'], index)

    def test_es_initialize_db(self):
        from workhours.models.es import initialize_esdb
        s = initialize_esdb(test_es_url)
        self.assertTrue(isinstance(s, ESSession))
