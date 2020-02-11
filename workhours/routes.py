from pyramid.events import NewRequest
from pyramid.httpexceptions import HTTPBadRequest

from pyramid_restler.view import RESTfulView


def add_restful_routes(
    self, name, factory, view=RESTfulView, route_kw=None, view_kw=None
):
    """Add a set of RESTful routes for an entity.

    URL patterns for an entity are mapped to a set of views encapsulated in
    a view class. The view class interacts with the model through a context
    adapter that knows the particulars of that model.

    To use this directive in your application, first call
    `config.include('pyramid_restler')` somewhere in your application's
    `main` function, then call `config.add_restful_routes(...)`.

    ``name`` is used as the base name for all route names and patterns. In
    route names, it will be used as-is. In route patterns, underscores will
    be converted to dashes.

    ``factory`` is the model adapter that the view interacts with. It can be
    any class that implements the :class:`pyramid_restler.interfaces.IContext`
    interface.

    ``view`` must be a view class that implements the
    :class:`pyramid_restler.interfaces.IView` interface.

    Additional route and view keyword args can be passed directly through to
    all `add_route` and `add_view` calls. Pass ``route_kw`` and/or ``view_kw``
    as dictionaries to do so.

    """
    route_kw = {} if route_kw is None else route_kw
    view_kw = {} if view_kw is None else view_kw
    view_kw.setdefault("http_cache", 0)

    subs = dict(
        name=name,
        slug=name.replace("_", "-"),
        id="{id:.*}",
        renderer="{renderer}",
    )

    def add_route(name, pattern, attr, method):
        name = name.format(**subs)
        pattern = pattern.format(**subs)
        self.add_route(
            name, pattern, factory=factory, request_method=method, **route_kw
        )
        self.add_view(
            view=view,
            attr=attr,
            route_name=name,
            request_method=method,
            **view_kw
        )

    # Get collection
    add_route(
        "get_{name}_collection_rendered",
        "/{slug}.{renderer}",
        "get_collection",
        "GET",
    )
    add_route("get_{name}_collection", "/{slug}", "get_collection", "GET")

    # Get member
    add_route(
        "get_{name}_rendered", "/{slug}/{id}/.{renderer}", "get_member", "GET"
    )
    add_route("get_{name}", "/{slug}/{id}", "get_member", "GET")

    # Create member
    add_route("create_{name}", "/{slug}", "create_member", "POST")

    # Update member
    add_route("update_{name}", "/{slug}/{id}", "update_member", "PUT")

    # Delete member
    add_route("delete_{name}", "/{slug}/{id}", "delete_member", "DELETE")
