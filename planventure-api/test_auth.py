import unittest
from datetime import timedelta

from flask import Flask
from flask_jwt_extended import create_access_token, create_refresh_token

from extensions import db, jwt
from models import User
from routes.auth import auth_bp
from utils.jwt_utils import generate_access_token, verify_access_token
from utils.validators import is_valid_email, validate_password


class ValidatorTests(unittest.TestCase):
    def test_valid_emails(self):
        for email in ('user@example.com', 'first.last+tag@sub.example.co.uk', "o'brien@example.org"):
            with self.subTest(email=email):
                self.assertTrue(is_valid_email(email))

    def test_invalid_emails(self):
        too_long = 'a' * 250 + '@example.com'
        long_local = 'a' * 65 + '@example.com'
        for email in (
            '', 'plain', '@example.com', 'user@', 'user@example', 'user@@example.com',
            'user@example..com', '.user@example.com', 'user.@example.com',
            'us er@example.com', 'user@-example.com', 'user@example.c', too_long,
            long_local, None, 42,
        ):
            with self.subTest(email=email):
                self.assertFalse(is_valid_email(email))

    def test_password_rules(self):
        self.assertIsNone(validate_password('longenough'))
        self.assertIsNone(validate_password('a' * 72))
        for password in (None, 123, 'short', 'a' * 73, 'é' * 37):
            with self.subTest(password=password):
                self.assertIsNotNone(validate_password(password))


class AuthTestCase(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        app.config.update(
            SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
            JWT_SECRET_KEY='test-secret-key-0123456789-abcdefghij',
        )
        db.init_app(app)
        jwt.init_app(app)
        app.register_blueprint(auth_bp)
        self.app = app
        self.context = app.app_context()
        self.context.push()
        db.create_all()
        self.client = app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.context.pop()

    def register(self, payload):
        return self.client.post('/auth/register', json=payload)

    def login(self, payload):
        return self.client.post('/auth/login', json=payload)


class RegisterRouteTests(AuthTestCase):
    def test_successful_registration(self):
        response = self.register({'email': '  New.User@Example.com ', 'password': 'password123'})

        self.assertEqual(response.status_code, 201)
        body = response.get_json()
        self.assertEqual(body['user']['email'], 'new.user@example.com')
        self.assertNotIn('password', str(body['user']).lower())
        user = User.query.one()
        self.assertTrue(user.check_password('password123'))
        self.assertNotEqual(user.password_hash, 'password123')
        self.assertEqual(verify_access_token(body['access_token']), user.id)

    def test_validation_errors(self):
        cases = (
            {},
            {'email': 'not-an-email', 'password': 'password123'},
            {'email': 123, 'password': 'password123'},
            {'password': 'password123'},
            {'email': 'a@example.com'},
            {'email': 'a@example.com', 'password': 'short'},
            {'email': 'a@example.com', 'password': 'a' * 73},
        )
        for payload in cases:
            with self.subTest(payload=payload):
                response = self.register(payload)
                self.assertEqual(response.status_code, 400)
                self.assertIn('error', response.get_json())
        self.assertEqual(User.query.count(), 0)

    def test_non_json_body_rejected(self):
        for kwargs in ({'data': 'email=a@example.com'}, {'json': ['a@example.com']},
                       {'data': '{bad json', 'content_type': 'application/json'}):
            with self.subTest(kwargs=kwargs):
                response = self.client.post('/auth/register', **kwargs)
                self.assertEqual(response.status_code, 400)

    def test_duplicate_email_rejected_case_insensitively(self):
        self.assertEqual(self.register({'email': 'a@example.com', 'password': 'password123'}).status_code, 201)
        response = self.register({'email': 'A@Example.com', 'password': 'another-pass'})

        self.assertEqual(response.status_code, 409)
        self.assertEqual(User.query.count(), 1)


class LoginRouteTests(AuthTestCase):
    def setUp(self):
        super().setUp()
        registered = self.register({'email': 'user@example.com', 'password': 'password123'})
        self.user_id = registered.get_json()['user']['id']

    def test_successful_login_returns_valid_token(self):
        response = self.login({'email': ' User@Example.com ', 'password': 'password123'})

        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body['user']['email'], 'user@example.com')
        self.assertNotIn('password', str(body['user']).lower())
        self.assertEqual(verify_access_token(body['access_token']), self.user_id)

    def test_wrong_password_and_unknown_email_give_same_401(self):
        wrong_password = self.login({'email': 'user@example.com', 'password': 'wrong-password'})
        unknown_email = self.login({'email': 'nobody@example.com', 'password': 'password123'})

        self.assertEqual(wrong_password.status_code, 401)
        self.assertEqual(unknown_email.status_code, 401)
        self.assertEqual(wrong_password.get_json(), unknown_email.get_json())
        self.assertNotIn('access_token', wrong_password.get_json())

    def test_missing_or_malformed_fields_rejected(self):
        for payload in ({}, {'email': 'user@example.com'}, {'password': 'password123'},
                        {'email': '', 'password': 'password123'},
                        {'email': 'user@example.com', 'password': ''},
                        {'email': 123, 'password': 'password123'},
                        {'email': 'user@example.com', 'password': ['password123']}):
            with self.subTest(payload=payload):
                self.assertEqual(self.login(payload).status_code, 400)

        for kwargs in ({'data': 'email=user@example.com'}, {'json': ['user@example.com']}):
            with self.subTest(kwargs=kwargs):
                self.assertEqual(self.client.post('/auth/login', **kwargs).status_code, 400)

    def test_overlong_password_is_unauthorized_not_error(self):
        response = self.login({'email': 'user@example.com', 'password': 'a' * 100})
        self.assertEqual(response.status_code, 401)


