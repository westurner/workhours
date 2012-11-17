import unittest

from pyramid import testing

from workhours.models.sql import _initialize_sql_test
from workhours import _register_routes, _register_common_templates


class ViewTests(unittest.TestCase):
    def setUp(self):
        self.session = _initialize_sql_test()
        self.config = testing.setUp()

    def tearDown(self):
        import transaction
        transaction.abort()
        testing.tearDown()


    def test_about_view(self):
        from workhours.site.views.about import about_view
        _register_routes(self.config)
        _register_common_templates(self.config)
        request = testing.DummyRequest()
        about_view(request)

    def test_main_view(self):
        from workhours.site.views.main import main_view
        _register_routes(self.config)
        _register_common_templates(self.config)
        request = testing.DummyRequest()
        main_view(request)

    def test_http404_view(self):
        from workhours.site.views.errors import http404
        _register_routes(self.config)
        _register_common_templates(self.config)
        request = testing.DummyRequest()
        http404(request)

    def test_toolbar_view(self):
        from workhours.site.views.blocks import toolbar_view
        _register_routes(self.config)
        _register_common_templates(self.config)
        request = testing.DummyRequest()
        toolbar_view(request)

if __name__=="__main__":
    unittest.main()
