from workhours import models
from workhours.models.fixtures import data
from workhours.testing import PyramidFixtureTestCase
import unittest

class TestFixtureLoad(PyramidFixtureTestCase):
    fixtures = data.ALL_FIXTURES
    def test_fixtures(self):
        s = self.meta.Session()
        for cls in models.ALL_MODELS:
            result = s.query(cls).count()
            self.assertGreaterEqual(result, 1, msg=cls)

