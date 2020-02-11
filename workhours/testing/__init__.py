import unittest
from pyramid import testing

import workhours

import sqlalchemy

import logging
import transaction

log = logging.getLogger('workhours.testing')

test_settings = {

    'jinja2.directories': 'workhours:templates',

    'deform_jinja2.template_search_path':'deform_jinja2:bootstrap_templates',
    'deform_jinja2.i18n.domain':'deform',

    'sqlalchemy.url': 'sqlite:///test_db.sqlite.db',
    'sqlalchemy.echo': True,
    'sqlalchemy.echo_pool': True,

    'mail_sender': 'testing@wrd.nu',
    'mail.transport.use': 'logging',
    'mail.transport.log': 'CRITICAL', # log email bodies
    'mail.transport.debug.on': 'true',
    'db_main.url': 'sqlite:///test_events_db.sqlite.db',
    'db_main.echo': True,
    'db_main.echo_pool': True,

    'esdb.url': 'http://localhost:9200',
    'fs.url': 'tmpfs',
    'climain.ini': 'cli.ini',

    'sparql_url.http': 'http://localhost:8890/sparql',
    'rdflib.connstr': 'host=localhost,user=USER,password=PASSWORD,db=DBNAME',
    'rdflib.virtuoso_connstr': 'DSN=VOS;UID=dba;PWD=dba;WideAsUTF16=Y'
}

class PyramidTestCase(unittest.TestCase):
    def setUp(self, request=None):
        log.debug("TST PyramidTestCase.setUp %r" % self)

        self.meta = _initialize_sql_test()
        self.session = self.meta.Session()

        self.request = self._new_request()
        self.config = testing.setUp(request=self.request, settings=test_settings)
        workhours.configure_test_app(self.config, settings=test_settings)

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
    meta = _initialize_sql_test(engine=engine, Base=models.Base)
    dbfixture = SQLAlchemyFixture(
                    env=models,
                    style=NamedDataStyle(),
                    engine=engine )
    return meta, dbfixture

from workhours.models.fixtures import data

class PyramidFixtureTestCase(unittest.TestCase):
    fixtures = data.ALL_FIXTURES #tuple()

    def setUp(self, request=None):
        log.debug("TST PyramidFixtureTestCase.setUp %r" % self)
        self.config = testing.setUp(request=request, settings=test_settings)
        self.meta, self.dbfixture = initialize_db(config=self.config)
        self.session = self.meta.Session()
        self.setUp_fixtures()
        workhours.configure_test_app(self.config, settings=test_settings)
        self.request = self._new_request()

    def setUp_fixtures(self):
        if not self.fixtures:
            raise Exception('no fixtures specified')
        log.debug('setup fixtures: %s', [fx.__name__ for fx in self.fixtures])
        self.data = self.dbfixture.data(*self.fixtures)
        self.data.setup()

    def tearDown_fixtures(self):
        if self.fixtures:
            self.data.teardown()

    def tearDown(self):
        try:
            transaction.commit()
        except Exception as e:
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
