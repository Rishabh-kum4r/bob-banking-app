"""
Unit tests for services.py

Tests run against an isolated in-memory SQLite database — they never
touch BACKEND/banking.db.

Strategy: patch `services.get_connection` to return a non-closeable
wrapper around a shared in-memory connection. Because Python 3.14+
makes sqlite3.Connection.close read-only on the C object, we wrap it in
a thin proxy class whose close() is a no-op.
"""

import sys
import os
import sqlite3
import unittest
from unittest.mock import patch, MagicMock
from werkzeug.security import generate_password_hash

# Ensure BACKEND/ is on the path so absolute imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import services


# ---------------------------------------------------------------------------
# Non-closeable connection wrapper
# ---------------------------------------------------------------------------

class _NoCloseConnection:
    """
    Thin proxy around sqlite3.Connection whose close() is a no-op.
    Delegates everything else to the real connection.
    """
    def __init__(self, conn):
        self._conn = conn

    def close(self):
        pass   # intentional no-op — keep the in-memory DB alive

    def execute(self, *args, **kwargs):
        return self._conn.execute(*args, **kwargs)

    def commit(self):
        return self._conn.commit()

    def rollback(self):
        return self._conn.rollback()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


# ---------------------------------------------------------------------------
# Helper: create and seed an in-memory database
# ---------------------------------------------------------------------------

def _make_in_memory_db():
    """Create an in-memory SQLite database with one test customer (balance $500)."""
    conn = sqlite3.connect(':memory:', check_same_thread=False)
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
    return conn


def _make_wrapper(conn):
    """Return a _NoCloseConnection proxy whose row_factory mirrors the real conn."""
    wrapper = _NoCloseConnection(conn)
    return wrapper


# ---------------------------------------------------------------------------
# Base test case
# ---------------------------------------------------------------------------

class ServiceTestCase(unittest.TestCase):
    def setUp(self):
        self._real_conn = _make_in_memory_db()
        self._wrapper = _NoCloseConnection(self._real_conn)
        self.patcher = patch('services.get_connection', return_value=self._wrapper)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        self._real_conn.close()


# ---------------------------------------------------------------------------
# authenticate_customer tests
# ---------------------------------------------------------------------------

class TestAuthenticateCustomer(ServiceTestCase):
    def test_valid_credentials_returns_success(self):
        ok, customer_id, username = services.authenticate_customer('testuser', 'testpass')
        self.assertTrue(ok)
        self.assertEqual(customer_id, 1)
        self.assertEqual(username, 'testuser')

    def test_wrong_password_returns_failure(self):
        ok, customer_id, username = services.authenticate_customer('testuser', 'wrongpass')
        self.assertFalse(ok)
        self.assertIsNone(customer_id)

    def test_unknown_username_returns_failure(self):
        ok, customer_id, username = services.authenticate_customer('nobody', 'testpass')
        self.assertFalse(ok)
        self.assertIsNone(customer_id)

    def test_empty_username_returns_failure(self):
        ok, customer_id, username = services.authenticate_customer('', 'testpass')
        self.assertFalse(ok)

    def test_empty_password_returns_failure(self):
        ok, customer_id, username = services.authenticate_customer('testuser', '')
        self.assertFalse(ok)

    def test_none_username_returns_failure(self):
        ok, customer_id, username = services.authenticate_customer(None, 'testpass')
        self.assertFalse(ok)


# ---------------------------------------------------------------------------
# get_balance tests
# ---------------------------------------------------------------------------

class TestGetBalance(ServiceTestCase):
    def test_returns_correct_balance(self):
        balance = services.get_balance(1)
        self.assertAlmostEqual(balance, 500.00)

    def test_unknown_customer_returns_zero(self):
        balance = services.get_balance(9999)
        self.assertEqual(balance, 0.0)


# ---------------------------------------------------------------------------
# deposit tests
# ---------------------------------------------------------------------------

class TestDeposit(ServiceTestCase):
    def test_valid_deposit_increases_balance(self):
        ok, new_balance = services.deposit(1, '200')
        self.assertTrue(ok)
        self.assertAlmostEqual(new_balance, 700.00)

    def test_empty_amount_returns_error(self):
        ok, msg = services.deposit(1, '')
        self.assertFalse(ok)
        self.assertIn('required', msg.lower())

    def test_non_numeric_amount_returns_error(self):
        ok, msg = services.deposit(1, 'abc')
        self.assertFalse(ok)
        self.assertIn('number', msg.lower())

    def test_zero_amount_returns_error(self):
        ok, msg = services.deposit(1, '0')
        self.assertFalse(ok)
        self.assertIn('greater than zero', msg.lower())

    def test_negative_amount_returns_error(self):
        ok, msg = services.deposit(1, '-50')
        self.assertFalse(ok)
        self.assertIn('greater than zero', msg.lower())

    def test_over_ceiling_returns_error(self):
        ok, msg = services.deposit(1, '2000000')
        self.assertFalse(ok)
        self.assertIn('limit', msg.lower())

    def test_decimal_deposit(self):
        ok, new_balance = services.deposit(1, '99.99')
        self.assertTrue(ok)
        self.assertAlmostEqual(new_balance, 599.99)


# ---------------------------------------------------------------------------
# withdraw tests
# ---------------------------------------------------------------------------

class TestWithdraw(ServiceTestCase):
    def test_valid_withdrawal_decreases_balance(self):
        ok, new_balance = services.withdraw(1, '100')
        self.assertTrue(ok)
        self.assertAlmostEqual(new_balance, 400.00)

    def test_withdrawal_full_balance_succeeds(self):
        ok, new_balance = services.withdraw(1, '500')
        self.assertTrue(ok)
        self.assertAlmostEqual(new_balance, 0.00)

    def test_insufficient_funds_returns_error(self):
        ok, msg = services.withdraw(1, '600')
        self.assertFalse(ok)
        self.assertIn('insufficient', msg.lower())

    def test_empty_amount_returns_error(self):
        ok, msg = services.withdraw(1, '')
        self.assertFalse(ok)
        self.assertIn('required', msg.lower())

    def test_non_numeric_amount_returns_error(self):
        ok, msg = services.withdraw(1, 'xyz')
        self.assertFalse(ok)
        self.assertIn('number', msg.lower())

    def test_zero_amount_returns_error(self):
        ok, msg = services.withdraw(1, '0')
        self.assertFalse(ok)
        self.assertIn('greater than zero', msg.lower())

    def test_negative_amount_returns_error(self):
        ok, msg = services.withdraw(1, '-10')
        self.assertFalse(ok)
        self.assertIn('greater than zero', msg.lower())


if __name__ == '__main__':
    unittest.main()
