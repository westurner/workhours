from pyramid.renderers import render


def toolbar_view(request):
    viewer_username = request.authenticated_userid
    return render(
        "templates/toolbar.jinja2",
        {"viewer_username": viewer_username},
        request,
    )
