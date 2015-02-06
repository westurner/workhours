import unittest
from pyramid import testing

from workhours.testing import PyramidFixtureTestCase
from workhours.models.html.datatables import datatables_view

class Test_datatables(PyramidFixtureTestCase):
    #def setUp(self):
        #self.meta = _initialize_sql_test()
        #self.session = self.meta.Session
        #self.config = testing.setUp()

    def _get_test_request(self, *args, **kwargs):
        request = testing.DummyRequest(*args, **kwargs)
        request.db_session = self.session
        return request

    #def tearDown(self):
        #import transaction
        #transaction.abort()
        #testing.tearDown()


    def test_about_view(self):
        #from workhours.site.views.about import about_view
        request = self._get_test_request()
        datatables_view(request)

