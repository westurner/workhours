#!/usr/bin/env python
"""
workhours

- ``workhours.main`` WSGI app factory entrypoint
- ``workhours.configure_test_app`` (testing setup)

"""

from pyramid.config import Configurator
from pyramid import authentication, authorization
from pyramid.renderers import JSONP
from pyramid.events import subscriber
from pyramid.events import NewRequest, ApplicationCreated

from sqlalchemy import engine_from_config
from sqlalchemy.orm import sessionmaker
from .resource import APIRoot
from .security import get_principals
from .models import User
from configparser import ConfigParser


from .models.sql import initialize_sql
from .models.es import initialize_esdb
from .models.files import initialize_fs
#from .models.rdf import initialize_rdflib

import logging
log = logging.getLogger(__name__)

def db(request):
    """every request will have a session associated with it. and will
    automatically rollback if there's any exception in dealing with
    the request
    """
    maker = request.registry.dbmaker
    session = maker()

    def cleanup(request):
        if request.exception is not None:
            session.rollback()
        else:
            session.commit()
        session.close()

    request.add_finished_callback(cleanup)

    return session

def authenticated_user(request):
    def x():
        return request.db.query(User).filter_by(id=request.authenticated_userid).first()
    return x

def config_static(config):
    config.add_static_view('static', 'static', cache_max_age=3600)

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
    except ImportError as e:
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


def config_jinja2(config):
    config.include('pyramid_jinja2')
    config.add_jinja2_renderer('.html')
    config.add_jinja2_search_path('templates', name='.html')

    from .site.templatefilters import skipautoescape, jsonify, jsonify_indent
    config.commit()
    env = config.get_jinja2_environment()
    env.filters['skipautoescape'] = skipautoescape
    env.filters['jsonify'] = jsonify
    env.filters['jsonify_indent'] = jsonify_indent


def config_debugtoolber(config):
    config.include('pyramid_debugtoolbar')


def config_mailer(config):
    config.include('pyramid_marrowmailer')
    config.include('pyramid_tm')


def config_db(config, settings, prefix="sqlalchemy."):
    # configure database with variables sqlalchemy.*
    engine = engine_from_config(settings, prefix=prefix)
    config.registry.dbmaker = sessionmaker(bind=engine)

    # add db session to request
    config.add_request_method(db, reify=True)

    ## workhours
    config.add_request_method(_connect_sqldb,
                              'db_session',
                              property=True,
                              reify=True)
    config.add_request_method(_connect_esdb,
                              'es_session',
                              property=True,
                              reify=True)

import os
from pyramid.response import FileResponse

def favicon_view(request):
    here = os.path.dirname(__file__)
    icon = os.path.join(here, 'static', 'favicon.ico')
    return FileResponse(icon, request=request)


def config_routes(config):
    ## Site Routes
    config.add_route('about', '/about')
    config.add_route('home', '/home')
    config.add_route('main', '/')
    config.add_route('favicon', '/favicon.ico')
    config.add_view('workhours.favicon_view', name='favicon')

    config.include('deform_jinja2')

    ## Security Routes
    #config.add_route('register', '/register')
    #config.add_route('login', '/login')
    #config.add_route('logout', '/logout')
    #config.add_route('user', '/user')

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

    config.add_route("api", '/api/*traverse', factory=APIRoot)
    config.scan()


def config_error_pages(config):
    config.add_view('workhours.site.views.errors.http404',
            renderer='workhours:templates/http404.jinja2',
            context='pyramid.exceptions.NotFound')

    config.add_view('workhours.site.views.errors.http403',
            renderer='workhours:templates/http403.jinja2',
            context='pyramid.exceptions.Forbidden')




def config_renderers(config):
    config.add_renderer('jsonp', JSONP(param_name='callback'))



from pyramid.session import SignedCookieSessionFactory

DEFAULT_AUTH_SECRET = "supersecret"
DEFAULT_COOKIE_SECRET = "crazysecret"

def config_auth_policy(config, settings):
    policy = authentication.AuthTktAuthenticationPolicy(
        settings.get('auth_secret', DEFAULT_AUTH_SECRET),
        get_principals,
        cookie_name="workhours_auth",
        hashalg="sha512",)
    config.set_authorization_policy(authorization.ACLAuthorizationPolicy())
    config.set_authentication_policy(policy)

    my_session_factory = SignedCookieSessionFactory(
        settings.get('auth_secret', DEFAULT_COOKIE_SECRET))
    config.set_session_factory(my_session_factory)


def config_secrets(settings):
    if "secrets" in settings:
        try:
            config = ConfigParser()
            config.read(settings["secrets"])
            settings.update(config.items("secrets"))
        except:
            log.warn("secrets were specificed in the configuration but could not be read\n\n%s" % settings.get("secrets", ""), exc_info=1)


def config_settings(settings):
    if settings is None:
        raise Exception()
        #settings = config.registry.settings
        settings = {
            'sqlalchemy.url': 'sqlite:///',
            'mail.transport.use': 'logging',
        }
    settings.setdefault('jinja2.i18n.domain', 'workhours')
    return settings


def config_app(config, settings=None, debug=False):
    settings = config_settings(settings)
    settings = config.registry.settings
    print(settings)
    config_static(config)
    config_jinja2(config)
    config_error_pages(config)
    config_db(config, settings)
    config_routes(config)
    config_auth_policy(config, settings)
    config_mailer(config)
    config.add_request_method(authenticated_user, reify=True)
    if debug:
        config_debugtoolber(config)


def configure_test_app(config, settings=None, debug=True):
    if settings is None:
        from workhours.testing import test_settings
        settings = test_settings
    return config_app(config, settings=settings, debug=debug)


def main(global_config, **settings):
    config_secrets(settings)
    config = Configurator(settings=settings)
    config_app(config, settings=settings, debug=True)
    return config.make_wsgi_app()
