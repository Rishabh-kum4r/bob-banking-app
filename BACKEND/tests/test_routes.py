"""
Integration tests for Flask routes in app.py

Uses Flask's built-in test client to make HTTP requests without a
running server.  All tests use a separate temporary SQLite database
so they never touch BACKEND/banking.db.
"""

import sys
import os
import sqlite3
import tempfile
import unittest
from werkzeug.security import generate_password_hash

# Ensure BACKEND/ is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


# ---------------------------------------------------------------------------
# Test database factory
# ---------------------------------------------------------------------------

def _create_test_db(path):
    """Create and seed a test SQLite database at the given path."""
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute('''
        CREATE TABLE customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            balance REAL NOT NULL DEFAULT 0.0
        )
    ''')
    pw_hash = generate_password_hash('testpass')
    conn.execute(
        'INSERT INTO customers (username, password_hash) VALUES (?, ?)',
        ('testuser', pw_hash)
    )
    conn.execute(
        'INSERT INTO accounts (customer_id, balance) VALUES (?, ?)',
        (1, 500.00)
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Base test case: creates a temp DB, patches database.DB_PATH, configures
# the Flask test client.
# ---------------------------------------------------------------------------

class BankingAppTestCase(unittest.TestCase):
    def setUp(self):
        # Create a temp file for the test database
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')
        _create_test_db(self.db_path)

        # Patch DB_PATH before importing app so every connection goes to
        # the temp database.
        import database
        self._original_db_path = database.DB_PATH
        database.DB_PATH = self.db_path

        # Import app *after* patching DB_PATH so init_db() seeds the test DB
        import app as flask_app
        flask_app.app.config['TESTING'] = True
        flask_app.app.config['SECRET_KEY'] = 'test-secret'
        flask_app.app.config['WTF_CSRF_ENABLED'] = False

        self.client = flask_app.app.test_client()
        self.app_module = flask_app

    def tearDown(self):
        import database
        database.DB_PATH = self._original_db_path
        os.close(self.db_fd)
        try:
            os.unlink(self.db_path)
        except OSError:
            pass

    # Helper: log in via the test client and return the response
    def _login(self, username='testuser', password='testpass'):
        return self.client.post('/login', data={
            'username': username,
            'password': password
        }, follow_redirects=False)


# ---------------------------------------------------------------------------
# Authentication route tests
# ---------------------------------------------------------------------------

class TestLoginRoute(BankingAppTestCase):
    def test_get_login_returns_200(self):
        resp = self.client.get('/login')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Login', resp.data)

    def test_valid_login_redirects_to_dashboard(self):
        resp = self._login()
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/dashboard', resp.headers['Location'])

    def test_invalid_password_returns_200_with_error(self):
        resp = self.client.post('/login', data={
            'username': 'testuser', 'password': 'wrongpass'
        })
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Invalid username or password', resp.data)

    def test_unknown_username_returns_200_with_error(self):
        resp = self.client.post('/login', data={
            'username': 'ghost', 'password': 'testpass'
        })
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Invalid username or password', resp.data)

    def test_already_logged_in_get_login_redirects_to_dashboard(self):
        self._login()
        resp = self.client.get('/login')
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/dashboard', resp.headers['Location'])


class TestLogoutRoute(BankingAppTestCase):
    def test_logout_clears_session_and_redirects(self):
        self._login()
        resp = self.client.get('/logout', follow_redirects=False)
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login', resp.headers['Location'])

    def test_dashboard_after_logout_redirects_to_login(self):
        self._login()
        self.client.get('/logout')
        resp = self.client.get('/dashboard', follow_redirects=False)
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login', resp.headers['Location'])


# ---------------------------------------------------------------------------
# Dashboard route tests
# ---------------------------------------------------------------------------

class TestDashboardRoute(BankingAppTestCase):
    def test_dashboard_without_session_redirects_to_login(self):
        resp = self.client.get('/dashboard', follow_redirects=False)
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login', resp.headers['Location'])

    def test_dashboard_with_valid_session_returns_200(self):
        self._login()
        resp = self.client.get('/dashboard', follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'500', resp.data)   # seed balance

    def test_dashboard_shows_username(self):
        self._login()
        resp = self.client.get('/dashboard', follow_redirects=True)
        self.assertIn(b'testuser', resp.data)


# ---------------------------------------------------------------------------
# Deposit route tests
# ---------------------------------------------------------------------------

class TestDepositRoute(BankingAppTestCase):
    def test_get_deposit_without_session_redirects_to_login(self):
        resp = self.client.get('/deposit', follow_redirects=False)
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login', resp.headers['Location'])

    def test_get_deposit_with_session_returns_200(self):
        self._login()
        resp = self.client.get('/deposit')
        self.assertEqual(resp.status_code, 200)

    def test_valid_deposit_redirects_to_dashboard(self):
        self._login()
        resp = self.client.post('/deposit', data={'amount': '100'},
                                follow_redirects=False)
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/dashboard', resp.headers['Location'])

    def test_valid_deposit_updates_balance(self):
        self._login()
        self.client.post('/deposit', data={'amount': '250'})
        resp = self.client.get('/dashboard', follow_redirects=True)
        self.assertIn(b'750', resp.data)

    def test_invalid_deposit_amount_returns_error(self):
        self._login()
        resp = self.client.post('/deposit', data={'amount': '-50'})
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'greater than zero', resp.data)

    def test_empty_deposit_amount_returns_error(self):
        self._login()
        resp = self.client.post('/deposit', data={'amount': ''})
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'required', resp.data.lower())


# ---------------------------------------------------------------------------
# Withdraw route tests
# ---------------------------------------------------------------------------

class TestWithdrawRoute(BankingAppTestCase):
    def test_get_withdraw_without_session_redirects_to_login(self):
        resp = self.client.get('/withdraw', follow_redirects=False)
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login', resp.headers['Location'])

    def test_get_withdraw_with_session_returns_200(self):
        self._login()
        resp = self.client.get('/withdraw')
        self.assertEqual(resp.status_code, 200)

    def test_valid_withdrawal_redirects_to_dashboard(self):
        self._login()
        resp = self.client.post('/withdraw', data={'amount': '100'},
                                follow_redirects=False)
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/dashboard', resp.headers['Location'])

    def test_valid_withdrawal_updates_balance(self):
        self._login()
        self.client.post('/withdraw', data={'amount': '200'})
        resp = self.client.get('/dashboard', follow_redirects=True)
        self.assertIn(b'300', resp.data)

    def test_withdrawal_exceeding_balance_returns_error(self):
        self._login()
        resp = self.client.post('/withdraw', data={'amount': '9999'})
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Insufficient', resp.data)

    def test_empty_withdrawal_amount_returns_error(self):
        self._login()
        resp = self.client.post('/withdraw', data={'amount': ''})
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'required', resp.data.lower())

    def test_get_withdraw_shows_balance(self):
        self._login()
        resp = self.client.get('/withdraw')
        self.assertIn(b'500', resp.data)


if __name__ == '__main__':
    unittest.main()
