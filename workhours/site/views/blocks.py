from pyramid.renderers import render
from pyramid.security import authenticated_userid

def toolbar_view(request):
    viewer_username = authenticated_userid(request)
    return render('templates/toolbar.jinja2',
                    {'viewer_username': viewer_username},
                    request)
