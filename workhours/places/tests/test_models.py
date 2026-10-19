from unittest import mock

from workhours.models import Place
from workhours.places.models import PlacesContextFactory
from workhours.testing import PyramidFixtureTestCase


class PlacesContextTests(PyramidFixtureTestCase):
	def setUp(self):
		super().setUp()
		self.query = mock.Mock()
		for method in (
			"filter", "filter_by", "options", "distinct", "order_by",
			"offset", "limit",
		):
			getattr(self.query, method).return_value = self.query
		self.query.all.return_value = ["row"]
		self.session.query = mock.Mock(return_value=self.query)
		self.context = PlacesContextFactory(self.request)

	def test_get_collection_filters_search_and_pagination(self):
		self.context.filters = ("global filter",)
		with mock.patch.object(
			Place, "slug_filter", return_value="slug filter", create=True
		):
			result = self.context.get_collection(
				filters={"slug": "value", "url": "https://example.test"},
				distinct=True,
				search="needle",
				order_by=1,
				sort_dir="desc",
				offset=2,
				limit=5,
			)

		self.assertIs(result, self.query)
		self.assertEqual(self.query.filter.call_count, 3)
		self.query.filter_by.assert_called_once_with(url="https://example.test")
		self.query.distinct.assert_called_once_with()
		self.query.order_by.assert_called_once()
		self.query.offset.assert_called_once_with(2)
		self.query.limit.assert_called_once_with(5)

	def test_get_collection_defaults_wildcard_search_and_invalid_order(self):
		self.assertIs(self.context.get_collection(), self.query)
		self.assertEqual(
			self.context.get_collection(search="%needle%", order_by=0),
			self.query,
		)
		with self.assertRaises(AttributeError):
			self.context.get_collection(order_by="url")

	def test_get_member_integer_invalid_and_url_identifiers(self):
		self.assertEqual(self.context.get_member("123"), self.query.get.return_value)
		self.assertEqual(self.context.get_member("invalid"), self.query.get.return_value)
		self.query.filter.return_value.one.return_value = "url row"
		self.assertEqual(
			self.context.get_member("https://example.test"), "url row"
		)
		self.query.get.assert_any_call("123")
		self.query.get.assert_any_call("invalid")

	def test_count_and_json_wrapper(self):
		self.session.query.return_value.one.return_value = (7,)
		self.assertEqual(self.context.count(), (7,))
		with mock.patch.object(self.context, "count", return_value=(7,)):
			self.assertEqual(
				self.context.wrap_json_obj(["a", "b"]),
				{
					"results": ["a", "b"],
					"result_count": 2,
					"iTotalRecords": 7,
					"iTotalDisplayRecords": 7,
				},
			)
