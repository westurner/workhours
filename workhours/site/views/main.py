from pyramid.view import view_config

@view_config(route_name="main", renderer="templates/main.jinja2")
def main_view(request):
    return {
        "title": "Workhours",
        "username": request.authenticated_userid,
    }
    # from ..security.views import login_form_view
    #'login_form': login_form_view(request)}
