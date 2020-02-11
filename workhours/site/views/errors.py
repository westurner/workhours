def http404(request):
    return {"title": "404 Not Found", "errcode": "404"}


def http403(request):
    return {"title": "403 Forbidden", "errcode": "403"}
