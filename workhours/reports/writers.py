#!/usr/bin/env python
# encoding: utf-8

"""
Report writers for various formats
"""
import csv
import workhours.models.json as json
import io
import functools


def itemgetter_default(args, default=None):
    """
    Return a callable object that fetches the given item(s) from its operand,
    or the specified default value.

    Similar to operator.itemgetter except returns ``default``
    when the index does not exist
    """
    if args is None:
        columns = range(len(line))
    else:
        columns = args

    def _itemgetter(row):
        for col in columns:
            try:
                yield row[col]
            except IndexError:
                yield default

    return _itemgetter


def get_list_from_str(str_, cast_callable=int):
    if str_ is None:
        return None
    if not str_ or not str_.strip():
        return []
    return [cast_callable(x.strip()) for x in str_.split(",")]


# TODO FIXME
import operator


def sort_by(sortstr, iterable, reverse=False):
    columns = get_list_from_str(sortstr)
    log.debug("columns: %r" % columns)

    # get_columns = operator.itemgetter(*columns)

    get_columns = itemgetter_default(columns, default=None)

    return sorted(iterable, key=get_columns, reverse=reverse)


class ResultWriter(object):
    OUTPUT_FILETYPES = {
        "csv": ",",
        "json": True,
        "tsv": "\t",
        "html": True,
        "txt": True,
    }
    filetype = None

    def __init__(self, _output, *args, **kwargs):
        self._output = _output
        self._conf = kwargs
        self.setup(_output, *args, **kwargs)

    def setup(self, *args, **kwargs):
        pass

    def set_output(self, _output):
        if _output and self._output is not None:
            raise Exception()
        else:
            self._output = _output

    def header(self, *args, **kwargs):
        pass

    def write(self, obj):
        print(obj, file=self._output)

    def write_numbered(self, obj):
        print(obj, file=self._output)

    def footer(self, *args, **kwargs):
        pass

    @classmethod
    def get_writer(cls, _output, filetype="csv", **kwargs):
        """get writer object for _output with the specified filetype

        :param output_filetype: csv | json | tsv
        :param _output: output file

        """
        output_filetype = filetype.strip().lower()

        if output_filetype not in ResultWriter.OUTPUT_FILETYPES:
            raise Exception()

        writer = None
        if output_filetype == "txt":
            writer = ResultWriter_txt(_output)
        elif output_filetype == "csv":
            writer = ResultWriter_csv(_output, **kwargs)
        elif output_filetype == "tsv":
            writer = ResultWriter_csv(_output, delimiter="\t", **kwargs)
        elif output_filetype == "json":
            writer = ResultWriter_json(_output)
        elif output_filetype == "html":
            writer = ResultWriter_html(_output, **kwargs)
        else:
            raise NotImplementedError()
        return (
            writer,
            (
                kwargs.get("number_lines")
                and writer.write_numbered
                or writer.write
            ),
        )


class ResultWriter_txt(ResultWriter):
    filetype = "txt"

    def write_numbered(self, obj):
        self.write(obj._numbered_str(odelim="\t"))


class ResultWriter_csv(ResultWriter):
    filetype = "csv"

    def setup(self, *args, **kwargs):
        self.delimiter = kwargs.get(
            "delimiter", ResultWriter.OUTPUT_FILETYPES.get(self.filetype, ",")
        )
        self._output_csv = csv.writer(
            self._output,
            quoting=csv.QUOTE_NONNUMERIC,
            delimiter=self.delimiter,
        )
        # doublequote=True)

    def header(self, *args, **kwargs):
        attrs = kwargs.get("attrs", PylineResult._fields)
        self._output_csv.writerow(attrs)

    def write(self, obj):
        self._output_csv.writerow(obj.result)

    def write_numbered(self, obj):
        self._output_csv.writerow(tuple(obj._numbered()))


class ResultWriter_json(ResultWriter):
    filetype = "json"

    def write(self, obj):
        print(
            json.dumps(obj._asdict(), indent=2), end=",\n", file=self._output
        )

    write_numbered = write


class ResultWriter_html(ResultWriter):
    filetype = "html"

    def header(self, *args, **kwargs):
        attrs = self._conf.get("attrs")
        title = self._conf.get("title")
        if title:
            self._output.write("<p>")
            self._output.write(title)  # TODO
            self._output.write("</p>")
        self._output.write("<table>")
        if bool(attrs):
            self._output.write("<tr>")
            for col in attrs:
                self._output.write("<th>%s</th>" % col)
            self._output.write("</tr>")

    def _html_row(self, obj):
        yield "\n<tr>"  # TODO: handle regular tuples
        for attr, col in obj._asdict().items():  # TODO: zip(_fields, ...)
            yield "<td%s>" % (
                (attr is not None) and (' class="%s"' % attr) or ""
            )
            if hasattr(col, "__iter__"):
                for value in col:
                    yield "<span>%s</span>" % value
            else:
                yield "%s" % (
                    col and hasattr(col, "rstrip") and col.rstrip() or str(col)
                )  # TODO
            yield "</td>"
        yield "</tr>"

    def write(self, obj):
        return self._output.write("".join(self._html_row(obj,)))

    def footer(self):
        self._output.write("</table>\n")


def write_iterable_to_output(
    iterable,
    _output,
    filetype="csv",
    number_lines=False,
    attrs=None,
    sortfunc=None,
    **kwargs
):
    (writer, output_func) = ResultWriter.get_writer(
        _output,
        filetype=filetype,
        number_lines=number_lines,
        attrs=attrs,
        **kwargs
    )

    writer.header()

    for result in iterable:
        if not result.result:
            continue  # TODO
        try:
            output_func(result)
        except Exception as e:
            log.exception(e)
            continue  # TODO

    writer.footer()

    return writer, output_func


def write_iterable_to_file(iterable, filename, *args, **kwargs):
    with codecs.open(filename, "w", encoding="utf8") as _output:
        return write_iterable_to_output(iterable, _output, *args, **kwargs)
