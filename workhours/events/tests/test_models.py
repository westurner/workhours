# -*- coding: utf-8 -*-


import transaction
import unittest
from pyramid import testing
from pyramid_restler.model import SQLAlchemyORMContext
from workhours.events.models import EventsContextFactory
#import workhours.models
from workhours.models.fixtures import data
from workhours.models.sql import _initialize_sql_test
from workhours.testing import PyramidFixtureTestCase

#IContextFactory
class EventsContextTests(PyramidFixtureTestCase):
    #fixtures = (data.EventData,)
    def setUp(self):
        super(EventsContextTests, self).setUp()
        #req = testing.DummyRequest()
        #self.config = testing.setUp(req)
        #self.meta = _initialize_sql_test()
        #req.db_session = self.meta.Session
        self.request = self._new_request()
        self.context = EventsContextFactory(self.request)


    def test_context(self):
        self.assertTrue(self.context)
        self.failIfEqual(self.context, None)
        self.assertTrue(isinstance(self.context, SQLAlchemyORMContext))

    def test_get_collection(self):
        results = self.context.get_collection()
        self.failIfEqual(results, None)

    def test_get_member(self):
        obj = self.context.get_member(data.EventData.one.id)
        self.assertIsNotNone(obj)

        #fails:
        for id in [None,'NONEXISTANT']:
            self.failUnlessRaises(Exception,
                lambda id: self.context.get_member(id))
        # self.context.get_member(-1)

    # NOP
    #def test_create_member(self):
    #    self.context.create_member()

    #def test_update_member(self):
    #    self.context.update_member(-1, {})

    def test_delete_member(self):
        id = data.EventData.one.id
        obj = self.context.get_member(id)
        self.assertIsNotNone(obj)
        self.context.delete_member(id)
        self.session.flush()

        obj = self.context.get_member(id)
        self.assertIsNone(obj)

    # TODO: ?
    #def test_get_member_id_as_string(self):
    #    self.assertEqual(
    #        "10",
    #        self.context.get_member_id_as_string({'n': "10"}))

    def test_to_json(self):
        obj = self.context.get_member(data.EventData.one.id)
        self.assertIsNotNone(obj)

        output = self.context.to_json(obj)
        import json
        self.assertIsNotNone(json.loads(output)) # TODO

    #def test_get_json_obj(self):
    #    self.context.get_json_obj(value, fields, wrap)

    def test_wrap_json_obj(self):
        #obj = ['one','two','three']
        #outp = dict(results=obj, result_count=len(obj))
        ID = data.EventData.one.id
        obj = [self.context.get_member(ID)]
        self.assertTrue(obj)
        outp = dict(
                results=obj,
                result_count=len(obj),
                iTotalDisplayRecords=(1,),  # datatables
                iTotalRecords=(1,),
        )
        self.assertEqual(self.context.wrap_json_obj(obj), outp)

    def test_member_to_dict(self):
        ID = data.EventData.one.id
        obj = self.context.get_member(ID)
        self.assertIsNotNone(obj)
        self.assertEqual(
                obj._asdict(),
                self.context.member_to_dict(obj)
        )
        # TODO
        # self.context.member_to_dict(member, fields=['one'])

    def test_default_fields(self):
        expected = ('id', 'date', 'source', 'url', 'title',
                    'place_id', 'source_id', 'task_id', 'meta')
        fields = self.context.default_fields
        self.assertEqual(expected, fields)




