import math
import re
from datetime import date

from flask import Blueprint, jsonify, request
from sqlalchemy import select

from extensions import db
from models import Trip
from utils.auth import get_current_user, login_required
from utils.itinerary import generate_default_itinerary
from utils.responses import error_response

trips_bp = Blueprint('trips', __name__, url_prefix='/api/trips')

MAX_DESTINATION_LENGTH = 255
REQUIRED_FIELDS = ('destination', 'start_date', 'end_date')
UPDATABLE_FIELDS = REQUIRED_FIELDS + ('latitude', 'longitude', 'itinerary')
_DATE_RE = re.compile(r'\d{4}-\d{2}-\d{2}')


def _parse_date(value, field):
    if isinstance(value, str) and _DATE_RE.fullmatch(value):
        try:
            return date.fromisoformat(value), None
        except ValueError:
            pass
    return None, f'{field} must be a valid date in YYYY-MM-DD format'


def _parse_coordinate(value, field, limit):
    if value is None:
        return None, None
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or abs(value) > limit):
        return None, f'{field} must be a number between -{limit} and {limit}'
    return float(value), None


def parse_trip_data(data, trip=None):
    """Validate a payload and return (values, error).

    When `trip` is given this is an update: only supplied fields are validated and
    changed, but the result is checked against the trip's existing values.
    """
    if trip is None:
        for field in REQUIRED_FIELDS:
            if field not in data:
                return None, f'{field} is required'
    elif not any(field in data for field in UPDATABLE_FIELDS):
        return None, 'No updatable fields provided'

    values = {}

    if 'destination' in data:
        destination = data['destination']
        if (not isinstance(destination, str) or not destination.strip()
                or len(destination.strip()) > MAX_DESTINATION_LENGTH):
            return None, f'destination must be a non-empty string of at most {MAX_DESTINATION_LENGTH} characters'
        values['destination'] = destination.strip()

    for field in ('start_date', 'end_date'):
        if field in data:
            values[field], error = _parse_date(data[field], field)
            if error:
                return None, error

    for field, limit in (('latitude', 90), ('longitude', 180)):
        if field in data:
            values[field], error = _parse_coordinate(data[field], field, limit)
            if error:
                return None, error

    if 'itinerary' in data:
        if not isinstance(data['itinerary'], (list, dict)):
            return None, 'itinerary must be a JSON array or object'
        values['itinerary'] = data['itinerary']

    def effective(field):
        return values[field] if field in values else getattr(trip, field, None)

    if effective('end_date') < effective('start_date'):
        return None, 'end_date must not be before start_date'
    if (effective('latitude') is None) != (effective('longitude') is None):
        return None, 'latitude and longitude must be provided together'

    return values, None


def _get_owned_trip(trip_id):
    return db.session.execute(
        select(Trip).filter_by(id=trip_id, user_id=get_current_user().id)
    ).scalar_one_or_none()


def _trip_not_found():
    return error_response('Trip not found', 404)


@trips_bp.route('', methods=['POST'], strict_slashes=False)
@login_required
def create_trip():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return error_response('Request body must be a JSON object', 400)

    values, error = parse_trip_data(data)
    if error:
        return error_response(error, 400)

    if 'itinerary' not in data:
        values['itinerary'] = generate_default_itinerary(values['start_date'], values['end_date'])

    trip = Trip(user_id=get_current_user().id, **values)
    db.session.add(trip)
    db.session.commit()
    return jsonify({'trip': trip.to_dict()}), 201


@trips_bp.route('', methods=['GET'], strict_slashes=False)
@login_required
def list_trips():
    trips = db.session.execute(
        select(Trip).filter_by(user_id=get_current_user().id).order_by(Trip.start_date, Trip.id)
    ).scalars()
    return jsonify({'trips': [trip.to_dict() for trip in trips]})


@trips_bp.route('/<int:trip_id>', methods=['GET'], strict_slashes=False)
@login_required
def get_trip(trip_id):
    trip = _get_owned_trip(trip_id)
    if trip is None:
        return _trip_not_found()
    return jsonify({'trip': trip.to_dict()})


@trips_bp.route('/<int:trip_id>', methods=['PUT', 'PATCH'], strict_slashes=False)
@login_required
def update_trip(trip_id):
    trip = _get_owned_trip(trip_id)
    if trip is None:
        return _trip_not_found()

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return error_response('Request body must be a JSON object', 400)

    values, error = parse_trip_data(data, trip)
    if error:
        return error_response(error, 400)

    for field, value in values.items():
        setattr(trip, field, value)
    db.session.commit()
    return jsonify({'trip': trip.to_dict()})


@trips_bp.route('/<int:trip_id>', methods=['DELETE'], strict_slashes=False)
@login_required
def delete_trip(trip_id):
    trip = _get_owned_trip(trip_id)
    if trip is None:
        return _trip_not_found()

    db.session.delete(trip)
    db.session.commit()
    return '', 204
