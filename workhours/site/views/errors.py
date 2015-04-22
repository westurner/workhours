
#@view_config(context=HTTPNotFound, renderer='404.jinja')
def http404(request):
    request.response.status = 404
    return {'title': '404 Not Found',
            'errcode': '404'}

#@view_config(renderer='403.jinja')
def http403(request):
    request.response.status = 403
    return {'title': '403 Forbidden',
            'errcode': '403'}
