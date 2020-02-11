from pyramid.view import view_config

# from ...shootout.views import cloud_view
# from ...shootout.views import latest_view
# from ...security.views import login_form_view

from .blocks import toolbar_view


@view_config(
    permission="view", route_name="about", renderer="templates/about.jinja2"
)
def about_view(request):
    return {
        "toolbar": toolbar_view(request),
        #'cloud': cloud_view(request),
        #'latest': latest_view(request),
        #'login_form': login_form_view(request),
    }
