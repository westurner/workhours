#from pyramid.renderers import render
#from pyramid.decorator import reify
#from pyramid.response import Response
from workhours.models.context import WorkhoursORMContext
#from pyramid_restler.view import RESTfulView
#from workhours.future import OrderedDict

from workhours.models import Place
import sqlalchemy
from sqlalchemy import orm
from sqlalchemy.sql import func

import logging

log = logging.getLogger('workhours.places.models')

class PlacesContextFactory(WorkhoursORMContext):
    entity = Place
    default_fields = ('_id','url','netloc','eventcount','title')

    def get_collection(self, distinct=False, order_by=None, limit=None,
                       offset=None, filters=None,
                       **kwargs):
        """Get the entire collection or a subset of it.

        By default, this will fetch all records for :attr:`entity`. Various
        types of filtering can be applied to instead fetch a subset.

        The simplest "filter" is LIMIT. This can be used by itself or in
        conjunction with other filters.

        There are two types of filters that can be applied: global filters
        that will be applied to *all* queries of this collection and
        per-query filters.

        Global filters are specified by the :attr:`filters` attribute.
        Generally, it will be a class-level attribute, but an instance can
        also set `filters` (perhaps to disable the global defaults). The
        items in the `filters` list can be anything that can be passed into
        SQLAlchemy's `Query.filter` method.

        Per-query filters are specified by passing a `dict` of filters via
        the ``filters`` keyword arg. A key in the `dict` names either a
        method on the entity that is named as {key}_filter *or* an `entity`
        attribute. In the first case, the {key}_filter method is expected to
        return a filter that can be passed into `Query.filter`. In the
        second case, a simple `filter_by(key=value)` is applied to the
        query.

        """
        q = self.session.query(self.entity)

        # XXX: Handle joined loads here?
        q.options(orm.joinedload(self.entity.events))

        # Apply "global" (i.e., every request) filters
        if hasattr(self, 'filters'):
            for f in self.filters:
                q = q.filter(f)

        for k, v in list((filters or {}).items()):
            #v = self.convert_param(k, v)
            filter_method = getattr(self.entity, '{0}_filter'.format(k), None)
            if filter_method is not None:
                # Prefer a method that returns something that can be passed
                # into `Query.filter()`.
                q = q.filter(filter_method(v))
            else:
                q = q.filter_by(**{k: v})

        if distinct:
            q = q.distinct()
        search = kwargs.get('search')
        if search is not None and search is not '':
            if '%' not in search:
                search = '%%%s%%' % search
            q = q.filter(
                        ( self.entity.url.like(search) )
                    |   ( self.entity.netloc.like(search) )
            )
        if order_by is not None:
            if isinstance(order_by, int): # numeric?
                order_by = getattr(self.entity, self.default_fields[order_by])
            else:
                raise AttributeError()

            sort_dir = kwargs.get('sort_dir')
            if sort_dir == 'desc':
                order_by = sqlalchemy.desc(order_by)

            log.debug("ordering by: %s : %s" % (order_by, sort_dir))

            q = q.order_by(order_by)
        if offset is not None:
            q = q.offset(offset)
        if limit is not None:
            log.debug("limit: %r" % limit)
            q = q.limit(limit)

        return q

    def get_member(self, id):
        q = self.session.query(self.entity)
        intval = None
        try:
            intval = int(id)
            return q.get(id)
        except Exception as e:
            log.debug("not an int: %r" % id)
            if hasattr(id, '__contains__') and '://' in id:
                return q.filter(self.entity.url == id).one()
            return q.get(id)

    def count(self):
        # TODO: ...
        return (
            self.request
                .db_session
                .query(
                    func.count(self.entity._id)
                ).one() )

    def wrap_json_obj(self, obj):
        result_count=len(obj)
        total_count = self.count()[0]
        return dict(
            results=obj,
            result_count=result_count,
            iTotalRecords=total_count,
            iTotalDisplayRecords=total_count, # TODO:
        )
