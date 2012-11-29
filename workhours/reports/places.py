import itertools
import sqlalchemy
from sqlalchemy import func
from urlparse import urlparse
from workhours.models import Place
from workhours.reports.models import ReportContext
from zope.interface import implements

class DomainsContext(ReportContext):
    _report_type = 'domains'

    def generate_report(self):
        return (
            self.request.db_session()
            .query( Place.netloc, func.count(Place.netloc).label('count'), )
                .group_by(Place.netloc)
                .order_by('-count') )


class ProjectsContext(ReportContext):
    _report_type = 'projects'
    RESERVED_WORDS = dict( (x,1) for x in (
        'settings', 'session', 'account', 'login', 'users', 'repo'
    ))


    def generate_report(self):
        query = (
            self.request.db_session()
            .query(Place)
                .filter(
                    Place.netloc.in_((
                        'bitbucket.org',
                        'github.com',
                        'code.google.com',))))

        def mapfn(obj):
            return (
                (obj.netloc,) + tuple(obj.path.split('/')[1:]),
                obj)

        def filterfn(obj):
            if (len(obj[0]) >= 3):
                if obj[0][0] in [u'github.com',u'bitbucket.org']:
                    return obj[0][1] not in self.RESERVED_WORDS
                elif obj[0][0] == u'code.google.com':
                    return obj[0][1] in [u'r',u'p']
            return False

        objects = itertools.imap(mapfn, query)
        objects = itertools.ifilter(filterfn, objects)

        for k,i in itertools.groupby(objects, lambda x: u'/'.join(x[0][0:3])):
            urls = [ (v[1].url, v[1].eventcount or 1) for v in i]
            yield k, [x[0] for x in urls], sum(x[1] for x in urls)


class WikipediaPagesContext(ReportContext):
    _report_type = 'wikipediapages'

    def generate_report(self):
        query = (
            self.request.db_session().query(Place)
                .filter(
                    Place.netloc.like('%wikipedia.org')))

        def mapfn(obj):
            return(
                (obj.netloc,) + tuple(obj.path.split('/')[1:]),
                obj)

        def filterfn(obj):
            return obj[0][0:1] and obj[0][1] == u'wiki'

        objects = itertools.imap(mapfn, query)
        objects = itertools.ifilter(filterfn, objects)

        for k,i in itertools.groupby(objects, lambda x: u'/'.join(x[0])):
            urls = [ (v[1].url, v[1].eventcount or 1) for v in i]
            yield k, [x[0] for x in urls], sum(x[1] for x in urls)

