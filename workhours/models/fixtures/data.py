from fixture import DataSet
import datetime

class UserData(DataSet):
    class one:
        _id = 'c94f2784-8d42-469a-a5c6-3aaa2934f703'
        username = 'testfixture_username'
        name = 'name'
        email = 'example@localhost'
        passphrase = 'passphrase'


class TaskQueueData(DataSet):
    class one:
        _id = 'c37e32d9-79db-4dfd-a19d-4a8b12416da8'
        type = 'type'
        label = 'label'
        uri = 'uri'
        host = 'host'
        user = 'user'


class TaskData(DataSet):
    class one:
        _id = '873e32d9-79db-4dfd-a19d-4a8b12416da8'
        queue_id = TaskQueueData.one._id
        args = {}
        date = datetime.datetime.now() # TODO
        state = 'state'
        statemsg = 'statemsg'


class PlaceData(DataSet):
    class one:
        _id = '123e32d9-79db-4dfd-a19d-4a8b12416da8'
        url = 'http://localhost/test'
        eventcount = 1
        meta = {}
        scheme = 'http://'
        port = 80
        netloc = 'localhost'
        path = '/test'
        query = None
        fragment = None


class EventData(DataSet):
    class one:
        _id = '456e32d9-79db-4dfd-a19d-4a8b12416da8'
        source = 'firefox.bookmarks'
        date = datetime.datetime.now() # TODO
        url = 'http://localhost/test'
        title = 'title'
        meta = {}
        place_id = PlaceData.one._id
        task_id = TaskData.one._id


class ReportTypeData(DataSet):
    class one:
        _id = '001e32d9-79db-4dfd-a19d-4a8b12416da8'
        label = 'label'
        data = {}


class ReportData(DataSet):
    class one:
        _id = 'abce32d9-79db-4dfd-a19d-4a8b12416da8'
        report_type_id = ReportTypeData.one._id
        title = 'title'
        data = {}


ALL_FIXTURES = (
    UserData,
    TaskQueueData,
    TaskData,
    PlaceData,
    EventData,
    ReportTypeData,
    ReportData,
)
