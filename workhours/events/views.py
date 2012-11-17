from workhours.models.context import PlainContext
from pyramid_restler.view import RESTfulView
from collections import OrderedDict

from workhours.models import Event

def get_event(*args, **kargs):
    Event.query()

def get_events(*args, **kwargs):
    return Event.query.all()

def EventsContextFactory(request):
    return PlainContext(request,
            get_member=lambda n: n and get_event(request),
            get_collection=lambda *args, **kwargs: get_event(request),
            index_key='n'
            )

class EventsRESTfulView(RESTfulView):
    #def render_to_response(self, member):
    #    raise Exception(member)

    _entity_name = 'number'
    _renderers = OrderedDict((
        ('html', (('text/html',), 'utf-8',)),
        ('json', (('application/json',), 'utf-8')),
        ('xml', (('application/xml',), 'utf-8')),
    ))

    def determine_renderer(self):
        request = self.request
        rendererstr = (request.matchdict or {}).get('renderer', '').lstrip('.')

        if rendererstr:
            if rendererstr in self._renderers:
                return rendererstr
            return 'to_404'
        for rndrstr, (ct, charset) in self._renderers.iteritems():
            if request.accept.best_match(ct):
                return rndrstr
        return 'to_404'

    def render_to_response(self, value, fields=None):
        rendererstr = self.determine_renderer()
        try:
            renderer = getattr(self, 'render_{0}'.format(rendererstr))
        except AttributeError:
            name = self.__class__.__name__
            raise HTTPBadRequest(
                '{0} view has no renderer "{1}".'.format(name, rendererstr))

        renderer_output = renderer(value)
        if 'body' in renderer_output:
            return Response(**renderer_output)

        return self.render_to_404(value)

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
        return dict(
            body=render('numbers/templates/number.jinja2', value,
                        self.request),
            charset=renderer[1],
            content_type=renderer[0][0]
        )

