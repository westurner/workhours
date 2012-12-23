
from jinja2 import Markup
from pprint import pformat
from pyramid.decorator import reify
from pyramid.exceptions import HTTPNotFound
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.renderers import render
from pyramid.response import Response
from pyramid_restler.view import RESTfulView
from sqlalchemy import orm
from workhours.models import Place, DBSession
from workhours.models.html.datatables import read_datatables_params
from workhours.places.models import PlacesContextFactory
from workhours.future import OrderedDict
import logging
import workhours.models.json as json
log = logging.getLogger('workhours.places.views')

class PlacesRESTfulView(RESTfulView):
    _entity_name = 'place'
    _entity_name_plural = 'places'
    _renderers = OrderedDict((
        ('html', (('text/html',), 'utf-8',)),
        ('json', (('application/json',), 'utf-8')),
        ('xml', (('application/xml',), 'utf-8')),
    ))

    fields = ['_id','url','netloc','eventcount','title']

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
        for rndrstr, (ct, charset) in self._renderers.iteritems():
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

    def render_xml(self, value):
        raise HTTPBadRequest('XML renderer not implemented.')

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
        title='api : places'
        fields = self.fields

        # a model instance
        if isinstance(value, Place): #not hasattr(value, '__iter__'):
            value = [value]
            title = u"Place: %s" % self.request.matchdict['_id']
            template = 'places/templates/_place.jinja2'
        else:
            template = 'places/templates/_places_table.jinja2'

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
                    fields_json=(
                        Markup(
                            json.dumps([dict(mDataProp=f) for f in fields])
                    ))
                ),
                self.request),
            charset=renderer[1],
            content_type=renderer[0][0]
        )

