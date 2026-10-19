import transaction
import unittest
from unittest import mock
from datetime import datetime, timedelta, timezone
from pyramid import testing
from workhours.events import models as event_models
from workhours.events.models import EventsContextFactory
from workhours.models.context import SQLAlchemyORMContext
from workhours.models import Event
from workhours_parser import SourceRecord

# import workhours.models
from workhours.models.fixtures import data
from workhours.models.sql import _initialize_sql_test
from workhours.testing import PyramidFixtureTestCase

# IContextFactory
class EventsContextTests(PyramidFixtureTestCase):
    # fixtures = (data.EventData,)
    def setUp(self):
        super().setUp()
        # req = testing.DummyRequest()
        # self.config = testing.setUp(req)
        # self.meta = _initialize_sql_test()
        # req.db_session = self.meta.Session
        self.request = self._new_request()
        self.context = EventsContextFactory(self.request)

    def test_context(self):
        self.assertTrue(self.context)
        self.assertNotEqual(self.context, None)
        self.assertTrue(isinstance(self.context, SQLAlchemyORMContext))

    def test_get_collection(self):
        results = self.context.get_collection()
        self.assertNotEqual(results, None)

    def test_get_collection_with_all_query_options(self):
        query = mock.Mock()
        query.filter.return_value = query
        query.filter_by.return_value = query
        query.options.return_value = query
        query.distinct.return_value = query
        query.order_by.return_value = query
        query.offset.return_value = query
        query.limit.return_value = query
        query.all.return_value = ["row"]
        self.context.filters = ("global filter",)

        with (
            mock.patch.object(self.session, "query", return_value=query),
            mock.patch.object(Event, "custom_filter", return_value="custom filter", create=True),
            mock.patch.object(
                event_models.orm,
                "joinedload_all",
                return_value="eager option",
                create=True,
            ) as joinedload_all,
        ):
            results = self.context.get_collection(
                eagerload=True,
                filters={"custom": "value", "id": data.EventData.one.id},
                distinct=True,
                search="needle",
                order_by=1,
                sort_dir="desc",
                offset=2,
                limit=5,
            )

        self.assertEqual(results, ["row"])
        joinedload_all.assert_called_once_with(*EventsContextFactory.eagerload)
        query.options.assert_called_once_with("eager option")
        self.assertEqual(query.filter.call_count, 3)
        query.filter_by.assert_called_once_with(id=data.EventData.one.id)
        query.distinct.assert_called_once_with()
        query.order_by.assert_called_once()
        query.offset.assert_called_once_with(2)
        query.limit.assert_called_once_with(5)

    def test_get_collection_wildcard_and_invalid_ordering(self):
        query = mock.Mock()
        query.filter.return_value = query
        query.order_by.return_value = query
        query.all.return_value = []
        with mock.patch.object(self.session, "query", return_value=query):
            self.assertEqual(
                self.context.get_collection(
                    search="%needle%", order_by=0, sort_dir="asc"
                ),
                [],
            )
            with self.assertRaises(AttributeError):
                self.context.get_collection(order_by="date")

    def test_get_member(self):
        obj = self.context.get_member(data.EventData.one.id)
        self.assertIsNotNone(obj)

        # fails:
        for id in [None, "NONEXISTANT"]:
            self.assertRaises(
                Exception, lambda id: self.context.get_member(id)
            )
        # self.context.get_member(-1)

    # NOP
    # def test_create_member(self):
    #    self.context.create_member()

    # def test_update_member(self):
    #    self.context.update_member(-1, {})

    def test_delete_member(self):
        from uuid import uuid4

        from workhours.models import Event

        event = Event(
            id=str(uuid4()),
            source=data.TaskSourceData.one.type,
            date=data.EventData.one.date,
            url="https://example.test/delete",
            title="delete test",
            meta={},
            source_id=data.TaskSourceData.one.id,
            task_id=data.TaskData.one.id,
        )
        self.session.add(event)
        self.session.commit()

        member_id = event.id
        obj = self.context.get_member(member_id)
        self.assertIsNotNone(obj)
        self.context.delete_member(member_id)
        self.session.flush()

        obj = self.context.get_member(member_id)
        self.assertIsNone(obj)

    # TODO: ?
    # def test_get_member_id_as_string(self):
    #    self.assertEqual(
    #        "10",
    #        self.context.get_member_id_as_string({'n': "10"}))

    def test_to_json(self):
        obj = self.context.get_member(data.EventData.one.id)
        self.assertIsNotNone(obj)

        output = self.context.to_json(obj)
        import json

        self.assertIsNotNone(json.loads(output))  # TODO

    def test_get_member_id_as_string(self):
        obj = self.context.get_member(data.EventData.one.id)

        self.assertEqual(
            str(data.EventData.one.id), self.context.get_member_id_as_string(obj)
        )

    # def test_get_json_obj(self):
    #    self.context.get_json_obj(value, fields, wrap)

    def test_wrap_json_obj(self):
        # obj = ['one','two','three']
        # outp = dict(results=obj, result_count=len(obj))
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
        self.assertEqual(obj._asdict(), self.context.member_to_dict(obj))

    def test_source_record_persists_with_legacy_event_fields(self):
        source_timezone = timezone(timedelta(hours=5, minutes=30))
        record = SourceRecord(
            startDate=datetime(2024, 1, 2, tzinfo=source_timezone),
            endDate=datetime(2024, 1, 2, 1, tzinfo=source_timezone),
            duration="PT1H",
            source_key="test-source:record:1",
            url="https://example.test/event",
            name="A named event",
            meta={"source": "log.shell", "session": "session-1"},
        )
        event = Event.from_uhm(
            record,
            id=Event._new_id(),
            task_id=data.TaskData.one.id,
            source_id=data.TaskSourceData.one.id,
            source=data.TaskSourceData.one.type,
        )

        self.assertEqual(event.date, record.startDate)
        self.assertEqual(event.title, record.name)
        self.assertEqual(event.end_date, record.endDate)
        self.assertEqual(event.duration, record.duration)
        self.assertEqual(event.source_key, record.source_key)
        self.assertEqual(event.task_id, data.TaskData.one.id)
        self.session.add(event)
        self.session.flush()
        self.session.commit()
        self.session.expire(event)
        saved = self.session.query(Event).filter_by(id=event.id).one()
        self.assertEqual(saved.date, record.startDate)
        self.assertEqual(saved.date.isoformat(), record.startDate.isoformat())
        self.assertEqual(saved.title, record.name)
        self.assertEqual(saved.end_date, record.endDate)
        self.assertEqual(saved.end_date.isoformat(), record.endDate.isoformat())
        self.assertEqual(saved.duration, record.duration)
        self.assertEqual(saved.source_key, record.source_key)
        self.session.delete(saved)
        self.session.commit()
        # TODO
        # self.context.member_to_dict(member, fields=['one'])

    def test_default_fields(self):
        expected = (
            "id",
            "date",
            "source",
            "url",
            "title",
            "place_id",
            "source_id",
            "task_id",
            "meta",
        )
        fields = self.context.default_fields
        self.assertEqual(expected, fields)
