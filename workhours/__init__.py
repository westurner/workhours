from pyramid.config import Configurator
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.session import UnencryptedCookieSessionFactoryConfig
from pyramid.renderers import JSONP

from sqlalchemy import engine_from_config
from .models.sql import initialize_sql
#from .models.rdf import initialize_rdflib

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'db_main.')
    initialize_sql(engine)

    #data_engine = engine_from_config(settings, 'db_data.')
    #initialize_sql(data_engine)

    #initialize_rdflib(virtuoso_connstr=settings['rdflib.virtuoso_connstr'])

    session_factory = UnencryptedCookieSessionFactoryConfig('secret')

    authn_policy = AuthTktAuthenticationPolicy('s0secret')
    authz_policy = ACLAuthorizationPolicy()

    settings.setdefault('jinja2.i18n.domain', 'workhours')

    config = configure_app(settings,
            authn_policy,
            authz_policy,
            session_factory)

    config.scan()
    return config.make_wsgi_app()


def configure_app(settings, authn_policy, authz_policy, session_factory):
    config = Configurator(
        settings=settings,
        root_factory='workhours.models.RootFactory',
        authentication_policy=authn_policy,
        authorization_policy=authz_policy,
        session_factory=session_factory
    )
    config.add_translation_dirs('locale/')

    _register_common_templates(config)
    config.add_subscriber('workhours.security.csrf.csrf_validation',
                          'pyramid.events.NewRequest')
    _register_routes(config)
    return config


def _register_routes(config):
    config.add_static_view('static', 'workhours:static')
    config.include('deform_jinja2')

    config.add_route('register', '/register')
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.add_route('user', '/user')
    config.add_route('about', '/about')
    config.add_route('main', '/')


    config.include('pyramid_restler')
    config.enable_POST_tunneling()

    from .events.views import EventsContextFactory
    from .events.views import EventsRESTfulView
    config.add_restful_routes('event', EventsContextFactory,
                                    view=EventsRESTfulView)

    #from workhours.forms import pyramid_csrf_demo
    config.add_route('pyramid_csrf_demo', '/formdemo')

    #config.add_route('sparql_query', '/sparql')
    #config.add_route('deniz', '/browse')
    config.include('pyramid_debugtoolbar')


from .site.templatefilters import skipautoescape, jsonify

def _register_common_templates(config):
    config.add_renderer('jsonp', JSONP(param_name='callback'))

    config.include('pyramid_jinja2')
    env = config.get_jinja2_environment()
    env.filters['skipautoescape'] = skipautoescape
    env.filters['jsonify'] = jsonify

    config.add_view('workhours.site.views.errors.http404',
            renderer='workhours:templates/http404.jinja2',
            context='pyramid.exceptions.NotFound')

    config.add_view('workhours.site.views.errors.http403',
            renderer='workhours:templates/http403.jinja2',
            context='pyramid.exceptions.Forbidden')

    config.testing_add_renderer('templates/login.jinja2')
    config.testing_add_renderer('templates/toolbar.jinja2')
    #config.testing_add_renderer('templates/cloud.jinja2')
    #config.testing_add_renderer('templates/latest.jinja2')
    #config.testing_add_renderer('templates/sparql_query.jinja2')




import logging
log = logging.getLogger()

class Namespace(object):
    pass

