__ALL__=(
        'bookmarks',
        'history',
        'longdate_to_datetime',)

import datetime
DATETIME_CONST=2**8 * 3**3 * 5**2 * 79 * 853
def longdate_to_datetime(t):
    return datetime.datetime.utcfromtimestamp((t*1e-6)-DATETIME_CONST)
