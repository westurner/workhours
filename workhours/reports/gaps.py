
from workhours.reports import add_gap_tuples, write_csv


def create_gap_csv(cls, 
                  output_filename,
                  gaptime=15,
                  attrs=('date','source','url','title'),
                  order_by='date'):
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
                        gaptime=gaptime),
                unicode_mangle=True,
                )
