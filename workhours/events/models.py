#from pyramid.renderers import render
#from pyramid.decorator import reify
#from pyramid.response import Response
from pyramid_restler.model import SQLAlchemyORMContext
import sqlalchemy
from sqlalchemy import orm
#from pyramid_restler.view import RESTfulView
#from collections import OrderedDict

from workhours.models import Event
from workhours.models.json import DefaultJSONEncoder

import logging

log = logging.getLogger('.events.models')

class EventsContextFactory(SQLAlchemyORMContext):
    json_encoder = DefaultJSONEncoder
    entity = Event

    default_fields = ('id','date','type','url','title')

    #def get_collection(self, *args, **kwargs):
#
        #return super(EventsContextFactory, self).get_collection(*args, **kwargs)
    #    return SQLAlchemyORMContext.get_collection(self, *args, **kwargs)

    def get_collection(self, distinct=False, order_by=None, limit=None,
                       offset=None, filters=None, **kwargs):
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
        q.options(orm.joinedload_all('task.queue'))

        # Apply "global" (i.e., every request) filters
        if hasattr(self, 'filters'):
            for f in self.filters:
                q = q.filter(f)

        for k, v in (filters or {}).items():
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
        if search is not None:
            q = q.filter(
                        ( self.entity.url.like(search) )
                    |   ( self.entity.title.like(search) )
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
            q = q.limit(limit)

        return q.all()

    def count(self):
        # TODO: ...
        return self.request.db_session.query(self.entity).count()

    def wrap_json_obj(self, obj):
        result_count=len(obj)
        total_count = self.count()
        return dict(
            results=obj,
            result_count=result_count,
            iTotalRecords=total_count,
            iTotalDisplayRecords=total_count, # TODO:
        )
