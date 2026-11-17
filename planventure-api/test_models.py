import time
import unittest
from datetime import date

from flask import Flask
from sqlalchemy.exc import IntegrityError

from extensions import db
from models import Trip, User


class DbTestCase(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        db.init_app(app)
        self.context = app.app_context()
        self.context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.context.pop()


class UserModelTests(DbTestCase):
    def test_timestamps_and_email_normalization(self):
        user = User(email='  Test@Example.COM ', password_hash='hash')
        db.session.add(user)
        db.session.commit()

        self.assertEqual(user.email, 'test@example.com')
        self.assertIsNotNone(user.created_at)
        self.assertIsNotNone(user.updated_at)

        created_at = user.created_at
        time.sleep(0.01)
        user.password_hash = 'new-hash'
        db.session.commit()
        self.assertGreater(user.updated_at, user.created_at)
        self.assertEqual(user.created_at, created_at)

    def test_email_unique_and_hash_required(self):
        db.session.add(User(email='a@example.com', password_hash='hash'))
        db.session.commit()

        db.session.add(User(email='A@example.com', password_hash='hash'))
        with self.assertRaises(IntegrityError):
            db.session.commit()
        db.session.rollback()

        db.session.add(User(email='b@example.com'))
        with self.assertRaises(IntegrityError):
            db.session.commit()

    def test_to_dict_excludes_password_hash(self):
        user = User(email='a@example.com', password_hash='secret-hash')
        db.session.add(user)
        db.session.commit()

        data = user.to_dict()
        self.assertEqual(data['email'], 'a@example.com')
        self.assertNotIn('password_hash', data)
        self.assertNotIn('secret-hash', str(data))


class TripModelTests(DbTestCase):
    def make_user(self, email='a@example.com'):
        user = User(email=email, password_hash='hash')
        db.session.add(user)
        db.session.commit()
        return user

    def make_trip(self, user, **overrides):
        values = dict(
            user=user,
            destination='Lisbon',
            start_date=date(2027, 5, 1),
            end_date=date(2027, 5, 8),
        )
        values.update(overrides)
        return Trip(**values)

    def test_trip_belongs_to_user_with_coordinates_and_itinerary(self):
        user = self.make_user()
        itinerary = [{'day': 1, 'activities': ['Alfama walk']}]
        trip = self.make_trip(
            user, latitude=38.7223, longitude=-9.1393, itinerary=itinerary
        )
        db.session.add(trip)
        db.session.commit()
        db.session.expire_all()

        saved = db.session.get(Trip, trip.id)
        self.assertEqual(saved.user.email, 'a@example.com')
        self.assertEqual(user.trips, [saved])
        self.assertEqual(saved.itinerary, itinerary)
        self.assertEqual((saved.latitude, saved.longitude), (38.7223, -9.1393))
        self.assertEqual(saved.to_dict()['start_date'], '2027-05-01')

    def test_itinerary_defaults_to_empty_list_and_coordinates_optional(self):
        trip = self.make_trip(self.make_user())
        db.session.add(trip)
        db.session.commit()

        self.assertEqual(trip.itinerary, [])
        self.assertIsNone(trip.latitude)
        self.assertIsNone(trip.longitude)

    def test_invalid_trips_rejected(self):
        user = self.make_user()
        invalid = (
            dict(end_date=date(2027, 4, 30)),
            dict(latitude=91, longitude=0),
            dict(latitude=0, longitude=-181),
            dict(destination=None),
        )
        for overrides in invalid:
            with self.subTest(overrides=overrides):
                db.session.add(self.make_trip(user, **overrides))
                with self.assertRaises(IntegrityError):
                    db.session.commit()
                db.session.rollback()

    def test_deleting_user_deletes_trips(self):
        user = self.make_user()
        db.session.add(self.make_trip(user))
        db.session.commit()

        db.session.delete(user)
        db.session.commit()
        self.assertEqual(Trip.query.count(), 0)


if __name__ == '__main__':
    unittest.main()
