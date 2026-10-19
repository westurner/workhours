import os.path
from zope.interface import Attribute
from zope.interface import Interface
from zope.interface import implements


class IDataSource(Interface):
    """
    baseclass/interface for DataSource modules
    
    """

    types = Attribute("types emitted")
    files = Attribute("file paths")

    def setup(self):
        """
        configure and setup for parsing
        """

    def parse(self):
        """
        :returns: generator of items
        """

    def __del__(self):
        """
        shutdown
        """


class DataSource:
    implements(IDataSource)

    def __init__(self, name, *args, **kwargs):
        self.name = name
        self.args = args
        self.kwargs = kwargs
        self.uri = self.kwargs["uri"]
        self._files = ("",)

    @property
    def files(self):
        return [os.path.dirname(self.uri, f) for f in self._files]

    def setup(self):
        """ setup_mappers(self.uri) """

    def parse(self):
        yield from self.parse____


def test_data_source():
    ds = DataSource("cool", uri="test")
