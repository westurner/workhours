import csv
import datetime
import codecs


def add_gap_tuples(iterable,
                    attrs,
                    gaptime=15,
                    date_attr=lambda x: x[0],
                    ):
    ltime = None
    gaprow = len(attrs)*('--------',)
    timedelta = datetime.timedelta(minutes=gaptime)
    for item in iterable:
        date=date_attr(item)
        if ltime and (ltime + timedelta) < date:
            yield gaprow
        ltime = date
        yield item


def _write_csv(output, iterable, attrs, unicode_mangle=False):
    cw = csv.writer(output)
    cw.writerow(attrs)

    for row in iterable:
        try:
            cw.writerow(row)
        except UnicodeDecodeError:
            if not unicode_mangle:
                raise

            row = list(row)
            row[2] = row[2].decode('utf8','replace') # ...
            # Retry
            cw.writerow(row)
        except UnicodeEncodeError, error:
            if not unicode_mangle:
                raise
            print type(error.object), error.encoding
            print error.object.encode('utf8','replace')

            row = list(row)
            row[2] = unicode(row[2]).encode('utf8','replace')
            row[3] = unicode(row[3]).encode('utf8','replace')
            print row
            cw.writerow(row)


def write_csv(output, iterable, attrs, **kwargs):
    if isinstance(output, 'basestring'):
        with codecs.open(output,'w+',encoding='utf-8') as _file:
            _write_csv(_file, iterable, attrs, **kwargs)
    elif hasattr(output, 'write'):
        _write_csv(output, iterable, attrs, **kwargs)
    else:
        raise NotImplementedError(type(output), str(output))
    return output


def _write_html(output, iterable, attrs, unicode_mangle=False):
    # TODO: escape html entities
    #cw = csv.writer(output)a
    cw.write("<table>")
    cw.write("<tr>")
    [cw.write(u"<th>%s</th>" % col) for col in attrs]
    cw.write("</tr>")

    format_row = lambda row: ((u"<td>%s</td>" % col) for col in row)

    for row in iterable:

        cw.write("<tr>")
        try:
            [cw.write(col) for col in format_row(row)]
        except UnicodeDecodeError:
            if not unicode_mangle:
                raise

            row = list(row)
            row[2] = row[2].decode('utf8','replace') # ...
            # Retry
            cw.writerow(row)
        except UnicodeEncodeError, error:
            if not unicode_mangle:
                raise
            print type(error.object), error.encoding
            print error.object.encode('utf8','replace')

            row = list(row)
            row[2] = unicode(row[2]).encode('utf8','replace')
            row[3] = unicode(row[3]).encode('utf8','replace')
            print row
            [cw.write(col) for col in format_row(row)]

            # TODO..
        finally:
            cw.write("</tr>")

    cw.write("</table>")
