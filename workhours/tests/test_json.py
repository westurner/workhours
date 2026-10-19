import unittest
from collections import namedtuple
from datetime import date
from decimal import Decimal

from workhours.models.json import DefaultJSONEncoder, dumps, loads


class LegacyRecord:
    _fields = ("value",)

    def __init__(self, value):
        self.value = value

    def keys(self):
        return self._fields


class JSONEncoderTests(unittest.TestCase):
    def test_default_conversions(self):
        Record = namedtuple("Record", "value")
        encoder = DefaultJSONEncoder()

        self.assertEqual(encoder.default(Record("named")), {"value": "named"})
        self.assertEqual(encoder.default(LegacyRecord("legacy")), {"value": "legacy"})
        self.assertEqual(encoder.default(Decimal("1.25")), "1.25")
        self.assertEqual(encoder.default(date(2024, 1, 2)), "2024-01-02")

        ordinary = object()
        self.assertIs(encoder.default(ordinary), ordinary)

    def test_wrapped_json_helpers(self):
        encoded = dumps({"date": date(2024, 1, 2), "amount": Decimal("2.5")})
        self.assertEqual(
            loads(encoded), {"date": "2024-01-02", "amount": "2.5"}
        )
