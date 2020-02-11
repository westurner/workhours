from workhours.models import _Base
from workhours.reports import write_csv


def add_gap_tuples(
    iterable, attrs, gaptime=15, date_attr=lambda x: x[0],
):
    ltime = None
    gaprow = len(attrs) * ("--------",)
    timedelta = datetime.timedelta(minutes=gaptime)
    for item in iterable:
        date = date_attr(item)
        if ltime and (ltime + timedelta) < date:
            yield gaprow
        ltime = date
        yield item


def create_gap_csv(
    cls,
    output_filename,
    gaptime=15,
    attrs=("date", "source", "url", "title"),
    order_by="date",
):
    """
    Generate a CSV with '----' lines where events are
    separated by more than ``gaptime`` minutes

    :param meta: SQLAlchemy meta (with meta.Session)
    :type meta: SQLAlchemy meta
    :param output_filename: path to the CSV output file
    :type output_filename: str
    :param gaptime: Minimum gap size
    :type gaptime: int

    :returns: None
    """

    return write_csv(
        output_filename,
        add_gap_tuples(
            cls.select_columns(attrs, order_by=order_by),
            attrs,
            gaptime=gaptime,
        ),
        unicode_mangle=True,
    )
