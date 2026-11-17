from datetime import timedelta

# Longer trips get no template, so a bad date range can't create a huge list
MAX_ITINERARY_DAYS = 365


def generate_default_itinerary(start_date, end_date):
    """Return one empty day entry per day of the trip, both dates included.

    Returns an empty list if the dates are out of order or the trip is longer
    than MAX_ITINERARY_DAYS.
    """
    total_days = (end_date - start_date).days + 1
    if total_days < 1 or total_days > MAX_ITINERARY_DAYS:
        return []

    return [
        {
            'day': index + 1,
            'date': (start_date + timedelta(days=index)).isoformat(),
            'title': f'Day {index + 1}',
            'activities': [],
            'notes': '',
        }
        for index in range(total_days)
    ]
