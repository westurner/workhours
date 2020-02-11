#!/usr/bin/env python
# encoding: utf-8

"""
datatables
"""

from pyramid.renderers import render

import colander

class SearchForm(colander.MappingSchema):
    iDisplayStart = colander.SchemaNode(colander.Integer())
    iDisplayLength = colander.SchemaNode(colander.Integer())
    sSearch = colander.SchemaNode(colander.String()) #


# TODO
def _get_param(request, param, _type=str):
    try:
        value = request.params.get(param)
        if value is None:
            return None
        return _type(value)
    except Exception as e:
        return None

from workhours.future import OrderedDict
def read_datatables_params(request):
    r = OrderedDict()

    r['offset'] = _get_param(request, 'iDisplayStart', int)
    r['limit'] = _get_param(request, 'iDisplayLength', int)
    r['order_by'] = _get_param(request, 'iSortCol_0', int)
    #if r['order_by']:
    #    r['order_by'] = self.context.default_fields[r['order_by']]
    r['sort_dir'] = _get_param(request, 'sSortDir_0', str)

    r['search'] = _get_param(request, 'sSearch', str) # TODO
    return OrderedDict( (k,v) for (k,v) in r.items() if v is not None)


from workhours import models
from sqlalchemy import sql
def build_query(request, model=models.Event):
    #read_params(request.urlstr)

    s = request.db_session
    query = s.query(model)

    # TODO sanitize for SQL

    # sort column: TODO support multiple columns
    sortcol = _get_param(request, 'iSortCol_0', int)
    # TODO
    if sortcol:
        query = query.order_by(sortcol)

    # iDisplayStart = OFFSET
    offset = _get_param(request, 'iDisplayStart', int)
    if offset:
        query = query.offset(offset)

    # iDisplayLength = -1 or LIMIT
    limit = _get_param(request, 'iDisplayLength', int)
    if limit:
        query = query.limit(limit)



    # sSearch = LIKE
    search = _get_param(request, 'sSearch', str)
    if search:
        query = query.filter(
                    ( model.url.like(search) )
                |   ( model.title.like(search) )
        )

    return query
    #bRegex = TODO

    #sSearch_[i] = filter(like(cls._fields[i]))
    #bRegex_[i] = # TODO



def datatables_view(request):
    query = build_query(request)
    objects = query.all()
    return render('models/templates/_table.jinja2',
                    dict(value=objects),
                    request)




"""


from jquery.dataTables.js

.. code-block: javascript ::


		/*
		 * Function: _fnAjaxUpdate
		 * Purpose:  Update the table using an Ajax call
		 * Returns:  bool: block the table drawing or not
		 * Inputs:   object:oSettings - dataTables settings object
		 */
		function _fnAjaxUpdate( oSettings )
		{
			if ( oSettings.bAjaxDataGet )
			{
				_fnProcessingDisplay( oSettings, true );
				var iColumns = oSettings.aoColumns.length;
				var aoData = [];
				var i;

				/* Paging and general */
				oSettings.iDraw++;
				aoData.push( { "name": "sEcho",          "value": oSettings.iDraw } );
				aoData.push( { "name": "iColumns",       "value": iColumns } );
				aoData.push( { "name": "sColumns",       "value": _fnColumnOrdering(oSettings) } );
				aoData.push( { "name": "iDisplayStart",  "value": oSettings._iDisplayStart } );
				aoData.push( { "name": "iDisplayLength", "value": oSettings.oFeatures.bPaginate !== false ?
					oSettings._iDisplayLength : -1 } );

				/* Filtering */
				if ( oSettings.oFeatures.bFilter !== false )
				{
					aoData.push( { "name": "sSearch", "value": oSettings.oPreviousSearch.sSearch } );
					aoData.push( { "name": "bRegex",  "value": oSettings.oPreviousSearch.bRegex } );
					for ( i=0 ; i<iColumns ; i++ )
					{
						aoData.push( { "name": "sSearch_"+i,     "value": oSettings.aoPreSearchCols[i].sSearch } );
						aoData.push( { "name": "bRegex_"+i,      "value": oSettings.aoPreSearchCols[i].bRegex } );
						aoData.push( { "name": "bSearchable_"+i, "value": oSettings.aoColumns[i].bSearchable } );
					}
				}

				/* Sorting */
				if ( oSettings.oFeatures.bSort !== false )
				{
					var iFixed = oSettings.aaSortingFixed !== null ? oSettings.aaSortingFixed.length : 0;
					var iUser = oSettings.aaSorting.length;
					aoData.push( { "name": "iSortingCols",   "value": iFixed+iUser } );
					for ( i=0 ; i<iFixed ; i++ )
					{
						aoData.push( { "name": "iSortCol_"+i,  "value": oSettings.aaSortingFixed[i][0] } );
						aoData.push( { "name": "sSortDir_"+i,  "value": oSettings.aaSortingFixed[i][1] } );
					}

					for ( i=0 ; i<iUser ; i++ )
					{
						aoData.push( { "name": "iSortCol_"+(i+iFixed),  "value": oSettings.aaSorting[i][0] } );
						aoData.push( { "name": "sSortDir_"+(i+iFixed),  "value": oSettings.aaSorting[i][1] } );
					}

					for ( i=0 ; i<iColumns ; i++ )
					{
						aoData.push( { "name": "bSortable_"+i,  "value": oSettings.aoColumns[i].bSortable } );
					}
				}

				oSettings.fnServerData.call( oSettings.oInstance, oSettings.sAjaxSource, aoData,
					function(json) {
						_fnAjaxUpdateDraw( oSettings, json );
					}, oSettings );
				return false;
			}
			else
			{
				return true;
			}
		}

"""
