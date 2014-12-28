from workhours import models
from workhours.models.fixtures import data
from workhours.testing import PyramidFixtureTestCase
import unittest

import logging
log = logging.getLogger('workhours.models.fixtures.tests')

class TestFixtureLoad(PyramidFixtureTestCase):
    fixtures = data.ALL_FIXTURES
    def test_fixtures(self):
        s = self.meta.Session()
        for cls in models.ALL_MODELS:
            result = s.query(cls).count()
            self.assertGreaterEqual(result, 1, msg=cls)


    def test_fixtures2(self):
        s = self.meta.Session()
        for fixture, model in zip(data.ALL_FIXTURES, models.ALL_MODELS):
            for key, row in fixture.__dict__.iteritems():
                if key.startswith('_'):
                    continue
                try:
                    result = s.query(model).filter(model.id==row.id).one()
                except Exception as e:
                    log.error( (fixture, model, key, row) )
                    raise
                self.assertIsNotNone(result)
                self.assertEqual(result.id, row.id)

