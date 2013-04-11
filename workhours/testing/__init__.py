import unittest
from pyramid import testing

import sqlalchemy

import logging
import transaction

log = logging.getLogger('workhours.testing')

class PyramidTestCase(unittest.TestCase):
    def setUp(self, request=None):
        self.config = testing.setUp(request=request)

        self.meta = _initialize_sql_test()
        self.session = self.meta.Session()

        self.request = self._new_request()
        self.config = testing.setUp(self.request)

    def tearDown(self):
        testing.tearDown()

    def _new_request(self, *args, **kwargs):
        request = testing.DummyRequest(*args, **kwargs)
        request.db_session = self.session
        return request


from fixture import SQLAlchemyFixture, NamedDataStyle

from workhours import models
from workhours.models.sql import _initialize_sql_test, create_tables, drop_tables, get_test_engine






import os
def initialize_db(*args, **kwargs):
    engine = get_test_engine()
    meta = _initialize_sql_test(engine=engine)
    dbfixture = SQLAlchemyFixture(
                    env=models,
                    style=NamedDataStyle(),
                    engine=engine )
    return meta, dbfixture

from workhours.models.fixtures import data

class PyramidFixtureTestCase(unittest.TestCase):
    fixtures = data.ALL_FIXTURES #tuple()

    def setUp(self, request=None):
        log.debug("fixture setUp")
        self.config = testing.setUp(request=request)
        self.meta, self.dbfixture = initialize_db(config=self.config)
        self.setUp_fixtures()
        self.session = self.meta.Session()
        self.request = self._new_request()
        #transaction.begin()

        #import ipdb
        #ipdb.set_trace()

    def setUp_fixtures(self):
        if not self.fixtures:
            raise Exception('no fixtures specified')
        log.debug('setup fixtures: %s', self.fixtures)
        self.data = self.dbfixture.data(*self.fixtures)
        self.data.setup()

    def tearDown_fixtures(self):
        if self.fixtures:
            self.data.teardown()

    def tearDown(self):
        try:
            transaction.commit()
        except Exception, e:
            transaction.abort()
            log.exception(e)
            pass
        self.tearDown_fixtures()
        testing.tearDown()

    def _new_request(self, *args, **kwargs):
        request = testing.DummyRequest(*args, **kwargs)
        request.db_session = self.session
        return request


class ExampleTestCase(PyramidTestCase): # unittest.TestCase
    def example_text_function(self):
        from pyramid.httpexceptions import HTTPForbidden
        from workhours.site.views import about

        response = about(self.request)
