import workhours.models.json as json

from workhours.future import OrderedDict
from jinja2 import Markup
from pyramid.renderers import render, render_to_response
from pyramid.response import Response
from pyramid.view import view_config
from pyramid_restler.view import RESTfulView
from workhours.models import ReportType, Report
from workhours.reports.models import ReportContext


class ReportViews(object):
    def __init__(self, request):
        self.request = request


class ReportView(RESTfulView):
    context = ReportContext
    _report_type = "DEFAULT"
    _entity_name = "report"
    _renderers = OrderedDict(
        (
            ("html", (("text/html",), "utf-8",)),
            ("json", (("application/json",), "utf-8")),
            ("xml", (("application/xml",), "utf-8")),
        )
    )
    default_render = "html"
    fields = ReportContext.default_fields

    def determine_renderer(self):
        request = self.request
        rendererstr = (request.matchdict or {}).get("renderer", "").lstrip(".")

        if rendererstr:
            if rendererstr in self._renderers:
                return rendererstr
            return "to_404"
        for rndrstr, (ct, charset) in self._renderers.items():
            if request.accept.best_match(ct):
                return rndrstr
        return "to_404"

    def render_html(self, value):
        renderer = self._renderers["html"]
        title = "report : %s" % self.context._report_type
        fields = self.context.default_fields

        if isinstance(value, Report):
            # an iterable
            self.request.response.charset = renderer[1]
            self.request.response.content_type = renderer[0][0]
            return dict(
                body=render(
                    "reports/templates/_report.jinja2",
                    dict(
                        report=value,
                        fields=self.fields,
                        table_id=self._entity_name,
                        title=title,
                        wrap=self.wrap,
                        js_links="datatable/js/jquery.dataTables.min.js",
                        fields_json=Markup(
                            json.dumps([dict(mData=f) for f in self.fields])
                        ),
                    ),
                    self.request,
                ),
            )
        else:
            return render_to_response(
                "reports/templates/_report_list.jinja2",
                {
                    "title": "Reports",
                    "report_types": value
                    # self.request.db_session.query(ReportType)
                },
                self.request,
            )
        raise Exception()


class DomainsView(ReportView):
    _report_name = "domains"


class ProjectsView(ReportView):
    _report_name = "projects"


class WikipediaPagesView(ReportView):
    _report_name = "wikipedia pages"


class QuestionsView(ReportView):
    _report_name = "questions"
