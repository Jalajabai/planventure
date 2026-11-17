from unittest.mock import patch

from extensions import db
from models import Trip
from routes.trips import trips_bp
from test_auth import AuthTestCase

TRIPS = '/api/trips'
VALID_TRIP = {
    'destination': 'Lisbon',
    'start_date': '2027-05-01',
    'end_date': '2027-05-08',
}


class TripRoutesTestCase(AuthTestCase):
    def setUp(self):
        # Minimum bcrypt cost keeps per-test signups fast
        patcher = patch('utils.security.DEFAULT_ROUNDS', 4)
        patcher.start()
        self.addCleanup(patcher.stop)
        super().setUp()
        self.app.register_blueprint(trips_bp)
        self.token = self.sign_up('owner@example.com')
        self.other_token = self.sign_up('other@example.com')

    def sign_up(self, email):
        response = self.register({'email': email, 'password': 'password123'})
        return response.get_json()['access_token']

    def call(self, method, path, payload=None, token=None):
        headers = {'Authorization': f'Bearer {token or self.token}'}
        return self.client.open(path, method=method, json=payload, headers=headers)

    def create_trip(self, token=None, **overrides):
        response = self.call('POST', TRIPS, {**VALID_TRIP, **overrides}, token)
        self.assertEqual(response.status_code, 201, response.get_json())
        return response.get_json()['trip']


class TripAuthTests(TripRoutesTestCase):
    def test_all_endpoints_require_authentication(self):
        trip_id = self.create_trip()['id']
        for method, path in (('POST', TRIPS), ('GET', TRIPS), ('GET', f'{TRIPS}/{trip_id}'),
                             ('PUT', f'{TRIPS}/{trip_id}'), ('PATCH', f'{TRIPS}/{trip_id}'),
                             ('DELETE', f'{TRIPS}/{trip_id}')):
            with self.subTest(method=method, path=path):
                response = self.client.open(path, method=method, json=VALID_TRIP)
                self.assertEqual(response.status_code, 401)
        self.assertEqual(db.session.get(Trip, trip_id).destination, 'Lisbon')

    def test_old_unprefixed_path_is_not_served(self):
        self.assertEqual(self.call('GET', '/trips').status_code, 404)


class TripCreateTests(TripRoutesTestCase):
    def test_create_trip(self):
        trip = self.create_trip(
            destination='  Lisbon  ', latitude=38.7223, longitude=-9.1393,
            itinerary=[{'day': 1, 'activities': ['Alfama walk']}],
        )

        self.assertEqual(trip['destination'], 'Lisbon')
        self.assertEqual(trip['start_date'], '2027-05-01')
        self.assertEqual((trip['latitude'], trip['longitude']), (38.7223, -9.1393))
        self.assertEqual(trip['itinerary'], [{'day': 1, 'activities': ['Alfama walk']}])
        self.assertEqual(db.session.get(Trip, trip['id']).user.email, 'owner@example.com')

    def test_defaults_and_ownership_cannot_be_spoofed(self):
        trip = self.create_trip(user_id=999, id=999)

        self.assertEqual(len(trip['itinerary']), 8)
        self.assertEqual(trip['itinerary'][0]['title'], 'Day 1')
        self.assertIsNone(trip['latitude'])
        self.assertNotEqual(trip['id'], 999)
        self.assertNotEqual(trip['user_id'], 999)

    def test_default_itinerary_generated_only_when_not_supplied(self):
        generated = self.create_trip()['itinerary']
        self.assertEqual([d['date'] for d in generated],
                         [f'2027-05-0{day}' for day in range(1, 9)])

        self.assertEqual(self.create_trip(itinerary=[])['itinerary'], [])
        custom = {'plan': 'free-form'}
        self.assertEqual(self.create_trip(itinerary=custom)['itinerary'], custom)

        saved = self.call('GET', f"{TRIPS}/{self.create_trip()['id']}").get_json()['trip']
        self.assertEqual(len(saved['itinerary']), 8)

    def test_update_does_not_regenerate_itinerary(self):
        trip = self.create_trip(itinerary=[{'day': 1, 'activities': ['Museum']}])
        response = self.call('PATCH', f"{TRIPS}/{trip['id']}", {'end_date': '2027-05-20'})

        self.assertEqual(response.get_json()['trip']['itinerary'], [{'day': 1, 'activities': ['Museum']}])

    def test_trailing_slash_is_accepted(self):
        response = self.call('POST', f'{TRIPS}/', VALID_TRIP)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.call('GET', f'{TRIPS}/').status_code, 200)

    def test_validation_errors(self):
        invalid = (
            {},
            {k: v for k, v in VALID_TRIP.items() if k != 'destination'},
            {k: v for k, v in VALID_TRIP.items() if k != 'start_date'},
            {**VALID_TRIP, 'destination': '   '},
            {**VALID_TRIP, 'destination': 5},
            {**VALID_TRIP, 'destination': 'x' * 256},
            {**VALID_TRIP, 'start_date': '01/05/2027'},
            {**VALID_TRIP, 'start_date': '2027-02-30'},
            {**VALID_TRIP, 'start_date': '2027-05-01T10:00:00'},
            {**VALID_TRIP, 'end_date': '2027-04-30'},
            {**VALID_TRIP, 'latitude': 91, 'longitude': 0},
            {**VALID_TRIP, 'latitude': 0, 'longitude': -181},
            {**VALID_TRIP, 'latitude': '10', 'longitude': 10},
            {**VALID_TRIP, 'latitude': True, 'longitude': 10},
            {**VALID_TRIP, 'latitude': 10},
            {**VALID_TRIP, 'itinerary': 'plan'},
            {**VALID_TRIP, 'itinerary': None},
        )
        for payload in invalid:
            with self.subTest(payload=payload):
                response = self.call('POST', TRIPS, payload)
                self.assertEqual(response.status_code, 400)
                self.assertIn('error', response.get_json())
        self.assertEqual(Trip.query.count(), 0)

    def test_non_object_body_rejected(self):
        self.assertEqual(self.call('POST', TRIPS, [VALID_TRIP]).status_code, 400)
        response = self.client.post(
            TRIPS, data='{bad', content_type='application/json',
            headers={'Authorization': f'Bearer {self.token}'},
        )
        self.assertEqual(response.status_code, 400)


