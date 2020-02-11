import unittest

from pyramid import testing
from workhours.testing import PyramidTestCase


class ViewTests(PyramidTestCase):
    def test_about_view(self):
        from workhours.site.views.about import about_view

        about_view(self.request)

    def test_main_view(self):
        from workhours.site.views.main import main_view

        main_view(self.request)

    def test_http404_view(self):
        from workhours.site.views.errors import http404

        http404(self.request)

    def test_toolbar_view(self):
        from workhours.site.views.blocks import toolbar_view

        toolbar_view(self.request)


if __name__ == "__main__":
    unittest.main()
