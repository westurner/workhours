from pyramid_restler.model import SQLAlchemyORMContext

from workhours.models import Report, ReportType
import transaction

class ReportTypeContext(SQLAlchemyORMContext):
    entity = ReportType
    default_fields = ('_id',)

class ReportContext(SQLAlchemyORMContext):
    entity = Report
    default_fields = ('_id','report_type_id','title','data')

    _report_label = 'ReportContext'

    def member_to_dict(self, member, fields=None):
        if fields is None:
            fields = self.default_fields
        if isinstance(member, (tuple, list)):
            return member
        return SQLAlchemyORMContext.member_to_dict(self, member, fields)

    def _create_report_type(self):
        s = self.request.db_session()
        rtype = (
            s.query(ReportType)
                .filter(ReportType.label==self._report_type)
                .all() )
        rtype_len = len(rtype)
        if rtype_len == 0:
            rtype = ReportType(label=self._report_label)
            s.add(rtype)
            return rtype
        elif rtype_len == 1:
            rtype = rtype[0]
            return rtype
        elif len(rtype) != 1:
            raise Exception()

        return rtype

    def create_report(self):
        s = self.request.db_session()
        collection = list(self.generate_report())
        rtype = self._create_report_type()
        r = Report(rtype._id, self._report_type,{})
        r.data['results'] = collection
        s.add(r)
        return r

    def get_collection(self, *args, **kwargs):
        return self.create_report()
