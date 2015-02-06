import unittest
from pyramid import testing

from workhours.models.html import datatables
from workhours.events.views import EventsRESTfulView

from workhours.testing import PyramidFixtureTestCase

class Test_datatables(PyramidFixtureTestCase):
    def test_about_view(self):
        datatables.datatables_view(self.request)


