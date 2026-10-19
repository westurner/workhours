import unittest
from types import SimpleNamespace
from unittest import mock

from workhours.models.context import PlainContext, SQLAlchemyORMContext


class Record:
    def __init__(self, name=None, status=None):
        self.name = name
        self.status = status

    @staticmethod
    def status_filter(value):
        return ("status", value)


class RecordingQuery:
    def __init__(self, rows=()):
        self.rows = rows
        self.calls = []

    def filter(self, value):
        self.calls.append(("filter", value))
        return self

    def filter_by(self, **values):
        self.calls.append(("filter_by", values))
        return self

    def distinct(self):
        self.calls.append(("distinct",))
        return self

    def order_by(self, *values):
        self.calls.append(("order_by", values))
        return self

    def offset(self, value):
        self.calls.append(("offset", value))
        return self

    def limit(self, value):
        self.calls.append(("limit", value))
        return self

    def all(self):
        self.calls.append(("all",))
        return self.rows


class Context(SQLAlchemyORMContext):
    entity = Record
    default_fields = ("name", "status")


class FilteredContext(Context):
    filters = ("global-filter",)


class ContextTests(unittest.TestCase):
    def make_context(self, context_type=Context, rows=()):
        query = RecordingQuery(rows)
        session = mock.Mock()
        session.query.return_value = query
        context = context_type(SimpleNamespace(db_session=session))
        return context, session, query

    def test_collection_applies_optional_query_operations(self):
        context, _, query = self.make_context(rows=["row"])
        self.assertEqual(context.get_collection(), ["row"])
        self.assertEqual(query.calls, [("all",)])

        context, _, query = self.make_context(FilteredContext, rows=["row"])
        self.assertEqual(
            context.get_collection(
                filters={"status": "open", "name": "Ada"},
                distinct=True,
                order_by=("name",),
                offset=2,
                limit=5,
            ),
            ["row"],
        )
        self.assertEqual(
            query.calls,
            [
                ("filter", "global-filter"),
                ("filter", ("status", "open")),
                ("filter_by", {"name": "Ada"}),
                ("distinct",),
                ("order_by", ("name",)),
                ("offset", 2),
                ("limit", 5),
                ("all",),
            ],
        )

    def test_member_crud_and_none_cases(self):
        context, session, _ = self.make_context()
        member = Record("Ada", "open")
        session.get.return_value = member

        with self.assertRaisesRegex(ValueError, "member id cannot be None"):
            context.get_member(None)
        self.assertIs(context.get_member(1), member)
        session.get.assert_called_with(Record, 1)

        created = context.create_member({"name": "Grace", "status": "new"})
        session.add.assert_called_once_with(created)
        self.assertEqual(created.name, "Grace")
        self.assertEqual(session.commit.call_count, 1)

        session.get.return_value = None
        self.assertIsNone(context.update_member(2, {"name": "nobody"}))
        self.assertIsNone(context.delete_member(2))

        session.get.return_value = member
        self.assertIs(context.update_member(1, {"name": "Updated"}), member)
        self.assertEqual(member.name, "Updated")
        self.assertIs(context.delete_member(1), member)
        self.assertEqual(session.commit.call_count, 3)
        session.delete.assert_called_once_with(member)

    def test_member_identity_and_json_representation(self):
        context, _, _ = self.make_context()
        member = Record("Ada", "open")

        with mock.patch(
            "workhours.models.context.sa_inspect",
            return_value=SimpleNamespace(identity=None),
        ):
            self.assertIsNone(context.get_member_id(member))
        with mock.patch(
            "workhours.models.context.sa_inspect",
            return_value=SimpleNamespace(identity=(7,)),
        ):
            self.assertEqual(context.get_member_id(member), 7)
        with mock.patch(
            "workhours.models.context.sa_inspect",
            return_value=SimpleNamespace(identity=(7, 8)),
        ):
            self.assertEqual(context.get_member_id(member), (7, 8))

        with mock.patch.object(context, "get_member_id", return_value="id"):
            self.assertEqual(context.get_member_id_as_string(member), "id")
        with mock.patch.object(context, "get_member_id", return_value=(7, 8)):
            self.assertEqual(context.get_member_id_as_string(member), "[7, 8]")

        expected = {"name": "Ada", "status": "open"}
        self.assertEqual(
            context.get_json_obj(member),
            {"results": [expected], "result_count": 1},
        )
        self.assertEqual(context.get_json_obj([member], wrap=False), [expected])
        self.assertEqual(
            context.get_json_obj(member, ("name",), wrap=False),
            [{"name": "Ada"}],
        )
        self.assertEqual(context.member_to_dict(member, ("name",)), {"name": "Ada"})
        self.assertEqual(
            context.to_json(member),
            '{"results": [{"name": "Ada", "status": "open"}], "result_count": 1}',
        )

    def test_plain_context_delegation_keys_and_json(self):
        plain = PlainContext(
            object(),
            get_member=lambda key: {"id": key},
            get_collection=lambda **kwargs: kwargs,
            index_key="id",
            default_fields=("name",),
        )
        self.assertEqual(plain.get_member(3), {"id": 3})
        self.assertEqual(plain.get_collection(limit=5), {"limit": 5})
        self.assertIs(plain.get_member_key_as_string({"id": 3}), 3)
        self.assertEqual(plain.get_member_key_as_string({"id": "key"}), "key")
        self.assertEqual(plain.get_member_key_as_string({"id": [1, 2]}), "[1,2]")

        class PlainRecord:
            def _asdict(self):
                return {"name": "Ada"}

        member = PlainRecord()
        self.assertEqual(
            plain.get_json_obj(member, None, True),
            {"results": [{"name": "Ada"}], "result_count": 1},
        )
        self.assertEqual(
            plain.get_json_obj([member], None, False), [{"name": "Ada"}]
        )
        self.assertEqual(
            plain.get_json_obj(member, ("name",), False), [{"name": "Ada"}]
        )
        self.assertEqual(plain.to_json({"name": "Ada"}), '{"name":"Ada"}')

        defaults = PlainContext(object())
        self.assertEqual(defaults.get_member(1), {})
        self.assertEqual(defaults.get_collection(), {})
        for operation in (
            lambda: defaults.create_member({}),
            lambda: defaults.update_member(1, {}),
            lambda: defaults.delete_member(1),
        ):
            with self.assertRaises(NotImplementedError):
                operation()

    def test_sqlalchemy_default_fields_are_discovered_lazily(self):
        class DynamicContext(SQLAlchemyORMContext):
            entity = Record

        context = DynamicContext(SimpleNamespace(db_session=mock.Mock()))
        inspection = SimpleNamespace(
            column_attrs=SimpleNamespace(keys=lambda: ["name", "status"])
        )
        with mock.patch("workhours.models.context.sa_inspect", return_value=inspection):
            self.assertEqual(context.default_fields, ("name", "status"))

        self.assertEqual(
            context.member_to_dict(Record("Ada", "open")),
            {"name": "Ada", "status": "open"},
        )
