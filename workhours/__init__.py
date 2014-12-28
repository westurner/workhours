from pyramid.config import Configurator
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.session import UnencryptedCookieSessionFactoryConfig
from pyramid.renderers import JSONP
from pyramid.events import subscriber
from pyramid.events import NewRequest, ApplicationCreated

from sqlalchemy import engine_from_config
import workhours.models
from workhours.models.sql import initialize_sql
from workhours.models.es import initialize_esdb
from workhours.models.files import initialize_fs
#from .models.rdf import initialize_rdflib

import logging
log = logging.getLogger('workhours')



def _connect_sqldb(request):
    #conn = request.registry.dbsession() #
    sql_url = request.registry.settings.get('db_main.url').strip()

    if sql_url:
        engine = engine_from_config(
                request.registry.settings,
                'db_main.')

        def setup(*args):
            from workhours.models import Base
            from workhours.models.sql.tables import setup_mappers
            return initialize_sql(
                    engine=engine,
                    setup_mappers=setup_mappers,
                    Base=Base)
        request.set_property(setup, 'meta')

        conn = request.meta.Session # TODO
        # see: transaction.commit
        #def cleanup(_):
        #    log.debug('close sqldb')
        #    #conn.close()
        #    TODO: list session instances
        #request.add_finished_callback(cleanup)
        return conn
    raise Exception('db_main.url not configured')


def _connect_esdb(request):
    esdb_url = request.registry.settings.get('esdb.url').strip()
    if esdb_url:
        conn = initialize_esdb(esdb_url)
        def cleanup(_):
            log.debug('close esdb')
            conn.close()
        request.add_finished_callback(cleanup)
        return conn
    raise Exception('esdb.url not configured')


def _connect_fs(request):
    fs_url = request.registry.settings.get('fs.url').strip()
    if fs_url:
        fs = initialize_fs(fs_url)
        return fs
    raise Exception('fs.url not configured')


def _connect_rdflib(request):
    try:
        import rdflib
    except ImportError, e:
        log.error('import rdflib')

    rdf_url = request.registry.settings.get('rdflib.virtuoso_connstr')
    if rdf_url:
        conn = initialize_rdflib(
                    virtuoso_connstr=settings['rdflib.virtuoso_connstr'])
        return rdflib


#@subscriber(ApplicationCreated)
#def example_config(app):
#   pass

@subscriber(NewRequest)
def db_session_subscriber(event):
    request = event.request
    request.set_property(_connect_sqldb, 'db_session', reify=True)
    request.set_property(_connect_esdb, 'es_session', reify=True)
    #event.request.db_session = workhours.models.DBSession



def string_response_adapter(s):
    response = Response(s)
    response.content_type = 'text/html'
    return response



import os
from pyramid.response import FileResponse

def favicon_view(request):
    here = os.path.dirname(__file__)
    icon = os.path.join(here, 'static', 'favicon.ico')
    return FileResponse(icon, request=request)


def configure_routes(config):
    config.add_static_view('static', 'workhours:static')
    config.add_route('favicon', '/favicon.ico')
    config.add_view('workhours.favicon_view', name='favicon')

    config.include('deform_jinja2')

    ## Security Routes
    config.add_route('register', '/register')
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.add_route('user', '/user')

    ## Site Routes
    config.add_route('about', '/about')
    config.add_route('main', '/')

    ## API Routes
    config.include('pyramid_restler')
    config.enable_POST_tunneling()

    from workhours.events.views import EventsContextFactory
    from workhours.events.views import EventsRESTfulView
    config.add_restful_routes('api/events', EventsContextFactory,
                                    view=EventsRESTfulView)

    from workhours.places.models import PlacesContextFactory
    from workhours.places.views import PlacesRESTfulView
    config.add_restful_routes('api/places', PlacesContextFactory,
                                    view=PlacesRESTfulView)

    from workhours.reports.places import (
            DomainsContext,
            ProjectsContext,
            WikipediaPagesContext)
    from workhours.reports.views import (
            DomainsView,
            ProjectsView,
            WikipediaPagesView)
    config.add_restful_routes('reports/domains', DomainsContext,
                                    view=DomainsView)
    config.add_restful_routes('reports/projects', ProjectsContext,
                                    view=ProjectsView)
    config.add_restful_routes('reports/wikipedia', WikipediaPagesContext,
                                    view=WikipediaPagesView)

    #from workhours.forms import pyramid_csrf_demo
    config.add_route('pyramid_csrf_demo', '/formdemo')

    #config.add_route('sparql_query', '/sparql')
    #config.add_route('deniz', '/browse')
    config.include('pyramid_debugtoolbar')



def configure_renderers(config):
    config.add_renderer('jsonp', JSONP(param_name='callback'))


def configure_jinja2(config):
    from .site.templatefilters import skipautoescape, jsonify, jsonify_indent
    config.include('pyramid_jinja2')
    #config.add_jinja2_renderer('.jinja2')
    #config.add_jinja2_search_path('templates', name='.jinja2')

    env = config.get_jinja2_environment()
    if env is not None:
        # env.extensions
        env.filters['skipautoescape'] = skipautoescape
        env.filters['jsonify'] = jsonify
        env.filters['jsonify_indent'] = jsonify_indent
    else:
        logging.error('get_jinja2_environment() -> None')


def configure_auth_views(config):

    config.add_view('workhours.site.views.errors.http404',
            renderer='workhours:templates/http404.jinja2',
            context='pyramid.exceptions.NotFound')

    config.add_view('workhours.site.views.errors.http403',
            renderer='workhours:templates/http403.jinja2',
            context='pyramid.exceptions.Forbidden')

    config.testing_add_renderer('templates/login.jinja2')
    config.testing_add_renderer('templates/toolbar.jinja2')


def configure_app_views(config):
    #config.testing_add_renderer('templates/cloud.jinja2')
    #config.testing_add_renderer('templates/latest.jinja2')
    #config.testing_add_renderer('templates/sparql_query.jinja2')
    return config


def configure_test_app(config):
    configure_renderers(config)
    configure_jinja2(config)
    configure_auth_views(config)
    configure_app_views(config)
    configure_routes(config)
    return config


def configure_app(settings, authn_policy, authz_policy, session_factory):
    config = Configurator(
        settings=settings,
        root_factory='workhours.models.RootFactory',
        authentication_policy=authn_policy,
        authorization_policy=authz_policy,
        session_factory=session_factory,
    )
    config.add_translation_dirs('locale/')

    config.add_response_adapter(string_response_adapter, basestring)

    configure_test_app(config)

    config.add_subscriber('workhours.security.csrf.csrf_validation',
                          'pyramid.events.NewRequest')

    config.scan()
    configure_routes(config)

    return config


def main(global_config, **settings):
    """ This function returns a Workhours Pyramid WSGI application.
    """

    log.debug(settings)

    session_factory = UnencryptedCookieSessionFactoryConfig('secret')

    authn_policy = AuthTktAuthenticationPolicy('s0secret')
    authz_policy = ACLAuthorizationPolicy()

    settings.setdefault('jinja2.i18n.domain', 'workhours')

    config = configure_app(
        settings,
        authn_policy,
        authz_policy,
        session_factory)

    return config.make_wsgi_app()

app = main