class TripReadTests(TripRoutesTestCase):
    def test_list_returns_only_own_trips_ordered_by_start_date(self):
        later = self.create_trip(destination='Later', start_date='2027-09-01', end_date='2027-09-05')
        sooner = self.create_trip(destination='Sooner', start_date='2027-02-01', end_date='2027-02-05')
        self.create_trip(token=self.other_token, destination='Not mine')

        response = self.call('GET', TRIPS)
        self.assertEqual(response.status_code, 200)
        self.assertEqual([t['id'] for t in response.get_json()['trips']], [sooner['id'], later['id']])
        self.assertEqual(self.call('GET', TRIPS, token=self.other_token).get_json()['trips'][0]['destination'],
                         'Not mine')

    def test_list_is_empty_for_new_user(self):
        self.assertEqual(self.call('GET', TRIPS).get_json(), {'trips': []})

    def test_get_trip(self):
        trip = self.create_trip()
        response = self.call('GET', f"{TRIPS}/{trip['id']}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['trip'], trip)

    def test_other_users_and_missing_trips_return_404(self):
        trip = self.create_trip()
        for token, trip_id in ((self.other_token, trip['id']), (self.token, 9999)):
            with self.subTest(trip_id=trip_id):
                for method in ('GET', 'PUT', 'DELETE'):
                    response = self.call(method, f'{TRIPS}/{trip_id}', VALID_TRIP, token)
                    self.assertEqual(response.status_code, 404)
        self.assertEqual(db.session.get(Trip, trip['id']).destination, 'Lisbon')


class TripUpdateTests(TripRoutesTestCase):
    def test_partial_update_changes_only_supplied_fields(self):
        trip = self.create_trip(latitude=1, longitude=2)
        for method in ('PATCH', 'PUT'):
            with self.subTest(method=method):
                response = self.call(method, f"{TRIPS}/{trip['id']}", {'destination': f'Porto {method}'})
                self.assertEqual(response.status_code, 200)
                updated = response.get_json()['trip']
                self.assertEqual(updated['destination'], f'Porto {method}')
                self.assertEqual(updated['start_date'], '2027-05-01')
                self.assertEqual((updated['latitude'], updated['longitude']), (1.0, 2.0))

    def test_update_itinerary_dates_and_clear_coordinates(self):
        trip = self.create_trip(latitude=1, longitude=2)
        itinerary = [{'day': 1, 'activities': ['Museum']}]
        response = self.call('PATCH', f"{TRIPS}/{trip['id']}", {
            'itinerary': itinerary, 'end_date': '2027-05-20', 'latitude': None, 'longitude': None,
        })

        updated = response.get_json()['trip']
        self.assertEqual(updated['itinerary'], itinerary)
        self.assertEqual(updated['end_date'], '2027-05-20')
        self.assertIsNone(updated['latitude'])
        self.assertEqual(self.call('GET', f"{TRIPS}/{trip['id']}").get_json()['trip'], updated)

    def test_update_validated_against_existing_values(self):
        trip = self.create_trip()
        url = f"{TRIPS}/{trip['id']}"
        for payload in ({'end_date': '2027-04-01'}, {'start_date': '2027-06-01'}, {'latitude': 10},
                        {'destination': ''}, {}, {'unknown': 'field'}):
            with self.subTest(payload=payload):
                self.assertEqual(self.call('PATCH', url, payload).status_code, 400)
        self.assertEqual(self.call('GET', url).get_json()['trip'], trip)

    def test_update_cannot_change_owner_or_id(self):
        trip = self.create_trip()
        response = self.call('PATCH', f"{TRIPS}/{trip['id']}", {'destination': 'Porto', 'user_id': 999, 'id': 999})

        self.assertEqual(response.get_json()['trip']['id'], trip['id'])
        self.assertEqual(response.get_json()['trip']['user_id'], trip['user_id'])


class TripDeleteTests(TripRoutesTestCase):
    def test_delete_trip(self):
        trip = self.create_trip()
        keep = self.create_trip(destination='Keep')

        response = self.call('DELETE', f"{TRIPS}/{trip['id']}")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.data, b'')
        self.assertEqual(self.call('GET', f"{TRIPS}/{trip['id']}").status_code, 404)
        self.assertEqual(self.call('DELETE', f"{TRIPS}/{trip['id']}").status_code, 404)
        self.assertEqual([t['id'] for t in self.call('GET', TRIPS).get_json()['trips']], [keep['id']])
