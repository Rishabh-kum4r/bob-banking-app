from database import get_connection
from werkzeug.security import check_password_hash


def authenticate_customer(username, password):
    """
    Validates credentials against the database.

    Returns:
        (True, customer_id, username) on success.
        (False, None, None) on any failure.

    Always returns the same generic error regardless of whether the username
    was not found or the password was wrong — avoids username enumeration.
    """
    if not username or not password:
        return False, None, None

    conn = get_connection()
    try:
        row = conn.execute(
            'SELECT id, username, password_hash FROM customers WHERE username = ?',
            (username,)
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return False, None, None

    if not check_password_hash(row['password_hash'], password):
        return False, None, None

    return True, row['id'], row['username']


def get_balance(customer_id):
    """
    Returns the current account balance for the given customer_id as a float.
    """
    conn = get_connection()
    try:
        row = conn.execute(
            'SELECT balance FROM accounts WHERE customer_id = ?',
            (customer_id,)
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        return 0.0
    return float(row['balance'])


def deposit(customer_id, amount_str):
    """
    Validates and applies a deposit.

    Validation order: presence → numeric → positive → ceiling.

    Returns:
        (True, new_balance) on success.
        (False, error_message) on failure.
    """
    # Presence check
    if not amount_str or str(amount_str).strip() == '':
        return False, 'Deposit amount is required'

    # Numeric check
    try:
        amount = float(str(amount_str).strip())
    except ValueError:
        return False, 'Deposit amount must be a number'

    # Positive check
    if amount <= 0:
        return False, 'Deposit amount must be greater than zero'

    # Ceiling check
    if amount > 1_000_000:
        return False, 'Deposit amount exceeds the allowed limit'

    current_balance = get_balance(customer_id)
    new_balance = round(current_balance + amount, 2)

    conn = get_connection()
    try:
        conn.execute(
            'UPDATE accounts SET balance = ? WHERE customer_id = ?',
            (new_balance, customer_id)
        )
        conn.commit()
    finally:
        conn.close()

    return True, new_balance


def withdraw(customer_id, amount_str):
    """
    Validates and applies a withdrawal.

    Validation order: presence → numeric → positive → sufficient funds.

    Returns:
        (True, new_balance) on success.
        (False, error_message) on failure.
    """
    # Presence check
    if not amount_str or str(amount_str).strip() == '':
        return False, 'Withdrawal amount is required'

    # Numeric check
    try:
        amount = float(str(amount_str).strip())
    except ValueError:
        return False, 'Withdrawal amount must be a number'

    # Positive check
    if amount <= 0:
        return False, 'Withdrawal amount must be greater than zero'

    # Sufficient funds check
    current_balance = get_balance(customer_id)
    if current_balance < amount:
        return False, f'Insufficient funds. Your current balance is ${current_balance:,.2f}'

    new_balance = round(current_balance - amount, 2)

    conn = get_connection()
    try:
        conn.execute(
            'UPDATE accounts SET balance = ? WHERE customer_id = ?',
            (new_balance, customer_id)
        )
        conn.commit()
    finally:
        conn.close()

    return True, new_balance
