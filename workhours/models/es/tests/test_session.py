test_es_url = "http://localhost:9200/"

import logging
from unittest.mock import patch

log = logging.getLogger("workhours.models.es.tests.TestESSession")

import workhours.models.json as json

dumps = lambda obj: json.dumps(obj, indent=2)

import unittest
import workhours.models.es
from workhours.models.es import ESSession


class TestESSession(unittest.TestCase):
    def test_es_session(self):

        log.debug("ESSession: %s" % test_es_url)
        s = ESSession(test_es_url)
        log.debug("get_indexes: %s" % s.get_indexes())  # TODO
        index = "test-index"
        obj_type = "test-type"
        obj = {"test": True, "one": "two"}
        result = {"ok": True, "_type": obj_type, "_id": "test-id", "_index": index}
        with patch.object(s, "index", return_value=result) as index_request:
            response = s.put(obj, index=index, type=obj_type)
        log.debug("result: %r" % result)

        index_request.assert_called_once_with(obj, index, obj_type)
        self.assertTrue(response["ok"])
        self.assertEqual(response["_type"], obj_type)
        self.assertTrue(response.get("_id"))
        self.assertEqual(response["_index"], index)

    def test_es_initialize_db(self):
        from workhours.models.es import initialize_esdb

        s = initialize_esdb(test_es_url)
        self.assertTrue(isinstance(s, ESSession))
