import unittest
import re
from unittest.mock import patch

from werkzeug.security import check_password_hash, generate_password_hash

from app import create_app
from app.config import Config
from app.extensions import db
from app.models.user import User


class AuthenticationFlowTests(unittest.TestCase):
    def setUp(self):
        with patch.object(Config, 'SQLALCHEMY_DATABASE_URI', 'sqlite:///:memory:'), \
                patch.object(Config, 'SECRET_KEY', 'unit-test-secret-key'):
            self.app = create_app()
        self.app.config.update(TESTING=True, RATELIMIT_ENABLED=False)
        self.context = self.app.app_context()
        self.context.push()
        db.session.add_all([
            User(username='test-admin', password_hash=generate_password_hash('test-admin-password'), role='admin'),
            User(username='test-seller', password_hash=generate_password_hash('test-seller-password'), role='seller'),
        ])
        db.session.commit()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        self.context.pop()

    def test_users_can_log_in(self):
        login_page = self.client.get('/login')
        self.assertEqual(login_page.status_code, 200)
        csrf_token = re.search(rb'name="csrf_token" value="([^"]+)"', login_page.data).group(1).decode()
        admin = self.client.post('/login', data={
            'username': 'test-admin', 'password': 'test-admin-password', 'csrf_token': csrf_token,
        }, follow_redirects=True)
        self.assertEqual(admin.request.path, '/dashboard')
        self.client.post('/logout', data={'csrf_token': csrf_token}, follow_redirects=True)
        seller = self.client.post('/login', data={
            'username': 'test-seller', 'password': 'test-seller-password', 'csrf_token': csrf_token,
        }, follow_redirects=True)
        self.assertEqual(seller.request.path, '/dashboard')

    def test_post_without_csrf_token_is_rejected(self):
        response = self.client.post('/login', data={
            'username': 'test-admin', 'password': 'test-admin-password',
        })
        self.assertEqual(response.status_code, 400)

    def test_logout_requires_post(self):
        response = self.client.get('/logout')
        self.assertEqual(response.status_code, 405)

    def test_production_requires_secret_key(self):
        with patch.object(Config, 'SECRET_KEY', None), patch.object(Config, 'DEVELOPMENT', False):
            with self.assertRaisesRegex(RuntimeError, 'SECRET_KEY es obligatoria'):
                create_app()

    def test_secure_cookie_policy_and_hsts(self):
        self.assertTrue(self.app.config['SESSION_COOKIE_SECURE'])
        self.assertTrue(self.app.config['SESSION_COOKIE_HTTPONLY'])
        self.assertEqual(self.app.config['SESSION_COOKIE_SAMESITE'], 'Lax')
        self.assertTrue(self.app.config['REMEMBER_COOKIE_SECURE'])
        self.assertTrue(self.app.config['REMEMBER_COOKIE_HTTPONLY'])
        self.assertEqual(self.app.config['REMEMBER_COOKIE_SAMESITE'], 'Lax')
        response = self.client.get('/login')
        self.assertIn('max-age=31536000', response.headers['Strict-Transport-Security'])

    def test_login_is_rate_limited(self):
        self.app.config['RATELIMIT_ENABLED'] = True
        login_page = self.client.get('/login')
        csrf_token = re.search(rb'name="csrf_token" value="([^"]+)"', login_page.data).group(1).decode()
        responses = [self.client.post('/login', data={
            'username': 'missing-user', 'password': 'incorrect', 'csrf_token': csrf_token,
        }) for _ in range(6)]
        self.assertEqual(responses[-1].status_code, 429)
        self.assertIn('Demasiados intentos', responses[-1].get_data(as_text=True))

    def test_user_can_change_own_password_with_current_password(self):
        login_page = self.client.get('/login')
        csrf_token = re.search(rb'name="csrf_token" value="([^"]+)"', login_page.data).group(1).decode()
        self.client.post('/login', data={
            'username': 'test-seller', 'password': 'test-seller-password', 'csrf_token': csrf_token,
        })
        short = self.client.post('/change-password', data={
            'current_password': 'test-seller-password', 'new_password': 'too-short',
            'csrf_token': csrf_token,
        }, follow_redirects=True)
        self.assertIn('al menos 12 caracteres', short.get_data(as_text=True))
        changed = self.client.post('/change-password', data={
            'current_password': 'test-seller-password', 'new_password': 'new-secure-password',
            'csrf_token': csrf_token,
        }, follow_redirects=True)
        self.assertEqual(changed.status_code, 200)
        updated_user = User.query.filter_by(username='test-seller').first()
        self.assertTrue(check_password_hash(updated_user.password_hash, 'new-secure-password'))


if __name__ == '__main__':
    unittest.main()
