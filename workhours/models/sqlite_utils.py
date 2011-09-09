from sqlite3 import dbapi2 as sqlite


__ALL__=['commit_uncommitted_transactions']

def commit_uncommitted_transactions(db_filename):
    connection = sqlite.connect(db_filename)
    connection.commit()
    connection.close()

