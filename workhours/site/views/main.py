from pyramid.view import view_config

from pyramid.security import authenticated_userid


@view_config(route_name='main', renderer='templates/main.jinja2')
def main_view(request):
    return {
        'title': 'testapp',
        'username':authenticated_userid(request),
        }
        #from ..security.views import login_form_view
        #'login_form': login_form_view(request)}