class ProtectedRouteTests(AuthTestCase):
    def setUp(self):
        super().setUp()
        body = self.register({'email': 'user@example.com', 'password': 'password123'}).get_json()
        self.user_id = body['user']['id']
        self.token = body['access_token']

    def get_me(self, token=None, scheme='Bearer'):
        headers = {'Authorization': f'{scheme} {token}'} if token else {}
        return self.client.get('/auth/me', headers=headers)

    def test_valid_token_grants_access_to_current_user(self):
        response = self.get_me(self.token)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['user']['id'], self.user_id)
        self.assertEqual(response.get_json()['user']['email'], 'user@example.com')

    def test_login_token_works_too(self):
        token = self.login({'email': 'user@example.com', 'password': 'password123'}).get_json()['access_token']
        self.assertEqual(self.get_me(token).status_code, 200)

    def test_missing_or_bad_credentials_get_json_401(self):
        header, payload, signature = self.token.split('.')
        cases = {
            'no header': self.get_me(),
            'garbage': self.get_me('garbage'),
            'tampered': self.get_me(f'{header}.{payload}.{signature[:-2]}AA'),
            'wrong scheme': self.get_me(self.token, scheme='Basic'),
        }
        for name, response in cases.items():
            with self.subTest(case=name):
                self.assertEqual(response.status_code, 401)
                self.assertIn('error', response.get_json())

    def test_expired_token_rejected(self):
        self.app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(seconds=-1)
        expired = generate_access_token(self.user_id)

        response = self.get_me(expired)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json(), {'error': 'Token has expired'})

    def test_refresh_token_rejected(self):
        self.assertEqual(self.get_me(create_refresh_token(identity=str(self.user_id))).status_code, 401)

    def test_token_for_deleted_user_rejected(self):
        db.session.delete(db.session.get(User, self.user_id))
        db.session.commit()

        response = self.get_me(self.token)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json(), {'error': 'User not found'})

    def test_non_numeric_subject_rejected(self):
        self.assertEqual(self.get_me(create_access_token(identity='abc')).status_code, 401)


if __name__ == '__main__':
    unittest.main()
