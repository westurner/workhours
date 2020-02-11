import math
from operator import itemgetter

import formencode

# from pyramid_simpleform import Form
# from pyramid_simpleform.renderers import FormRenderer

from pyramid.view import view_config
from pyramid.url import route_url
from pyramid.renderers import render
from pyramid.httpexceptions import HTTPMovedPermanently
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPNotFound
from pyramid.security import authenticated_userid, remember, forget

# i178n
from pyramid.i18n import TranslationStringFactory

_ = TranslationStringFactory("workhours")

from workhours.models import DBSession
from workhours.models import User

# from workhours.shootout.models import Tag, Idea


# def login_form_view(request):
# logged_in = authenticated_userid(request)
# return render('templates/login.pt', {'loggedin': logged_in}, request)


# def latest_view(request):
# latest = Idea.ideas_bunch(Idea.idea_id.desc())
# return render('templates/latest.pt', {'latest': latest}, request)

# def cloud_view(request):
# totalcounts = []
# for tag in Tag.tag_counts():
# weight = int((math.log(tag[1] or 1) * 4) + 10)
# totalcounts.append((tag[0], tag[1], weight))
# cloud = sorted(totalcounts, key=itemgetter(0))

# return render('templates/cloud.pt', {'cloud': cloud}, request)
