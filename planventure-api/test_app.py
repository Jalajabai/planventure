import importlib.util
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from sqlalchemy import text


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
        response = module.app.test_client().get(
            '/', headers={'Origin': 'http://example.com'}
        )
        self.assertEqual(response.headers['Access-Control-Allow-Origin'],
                         'http://example.com')

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

        for origin in ('http://localhost:3000', 'http://localhost:5173'):
            response = client.get('/health', headers={'Origin': origin})
            self.assertEqual(response.headers['Access-Control-Allow-Origin'], origin)
        response = client.get(
            '/health', headers={'Origin': 'http://untrusted.example'}
        )
        self.assertNotIn('Access-Control-Allow-Origin', response.headers)
