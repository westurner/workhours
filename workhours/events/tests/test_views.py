import unittest
from pyramid import testing
from workhours.models.sql import _initialize_sql_test
from workhours import configure_test_app

from workhours.models.html import datatables
from workhours.events.views import EventsRESTfulView

class Test_datatables(unittest.TestCase):
    def setUp(self):
        self.meta = _initialize_sql_test()
        self.session = self.meta.Session
        self.config = testing.setUp()

    def _get_test_request(self, *args, **kwargs):
        request = testing.DummyRequest(*args, **kwargs)
        request.db_session = self.session
        # TODO/FIXME: Custom workhours.Request attributes
        return request

    def tearDown(self):
        import transaction
        transaction.abort()
        testing.tearDown()


    def test_about_view(self):
        #from workhours.site.views.about import about_view
        configure_test_app(self.config)
        request = self._get_test_request()
        datatables.datatables_view(request)


