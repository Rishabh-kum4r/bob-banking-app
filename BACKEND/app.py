import os
from flask import Flask, render_template, request, redirect, url_for, session
from models import init_db
from services import authenticate_customer, get_balance, deposit, withdraw

# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

_template_folder = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', 'FRONTEND', 'templates'
)

app = Flask(__name__, template_folder=_template_folder)
app.secret_key = 'dev-secret-key-change-in-production'

# Initialise database tables and seed data on startup
init_db()


# ---------------------------------------------------------------------------
# Session guard helper
# ---------------------------------------------------------------------------

def _require_login():
    """
    Returns a redirect response to /login when no session exists,
    or None when the user is authenticated. Call at the top of every
    protected route and return its result if it is not None.
    """
    if 'customer_id' not in session:
        return redirect(url_for('login'))
    return None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    return redirect(url_for('login'))


# --- Authentication ----------------------------------------------------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Already logged in — skip the form
    if 'customer_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        ok, customer_id, stored_username = authenticate_customer(username, password)
        if ok:
            session['customer_id'] = customer_id
            session['username'] = stored_username
            return redirect(url_for('dashboard'))

        return render_template('login.html', error='Invalid username or password')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# --- Dashboard --------------------------------------------------------------

@app.route('/dashboard')
def dashboard():
    guard = _require_login()
    if guard:
        return guard

    balance = get_balance(session['customer_id'])
    username = session.get('username', 'Customer')

    # Read and clear any post-redirect success message
    success = session.pop('success', None)

    return render_template('dashboard.html', balance=balance, username=username, success=success)


# --- Deposit ----------------------------------------------------------------

@app.route('/deposit', methods=['GET', 'POST'])
def deposit_route():
    guard = _require_login()
    if guard:
        return guard

    if request.method == 'POST':
        amount_str = request.form.get('amount', '').strip()
        ok, result = deposit(session['customer_id'], amount_str)
        if ok:
            session['success'] = f'Deposit of ${result:,.2f} was successful. New balance: ${result:,.2f}'
            return redirect(url_for('dashboard'))
        return render_template('deposit.html', error=result)

    return render_template('deposit.html')


# --- Withdraw ---------------------------------------------------------------

@app.route('/withdraw', methods=['GET', 'POST'])
def withdraw_route():
    guard = _require_login()
    if guard:
        return guard

    current_balance = get_balance(session['customer_id'])

    if request.method == 'POST':
        amount_str = request.form.get('amount', '').strip()

        # Validation: amount must be provided
        if not amount_str:
            return render_template('withdraw.html', error='Amount is required', balance=current_balance)

        # Validation: amount must be a positive number
        try:
            amount_val = float(amount_str)
        except ValueError:
            amount_val = 0
        if amount_val <= 0:
            return render_template('withdraw.html', error='Amount must be greater than zero', balance=current_balance)

        # Validation: amount must not exceed current balance
        if amount_val > current_balance:
            return render_template('withdraw.html', error='Insufficient funds', balance=current_balance)

        ok, result = withdraw(session['customer_id'], amount_str)
        if ok:
            session['success'] = f'Withdrawal of ${float(amount_str):,.2f} was successful. New balance: ${result:,.2f}'
            return redirect(url_for('dashboard'))
        return render_template('withdraw.html', error=result, balance=current_balance)

    return render_template('withdraw.html', balance=current_balance)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    app.run(debug=True)
