from sqlite3 import dbapi2 as sqlite

__ALL__ = ["commit_uncommitted_transactions"]


def commit_uncommitted_transactions(dburi):
    connection = sqlite.connect(dburi)
    connection.commit()
    connection.close()
