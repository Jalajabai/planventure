import unittest
from datetime import timedelta

from flask import Flask
from flask_jwt_extended import create_access_token, create_refresh_token

from extensions import db, jwt
from models import User
from utils.jwt_utils import generate_access_token, get_user_from_token, verify_access_token


def make_app(secret='test-secret-key-0123456789-abcdefghij', **config):
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
        JWT_SECRET_KEY=secret,
        **config,
    )
    db.init_app(app)
    jwt.init_app(app)
    return app


class JwtUtilsTests(unittest.TestCase):
    def setUp(self):
        self.app = make_app()
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.context.pop()

    def test_round_trip_returns_user_id(self):
        token = generate_access_token(42)
        self.assertEqual(verify_access_token(token), 42)

    def test_additional_claims_are_included(self):
        from flask_jwt_extended import decode_token
        token = generate_access_token(1, {'role': 'admin'})
        self.assertEqual(decode_token(token)['role'], 'admin')

    def test_invalid_tokens_rejected(self):
        valid = generate_access_token(1)
        header, payload, signature = valid.split('.')
        tampered = f'{header}.{payload}.{signature[:-2]}AA'
        other_app = make_app(secret='other-secret-key-0123456789-abcdefghij')
        with other_app.app_context():
            foreign = generate_access_token(1)

        for token in ('', 'garbage', None, tampered, foreign):
            with self.subTest(token=token):
                self.assertIsNone(verify_access_token(token))

    def test_expired_token_rejected(self):
        self.app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(seconds=-1)
        self.assertIsNone(verify_access_token(generate_access_token(1)))

    def test_refresh_token_not_accepted_as_access_token(self):
        self.assertIsNone(verify_access_token(create_refresh_token(identity='1')))

    def test_non_numeric_subject_rejected(self):
        self.assertIsNone(verify_access_token(create_access_token(identity='abc')))

    def test_get_user_from_token(self):
        user = User(email='a@example.com', password_hash='hash')
        db.session.add(user)
        db.session.commit()
        token = generate_access_token(user.id)

        self.assertEqual(get_user_from_token(token), user)
        self.assertIsNone(get_user_from_token('garbage'))

        db.session.delete(user)
        db.session.commit()
        self.assertIsNone(get_user_from_token(token))


if __name__ == '__main__':
    unittest.main()
