import itertools
import sqlalchemy
from sqlalchemy import func
from urllib.parse import urlparse
from workhours.models import Place
from workhours.reports.models import ReportContext
from zope.interface import implements
from workhours.future import OrderedDict

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
                if obj[0][0] in ['github.com','bitbucket.org']:
                    return obj[0][1] not in self.RESERVED_WORDS
                elif obj[0][0] == 'code.google.com':
                    return obj[0][1] in ['r','p']
            return False

        objects = map(mapfn, query)
        objects = filter(filterfn, objects)

        for k,i in itertools.groupby(objects, lambda x: '/'.join(x[0][0:3])):
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
            return (
                (obj.netloc,) + tuple(obj.path.split('/')[1:]),
                obj)

        def filterfn(obj):
            return obj[0][0:1] and obj[0][1] == 'wiki'

        objects = map(mapfn, query.all())
        objects = filter(filterfn, objects)

        for k,objiter in itertools.groupby(objects, lambda x: '/'.join(x[0])):
            places = list(objiter)
            urls = [
                (
                    obj[1].url,
                    len(obj[1].events) or 1, # FIXME
                    obj) # TODO.. SQL
                for obj in places]
            yield OrderedDict((
                ('url', k),

                ('urls', len(urls) > 1 and [x[0] for x in urls]),
                ('count', sum(x[1] for x in urls)),
                ('events', [str(place[-1].events) for place in places]),
                #[str(e) for e in x[0].events]
            ))

class QuestionsContext(ReportContext):
    _report_type = 'questions'

    def generate_report(self):
        query = (
            self.request.db_Session().query(Place)
                .filter(
                    Place.netloc.in_(
                        'stackoverflow.com',
                        'serverfault.com',
                        'superuser.com',
                        'webmasters.stackexchange.com',
                        'quora.com',
                    )))

        return query.all()
