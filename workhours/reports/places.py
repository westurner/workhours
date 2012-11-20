
from workhours.models import Place

def domains_by_count(s):
    return (
        s.query( Place.netloc, func.count(Place.netloc).label('count'), )
            .group_by(Place.netloc)
            .order_by('-count') )
