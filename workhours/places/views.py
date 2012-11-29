from pyramid.renderers import render
from pyramid.decorator import reify
from pyramid.response import Response
from pyramid_restler.view import RESTfulView
from collections import OrderedDict

from workhours.models import Place, DBSession

import logging

log = logging.getLogger('.places.views')
from workhours.models.html.datatables import read_datatables_params
from pprint import pformat
from sqlalchemy import orm
from workhours.places.models import PlacesContextFactory

from jinja2 import Markup
import workhours.models.json as json

class PlacesRESTfulView(RESTfulView):
    #def render_to_response(self, member):
    #    raise Exception(member)

    _entity_name = 'place'
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
        fields = self.context.default_fields

        # a model instance
        if not hasattr(value, '__iter__'):
            value = [value]
            title = u"Place: %s" % self.request.matchdict['id']

        # an iterable
        return dict(
            body=render('places/templates/_places_table.jinja2',
                dict(
                    value=value,
                    fields=fields,
                    table_id='places',
                    title=title,
                    wrap=self.wrap,
                    js_links="datatable/js/jquery.dataTables.min.js",
                    fields_json=Markup(json.dumps([dict(mDataProp=f) for f in fields]))
                ),
                self.request),
            charset=renderer[1],
            content_type=renderer[0][0]
        )

