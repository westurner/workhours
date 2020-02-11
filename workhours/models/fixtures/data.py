from fixture import DataSet as _DataSet
import datetime


_DataSet.default_primary_key = "_id"


class DataSet(_DataSet):
    class Meta:
        primary_key = ["_id"]


class UserData(DataSet):
    class one:
        id = "c94f2784-8d42-469a-a5c6-3aaa2934f703"
        username = "testfixture_username"
        name = "name"
        email = "example@localhost"
        # passphrase_ = '$pbkdf2-sha512$12000$NzQ2NTczNzQ2NjY5Nzg3NDc1NzI2NTVmNzU3MzY1NzI2ZTYxNmQ2NQ$BHqTZ4en1MZaCAOcCfF.nEVJEZu2tRxt8Xoigcdv85CYGoGBsum4Ao9oZ8Wra8hZkrIwcv7WUvW7i9PlN/3RmQ'

        passphrase_ = "$pbkdf2-sha512$12000$NzQ2NTczNzQ2NjY5Nzg3NDc1NzI2NTVmNzU3MzY1NzI2ZTYxNmQ2NQ$awknN.lgn4kJn2mrQnj11J9mDtIpJ0yEMJdHP0b4v5RtO3OLilONokO7M2Pu8/77fwu0mGDn0GV3wyp5czr1cQ"
        passphrase = "passphrase"


class TaskQueueData(DataSet):
    class one:
        id = "c37e32d9-79db-4dfd-a19d-4a8b12416da8"
        type = "test.bookmarks"
        label = "label"
        uri = "uri"  # TODO
        host = "host"
        user = "user"


class TaskSourceData(DataSet):
    class one:
        id = "ab9cfd6a-3d47-49fd-85dc-225c91e1836a"
        queue_id = TaskQueueData.one.id
        type = TaskQueueData.one.type
        date = datetime.datetime.now()
        url = TaskQueueData.one.uri
        label = "test label"
        host = TaskQueueData.one.host
        user = TaskQueueData.one.user


class TaskData(DataSet):
    class one:
        id = "873e32d9-79db-4dfd-a19d-4a8b12416da8"
        queue_id = TaskQueueData.one.id
        args = {}
        date = datetime.datetime.now()  # TODO
        state = "state"
        statemsg = "statemsg"


class PlaceData(DataSet):
    class one:
        id = "123e32d9-79db-4dfd-a19d-4a8b12416da8"
        url = "http://example.org/test"
        eventcount = 1
        meta = {}
        scheme = "http://"
        port = 80
        netloc = "localhost"
        path = "/test"
        query = None
        fragment = None  # TODO ...


class EventData(DataSet):
    class one:
        id = "456e32d9-79db-4dfd-a19d-4a8b12416da8"
        # source = 'firefox.bookmarks'
        date = datetime.datetime.now()  # TODO
        url = "http://example.org/test"
        title = "title"
        meta = {}
        place_id = PlaceData.one.id
        task_id = TaskData.one.id
        source = TaskSourceData.one.type
        source_id = TaskSourceData.one.id


class ReportTypeData(DataSet):
    class one:
        id = "001e32d9-79db-4dfd-a19d-4a8b12416da8"
        label = "label"
        data = {}


class ReportData(DataSet):
    class one:
        id = "abce32d9-79db-4dfd-a19d-4a8b12416da8"
        report_type_id = ReportTypeData.one.id
        title = "title"
        data = {}


ALL_FIXTURES = (
    UserData,
    TaskQueueData,
    TaskSourceData,
    TaskData,
    PlaceData,
    EventData,
    ReportTypeData,
    ReportData,
)
