from pyramid_restler.model import SQLAlchemyORMContext

from workhours.models import Report, ReportType
import transaction

class ReportContext(SQLAlchemyORMContext):
    entity = Report
    default_fields = ('id','report_type_id','title','data')

    def member_to_dict(self, member, fields=None):
        if fields is None:
            fields = self.default_fields
        if isinstance(member, (tuple, list)):
            return member
        return SQLAlchemyORMContext.member_to_dict(self, member, fields)

    def _create_report_type(self):
        s = self.request.db_session()
        rtype = ReportType(self._report_type)
        s.add(rtype)
        s.flush()
        return rtype

    def create_report(self):
        s = self.request.db_session()
        collection = list(self.generate_report())
        rtype = self._create_report_type()
        r = Report(rtype.id, self._report_type,{})
        r.data['results'] = collection
        s.add(r)
        s.flush()
        return r

    def get_collection(self, *args, **kwargs):
        return self.create_report()
