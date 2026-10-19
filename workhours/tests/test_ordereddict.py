import pickle
import unittest

from workhours.ordereddict import OrderedDict


class OrderedDictTests(unittest.TestCase):
    def test_construction_and_ordered_iteration(self):
        mapping = OrderedDict([("first", 1)], second=2)
        mapping["first"] = 3

        self.assertEqual(list(mapping), ["first", "second"])
        self.assertEqual(list(reversed(mapping)), ["second", "first"])
        self.assertEqual(mapping.keys(), ["first", "second"])
        self.assertEqual(mapping.values(), [3, 2])
        self.assertEqual(mapping.items(), [("first", 3), ("second", 2)])
        self.assertEqual(list(mapping.iterkeys()), ["first", "second"])
        self.assertEqual(list(mapping.itervalues()), [3, 2])
        self.assertEqual(
            list(mapping.iteritems()), [("first", 3), ("second", 2)]
        )

        with self.assertRaises(TypeError):
            OrderedDict({}, {})

        mapping.__init__([("third", 4)])
        self.assertEqual(list(mapping), ["first", "second", "third"])

    def test_clear_and_deletion(self):
        mapping = OrderedDict([("first", 1), ("second", 2)])
        del mapping["first"]
        self.assertEqual(list(mapping), ["second"])
        with self.assertRaises(KeyError):
            del mapping["missing"]

        mapping.clear()
        mapping.clear()
        self.assertEqual(mapping, {})

        uninitialized = OrderedDict.__new__(OrderedDict)
        uninitialized.clear()
        self.assertEqual(uninitialized, {})

    def test_pop_and_popitem_orders(self):
        mapping = OrderedDict([("first", 1), ("second", 2)])
        self.assertEqual(mapping.pop("first"), 1)
        self.assertIsNone(mapping.pop("missing", None))
        with self.assertRaises(KeyError):
            mapping.pop("missing")

        mapping["third"] = 3
        self.assertEqual(mapping.popitem(), ("third", 3))
        self.assertEqual(mapping.popitem(last=False), ("second", 2))
        with self.assertRaises(KeyError):
            mapping.popitem()

    def test_update_input_protocols(self):
        mapping = OrderedDict()
        mapping.update({"dict": 1})

        class KeyMapping:
            def keys(self):
                return ["keys"]

            def __getitem__(self, key):
                return 2

        mapping.update(KeyMapping())
        mapping.update([("iterable", 3)], keyword=4)
        self.assertEqual(
            mapping.items(),
            [("dict", 1), ("keys", 2), ("iterable", 3), ("keyword", 4)],
        )

        with self.assertRaises(TypeError):
            OrderedDict.update()
        with self.assertRaises(TypeError):
            mapping.update({}, {})

    def test_defaults_comparison_and_copy(self):
        mapping = OrderedDict.fromkeys(["first", "second"], 0)
        self.assertEqual(mapping.setdefault("first", 1), 0)
        self.assertEqual(mapping.setdefault("third", 3), 3)
        self.assertEqual(mapping, {"first": 0, "second": 0, "third": 3})
        self.assertEqual(mapping, mapping.copy())
        self.assertNotEqual(mapping, OrderedDict.fromkeys(["second", "first", "third"], 0))
        self.assertNotEqual(mapping, OrderedDict())
        self.assertEqual(OrderedDict.fromkeys([], 1), OrderedDict())

    def test_repr_and_pickle_state(self):
        self.assertEqual(repr(OrderedDict()), "OrderedDict()")
        recursive = OrderedDict()
        recursive["self"] = recursive
        self.assertEqual(repr(recursive), "OrderedDict([('self', ...)])")

        mapping = OrderedDict([("key", "value")])
        self.assertEqual(pickle.loads(pickle.dumps(mapping)), mapping)

        class ExtendedOrderedDict(OrderedDict):
            pass

        extended = ExtendedOrderedDict([("key", "value")])
        extended.extra = "state"
        reduction = extended.__reduce__()
        self.assertEqual(reduction[2], {"extra": "state"})
