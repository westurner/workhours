import unittest
import uuid
from types import SimpleNamespace
from unittest import mock

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import CHAR

from workhours.models.sql.guid import GUID
from workhours.models.sqlite_utils import commit_uncommitted_transactions
from workhours.models.sqla_utils import (
    JSONEncodedDict,
    MutationDict,
    clear_mappers,
)


class ModelUtilityTests(unittest.TestCase):
    def test_mutation_dict_coercion_and_change_notifications(self):
        mapping = MutationDict()
        self.assertIs(MutationDict.coerce("data", mapping), mapping)
        self.assertEqual(MutationDict.coerce("data", {"key": 1}), {"key": 1})
        with self.assertRaises(ValueError):
            MutationDict.coerce("data", "not a mapping")

        with mock.patch.object(mapping, "changed") as changed:
            mapping["key"] = 2
            del mapping["key"]
        self.assertEqual(changed.call_count, 2)

    def test_json_encoded_dict_none_and_values(self):
        column_type = JSONEncodedDict()
        encoded = column_type.process_bind_param({"key": "value"}, None)
        self.assertEqual(encoded, '{"key":"value"}')
        self.assertEqual(column_type.process_result_value(encoded, None), {"key": "value"})
        self.assertIsNone(column_type.process_bind_param(None, None))
        self.assertIsNone(column_type.process_result_value(None, None))

    def test_clear_mappers_disposes_each_discovered_registry_once(self):
        registry = mock.Mock()
        mapped = SimpleNamespace(registry=registry)
        with mock.patch("sqlalchemy.inspect", side_effect=[mapped, mapped, None]):
            clear_mappers([object(), object(), object()])
        registry.dispose.assert_called_once_with()

        with mock.patch("sqlalchemy.inspect", return_value=None):
            clear_mappers([object()])
            clear_mappers([])

    def test_guid_dialect_and_value_conversions(self):
        postgresql = SimpleNamespace(
            name="postgresql", type_descriptor=lambda value: value
        )
        sqlite = SimpleNamespace(name="sqlite", type_descriptor=lambda value: value)
        guid_type = GUID()

        self.assertIsInstance(guid_type.load_dialect_impl(postgresql), UUID)
        self.assertIsInstance(guid_type.load_dialect_impl(sqlite), CHAR)

        value = uuid.uuid4()
        self.assertEqual(guid_type.process_bind_param(value, postgresql), str(value))
        self.assertEqual(guid_type.process_bind_param(value, sqlite), str(value))
        self.assertEqual(guid_type.process_bind_param("already encoded", sqlite), "already encoded")
        self.assertIsNone(guid_type.process_bind_param(None, sqlite))
        self.assertEqual(guid_type.process_result_value(value, sqlite), str(value))
        self.assertIsNone(guid_type.process_result_value(None, sqlite))
        self.assertEqual(GUID.new_guid("name", uuid.NAMESPACE_URL), GUID.new_guid("name", uuid.NAMESPACE_URL))
        self.assertEqual(len(GUID.new_guid()), 36)

    def test_sqlite_helper_commits_and_closes(self):
        connection = mock.Mock()
        with mock.patch(
            "workhours.models.sqlite_utils.sqlite.connect",
            return_value=connection,
        ) as connect:
            commit_uncommitted_transactions("events.sqlite")

        connect.assert_called_once_with("events.sqlite")
        connection.commit.assert_called_once_with()
        connection.close.assert_called_once_with()
