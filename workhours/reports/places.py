
def places_reports():
    domains_by_count = (
        s.query( Place.netloc, func.count(Place.netloc).label('count'), )
            .group_by(Place.netloc)
            .order_by('-count')
