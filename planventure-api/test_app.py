import importlib.util
import os
from datetime import timedelta
from pathlib import Path
import unittest
from unittest.mock import patch

from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import text

from utils.jwt_utils import generate_access_token


class AppTests(unittest.TestCase):
    def load_app(self, environment):
        spec = importlib.util.spec_from_file_location(
            'app_under_test', Path(__file__).with_name('app.py')
        )
        module = importlib.util.module_from_spec(spec)
        with patch.dict(os.environ, environment, clear=True):
            with patch('dotenv.load_dotenv') as load_dotenv:
                spec.loader.exec_module(module)
        load_dotenv.assert_called_once_with(Path(__file__).with_name('.env'))
        return module

    def test_default_configuration(self):
        module = self.load_app({})
        with module.app.app_context():
            self.addCleanup(module.db.engine.dispose)
            self.assertEqual(module.db.engine.url.database,
                             str(Path(module.app.instance_path) / 'planventure.db'))
        self.assertFalse(module.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'])
        self.assertFalse(module.app.debug)
        client = module.app.test_client()
        for origin in ('http://localhost:3000', 'http://localhost:5173'):
            response = client.get('/', headers={'Origin': origin})
            self.assertEqual(response.headers['Access-Control-Allow-Origin'], origin)
        response = client.get('/', headers={'Origin': 'http://example.com'})
        self.assertNotIn('Access-Control-Allow-Origin', response.headers)

    def test_cors_preflight_for_react_frontend(self):
        module = self.load_app({'DATABASE_URL': 'sqlite:///:memory:'})
        client = module.app.test_client()

        response = client.options('/api/trips', headers={
            'Origin': 'http://localhost:3000',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'authorization,content-type',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Access-Control-Allow-Origin'], 'http://localhost:3000')
        allowed_headers = response.headers['Access-Control-Allow-Headers'].lower()
        self.assertIn('authorization', allowed_headers)
        self.assertIn('content-type', allowed_headers)
        allowed_methods = response.headers['Access-Control-Allow-Methods']
        for method in ('GET', 'POST', 'PUT', 'PATCH', 'DELETE'):
            self.assertIn(method, allowed_methods)
        self.assertEqual(response.headers['Access-Control-Max-Age'], '600')
        self.assertNotIn('Access-Control-Allow-Credentials', response.headers)

        blocked = client.options('/api/trips', headers={
            'Origin': 'http://evil.example',
            'Access-Control-Request-Method': 'POST',
        })
        self.assertNotIn('Access-Control-Allow-Origin', blocked.headers)

    def test_cors_headers_on_authenticated_error_responses(self):
        module = self.load_app({'DATABASE_URL': 'sqlite:///:memory:'})
        response = module.app.test_client().get('/api/trips', headers={'Origin': 'http://localhost:5173'})

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.headers['Access-Control-Allow-Origin'], 'http://localhost:5173')

    def test_environment_configuration_and_routes(self):
        module = self.load_app({
            'DATABASE_URL': 'sqlite:///:memory:',
            'SECRET_KEY': 'test-only-key',
            'CORS_ORIGINS': 'http://localhost:3000, http://localhost:5173',
        })
        self.assertEqual(module.app.secret_key, 'test-only-key')
        with module.app.app_context():
            self.addCleanup(module.db.engine.dispose)
            self.assertEqual(module.db.engine.url.database, ':memory:')
            self.assertEqual(module.db.session.execute(text('SELECT 1')).scalar(), 1)

        client = module.app.test_client()
        for route, payload in (
            ('/', {'message': 'Welcome to PlanVenture API'}),
            ('/health', {'status': 'healthy'}),
        ):
            with self.subTest(route=route):
                response = client.get(route)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.get_json(), payload)

        self.assertEqual(client.post('/auth/register', json={}).status_code, 400)

        for origin in ('http://localhost:3000', 'http://localhost:5173'):
            response = client.get('/health', headers={'Origin': origin})
            self.assertEqual(response.headers['Access-Control-Allow-Origin'], origin)
        response = client.get(
            '/health', headers={'Origin': 'http://untrusted.example'}
        )
        self.assertNotIn('Access-Control-Allow-Origin', response.headers)

    def test_jwt_configuration_and_error_responses(self):
        module = self.load_app({
            'DATABASE_URL': 'sqlite:///:memory:',
            'JWT_SECRET_KEY': 'jwt-test-key-0123456789-abcdefghijklmnop',
            'JWT_ACCESS_TOKEN_EXPIRES_MINUTES': '5',
        })
        self.assertEqual(module.app.config['JWT_ACCESS_TOKEN_EXPIRES'], timedelta(minutes=5))

        @module.app.route('/protected')
        @jwt_required()
        def protected():
            return module.jsonify({"user": get_jwt_identity()})

        client = module.app.test_client()
        with module.app.app_context():
            self.addCleanup(module.db.engine.dispose)
            token = generate_access_token(7)

        response = client.get('/protected', headers={'Authorization': f'Bearer {token}'})
        self.assertEqual(response.get_json(), {"user": "7"})

        response = client.get('/protected')
        self.assertEqual(response.status_code, 401)
        self.assertIn('error', response.get_json())

        response = client.get('/protected', headers={'Authorization': 'Bearer garbage'})
        self.assertEqual(response.status_code, 401)
        self.assertIn('error', response.get_json())

        module.app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(seconds=-1)
        with module.app.app_context():
            expired = generate_access_token(7)
        response = client.get('/protected', headers={'Authorization': f'Bearer {expired}'})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json(), {"error": "Token has expired"})
