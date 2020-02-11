
import workhours.models.json as json
import logging

from jinja2 import Markup
from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPNotFound, HTTPBadRequest
from pyramid.renderers import render
from pyramid.response import Response
from pyramid_restler.view import RESTfulView
from workhours.events.models import EventsContextFactory
from workhours.models import Event, DBSession
from workhours.models.html.datatables import read_datatables_params, build_query
from workhours.future import OrderedDict

log = logging.getLogger('.events.views')
from pprint import pformat

class EventsRESTfulView(RESTfulView):
    #def render_to_response(self, member):
    #    raise Exception(member)
    context = EventsContextFactory
    _entity_name = 'event'
    _entity_name_plural = 'events'
    _renderers = OrderedDict((
        ('html', (('text/html',), 'utf-8',)),
        ('json', (('application/json',), 'utf-8')),
        ('xml', (('application/xml',), 'utf-8')),
    ))

    def get_collection(self):
        kwargs = self.request.params.get('$$', {})
        if kwargs:
            kwargs = json.loads(kwargs)

        log.debug(kwargs)
        dtkwargs = read_datatables_params(self.request)
        log.debug(dtkwargs)

        kwargs.update(dtkwargs)
        log.debug(kwargs)

        if 'limit' not in kwargs:
            kwargs['limit'] = 100

        log.debug(kwargs)

        log.debug("get_collection: %s", pformat(kwargs))

        collection = self.context.get_collection(**kwargs)
        #collection = build_query(self.request)
        return self.render_to_response(collection)

    def determine_renderer(self):
        request = self.request
        rendererstr = (request.matchdict or {}).get('renderer', '').lstrip('.')

        if rendererstr:
            if rendererstr in self._renderers:
                return rendererstr
            return 'to_404'
        for rndrstr, (ct, charset) in self._renderers.items():
            if request.accept.best_match(ct):
                return rndrstr
        return 'to_404'

    def render_to_response(self, value, fields=None):
        if value is None:
            raise HTTPNotFound(self.context)
        renderer = self.determine_renderer()
        log.debug(renderer)

        try:
            renderer = getattr(self, 'render_{0}'.format(renderer))
        except AttributeError:
            name = self.__class__.__name__
            raise HTTPBadRequest(
                '{0} view has no renderer "{1}".'.format(name, renderer))
        return Response(**renderer(value))

    def render_json(self, value):
        response_data = dict(
            body=self.context.to_json(value, self.fields, self.wrap),
            content_type='application/json',
        )
        return response_data

    def render_xml(self, value):
        raise HTTPBadRequest('XML renderer not implemented.')

    @reify
    def fields(self): # TODO
        fields = self.request.params.get('$fields', None)
        if fields is not None:
            fields = json.loads(fields)
        return fields

    @reify
    def wrap(self):
        wrap = self.request.params.get('$wrap', 'true').strip().lower()
        return wrap in ('1', 'true')

    def render_to_404(self, value):
        # scrub value
        return HTTPNotFound(self.context)

    def render_json(self, value):
        renderer=self._renderers['json']
        response_data = dict(
            body=self.context.to_json(value, self.fields, self.wrap),
            charset=renderer[1],
            content_type=renderer[0][0],
        )
        return response_data

    def render_html(self, value):
        renderer=self._renderers['html']
        title='api : events'
        fields = self.context.default_fields

        # a model instance
        if isinstance(value, Event): #hasattr(value, '__iter__'):
            value = (value,)
            title = "Event: %s" % Event.id
            template = 'events/templates/_event.jinja2'
        else:
            template = 'events/templates/_events_table.jinja2'

        fieldsdict = [dict(mData=f) for f in fields]

        # an iterable
        return dict(
            body=render(template,
                dict(
                    value=value,
                    fields=fields,
                    table_id=self._entity_name_plural,
                    title=title,
                    wrap=self.wrap,
                    js_links=("workhours:static/datatable/js/jquery.dataTables.min.js",),
                    fields_json=Markup(json.dumps(fieldsdict))
                ),
                self.request),
            charset=renderer[1],
            content_type=renderer[0][0]
        )

