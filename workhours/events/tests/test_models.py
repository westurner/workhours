# -*- coding: utf-8 -*-


import unittest
from pyramid import testing

#from .. import _register_routes
#from .. import _register_common_templates

from workhours.events.models import EventsContextFactory
from pyramid_restler.model import SQLAlchemyORMContext
#from ..numbers.views import NumberGraphRESTfulView

import workhours.models
from workhours.models.sql import _initialize_sql_test
def patch_tests(**kwargs):
    testing.DummyRequest.db_session = workhours.models.DBSession
    for (k,v) in kwargs.iteritems():
        setattr(testing.DummyRequest, k, v)


import transaction

#IContextFactory
class EventsContextTests(unittest.TestCase):
    def setUp(self):

        self.config = testing.setUp()
        self.meta = _initialize_sql_test()
        self.session = self.meta.Session
        patch_tests(db_session=self.session)
        req = testing.DummyRequest()
        req.db_session.commit = transaction.commit
        self.context = EventsContextFactory(req)

    def tearDown(self):
        import transaction
        transaction.abort()
        testing.tearDown()

    def test_context(self):
        self.assertTrue(self.context)
        self.failIfEqual(self.context, None)
        self.assertTrue(isinstance(self.context, SQLAlchemyORMContext))

    def test_get_collection(self):
        results = self.context.get_collection()
        self.failIfEqual(results, None)

    def test_get_member(self):
        self.context.get_member("17")
        self.context.get_member("32")
        #fails:
        # self.context.get_member(17)
        # self.context.get_member(-1)

    # NOP
    def test_create_member(self):
        func = lambda : self.context.create_member({})
        self.failUnlessRaises(NotImplementedError, func)
        # should fail
    def test_update_member(self):
        func = lambda : self.context.update_member(-1, {})
        self.failUnlessRaises(NotImplementedError, func)
        # should fail
    def test_delete_member(self):
        id = 0
        obj = self.context.get_member(id)
        self.context.delete_member(id)
        func = lambda: self.context.get_member(id)
        self.failUnlessRaises(NotImplementedError, func)
        # should fail

    def test_get_member_id_as_string(self):
        self.assertEqual(
            "10",
            self.context.get_member_id_as_string({'n': "10"}))

    def test_to_json(self):
        import workhours.models.json as json
        #value = dict(one='two', two='three')
        #jsonstr = self.context.to_json(value)
        #self.assertTrue(json.loads(jsonstr))
        ID=0
        obj = self.context.get_member(ID)
        self.context.to_json(obj)

    #def test_get_json_obj(self):
    #    self.context.get_json_obj(value, fields, wrap)

    def test_wrap_json_obj(self):
        obj = ['one','two','three']
        outp = dict(results=obj, result_count=len(obj))
        self.assertEqual(self.context.wrap_json_obj(obj), outp)

    def test_member_to_dict(self):
        member = ['one','two','three']
        self.assertEqual(
                member,
                self.context.member_to_dict(member)
        )
        # TODO
        # self.context.member_to_dict(member, fields=['one'])

    def test_default_fields(self):
        expected = ('id', 'date','type','url','title')
        fields = self.context.default_fields
        self.assertEqual(expected, fields)


