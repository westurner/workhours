
def build_bookmarks_config():
    for p in path.path('~/notes/data/bookmarks').expanduser().listdir():
        if p.endswith('json'):
            yield('bookmarks.json', p)
        elif p.endswith('html'):
            yield('bookmarks.html',p)
