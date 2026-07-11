# Banking Web Application — Step-by-Step Implementation Guide

> **Reference:** [`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md)  
> **Status:** Planning  
> **Output of:** P2 — Implementation Guide  
> **Next step:** P3 — Full Application Build (Agent Mode)

---

## How to Use This Guide

Work through each section in order. Every section maps to a phase from the Implementation Roadmap in `IMPLEMENTATION_PLAN.md`. Each step describes **what to do and why** — it does not contain source code. Use this guide as the instruction set when switching to Agent Mode to build the application.

---

## Section 1 — Environment Setup

### 1.1 Create the Project Folder Structure

Before installing anything, create the two top-level application folders — `FRONTEND` and `BACKEND` — at the root of the `Banking_System` workspace. Inside `FRONTEND`, create a sub-folder called `templates`. This is where all HTML pages will live. The `BACKEND` folder will hold all Python files and the database.

This folder separation enforces the architectural boundary described in the Implementation Plan: the browser layer and the server layer are never mixed in the same directory.

### 1.2 Set Up a Python Virtual Environment

Inside the `BACKEND` folder, create a Python virtual environment. A virtual environment isolates the project's Python dependencies from any other Python projects on the same machine. This prevents version conflicts and makes the project self-contained.

Name the virtual environment `venv`. Once created, activate it in the terminal before running any other Python or pip commands. On Windows the activation command is in `venv\Scripts\activate`; on macOS/Linux it is `venv/bin/activate`.

### 1.3 Create the Requirements File

Before installing Flask, create a plain text file named `requirements.txt` inside the `BACKEND` folder. List the following dependencies in it, one per line:

- **Flask** — the web framework that handles routing, request handling, and template rendering.
- **Werkzeug** — Flask's underlying utility library; used for password hashing. It is installed automatically with Flask but should be listed explicitly.

Listing dependencies in `requirements.txt` means anyone can recreate the environment with a single install command and ensures the same versions are used every time.

### 1.4 Install Dependencies

With the virtual environment active, run the pip install command pointing at `requirements.txt`. Pip will download and install Flask and all its sub-dependencies into the virtual environment. Verify the installation succeeded by running a quick command to check the installed Flask version.

### 1.5 Verify the Setup

Confirm the environment is correct by checking three things:
1. The correct Python version is active (3.9 or higher).
2. Flask is importable from the Python interpreter.
3. The folder structure matches the layout in the Implementation Plan.

---

## Section 2 — Backend Implementation

### 2.1 Create the Database Helper (`database.py`)

The first backend file to create is the database helper. Its sole job is to open a connection to the SQLite database file and close it cleanly. It should expose two things: a function that returns an open connection to `banking.db`, and a function (or context) that ensures the connection is closed after each request.

SQLite is a file-based database — no server process is needed. The database file (`banking.db`) is created automatically the first time a connection is opened to it. Store the file path as a constant so it can easily be changed later.

### 2.2 Create the Database Models and Seed Data (`models.py`)

The models file is responsible for two things on application startup:

**Table creation:** Check whether the required tables exist; if they do not, create them. This is an idempotent operation — running it multiple times should not cause errors or data loss. The two tables needed are one for customer credentials and one for account balances.

**Seed data:** After ensuring the tables exist, check whether any customer records are present. If the database is empty, insert at least one test customer with a pre-set username, a hashed password, and a starting balance. The password must be stored as a hash — never as plain text. Use Werkzeug's password hashing utility for this.

The models file should be called once when the Flask application starts, before any requests are served.

### 2.3 Create the Flask Application Entry Point (`app.py`)

`app.py` is the heart of the backend. When building it, follow this order:

**Initialise the Flask app:** Create the Flask application object. Set a secret key on it — this key is used by Flask to sign the session cookie. Without it, sessions will not work. For development, a hard-coded string is acceptable.

**Register the template folder:** Tell Flask where to find HTML templates. Because the templates live in `FRONTEND/templates/` rather than the default `templates/` folder, the template folder path must be passed explicitly when creating the Flask app object.

**Call the database initialisation:** Import and call the models initialisation function so that tables and seed data are created before the first request arrives.

**Register routes:** Define URL route functions for every page — login (GET and POST), logout (GET), dashboard (GET), deposit (GET and POST), and withdraw (GET and POST). Each route function should delegate work to the service layer and then either render a template or issue a redirect.

**Run the app:** At the bottom of the file, add the standard `if __name__ == '__main__'` guard and call `app.run()` with `debug=True` for development. This ensures the file can be executed directly to start the server.

### 2.4 Build the Authentication Routes and Logic

**GET /login:** Render the login page template. If the user is already logged in (check the session), redirect them straight to the dashboard so they do not see the login form again.

**POST /login:** Read the username and password from the submitted form data. Pass them to the authentication service function. If authentication succeeds, store the customer's identifier in the Flask session object and redirect to the dashboard. If it fails, re-render the login page and pass an error message variable to the template so the user sees feedback.

**GET /logout:** Clear the entire Flask session using the session's `clear()` method. After clearing, redirect the user to the login page. Clearing the session is what FR-05 and NFR-04 require — no session data persists after logout.

### 2.5 Build the Session Guard

Every protected route (dashboard, deposit, withdraw) must check that a valid session exists before doing any work. The standard Flask pattern is to write a helper function or decorator that checks for the expected session key. If the key is absent, the helper redirects to `/login` immediately.

Apply this guard at the top of every protected route handler. This single mechanism satisfies FR-06 (unauthenticated requests redirect to login).

### 2.6 Build the Dashboard Route

**GET /dashboard:** Apply the session guard first. Then call the service function that retrieves the current balance for the logged-in customer. Pass the balance value (and the customer's name if desired) to the dashboard template for display. This route is read-only — it never modifies data.

### 2.7 Build the Transaction Routes

**GET /deposit and GET /withdraw:** Apply the session guard. Render the respective form template. No database interaction is needed for these GET requests.

**POST /deposit:** Apply the session guard. Read the amount from the form. Pass the amount and the session's customer identifier to the deposit service function. On success, redirect to the dashboard. On validation failure, re-render the deposit form with an error message.

**POST /withdraw:** Apply the session guard. Read the amount from the form. Pass it to the withdrawal service function. On success, redirect to the dashboard. On failure (invalid input or insufficient funds), re-render the withdraw form with a specific error message explaining the problem.

### 2.8 Build the Services Layer (`services.py`)

The services file contains all business logic. It imports the database helper but has no Flask imports — it knows nothing about HTTP requests or sessions. This clean separation means the logic can be tested without running a web server.

Write one function per business operation:

**`authenticate_customer(username, password)`** — Query the database for a customer record matching the username. If no record is found, return a failure result. If a record is found, use Werkzeug's password-checking utility to compare the submitted password against the stored hash. Return a success result with the customer's identifier, or a failure result.

**`get_balance(customer_id)`** — Query the accounts table for the balance belonging to the given customer identifier. Return the balance value as a number.

**`deposit(customer_id, amount)`** — Validate the amount (see Section 5). Retrieve the current balance. Add the deposit amount to it. Write the new balance back to the database. Return a success result.

**`withdraw(customer_id, amount)`** — Validate the amount (see Section 5). Retrieve the current balance. Check that the balance is greater than or equal to the requested withdrawal amount. If not, return a failure result with an insufficient-funds message. If yes, subtract the amount and write the new balance to the database. Return a success result.

### 2.9 Error Handling

For user-facing errors (wrong password, invalid amount, insufficient funds), pass an error string as a template variable so the page can display it in a styled alert box. Do not use HTTP error pages for these — they should be inline form errors.

For unexpected errors (database not found, missing session key in an unexpected state), Flask's default error handling is sufficient for development. A generic "something went wrong" message is acceptable.

---

## Section 3 — Frontend Implementation

All four HTML pages follow the same structural pattern: a Bootstrap 5 navbar at the top, a centred content card in the middle, and a flash/alert area between the navbar and the card for feedback messages.

### 3.1 Bootstrap Layout Approach

Every template should start by loading Bootstrap 5 from its CDN. Place the Bootstrap CSS `<link>` tag in the `<head>`. Place the Bootstrap JS `<script>` tag just before the closing `</body>` tag.

Use Bootstrap's grid system (container → row → col) to centre content on the page. A single column of width `col-md-6` offset to the centre works well for form pages. Use Bootstrap card components (`card`, `card-body`, `card-title`) to frame each form in a clean box.

Because Flask serves Jinja2 templates, every HTML file can use `{{ variable }}` to output dynamic values and `{% if error %}...{% endif %}` blocks to conditionally show alerts.

### 3.2 Login Page (`login.html`)

The login page contains a single form with two input fields — one for username (text type) and one for password (password type) — and a submit button labelled "Login".

The form's `action` attribute points to `/login` and its `method` is `POST`. This means submitting the form sends the credentials to Flask's `POST /login` route.

Above the form, include a conditional block that renders a Bootstrap danger alert (`alert alert-danger`) only when the template receives a non-empty error variable. This is how the "invalid credentials" message appears without a page reload.

### 3.3 Dashboard Page (`dashboard.html`)

The dashboard is a read-only display page. It shows:
- A welcome message that includes the customer's name (passed from the route).
- The current account balance, prominently displayed and formatted as currency.
- Three action buttons or links: one to `/deposit`, one to `/withdraw`, and one to `/logout`.

If a success message was passed to the template (e.g., "Deposit successful"), display it in a Bootstrap success alert (`alert alert-success`) at the top of the card. This gives the user feedback after completing a transaction.

### 3.4 Deposit Form (`deposit.html`)

The deposit page contains a single form with one numeric input field for the deposit amount and a submit button labelled "Deposit".

The form's `action` points to `/deposit` and its `method` is `POST`. Include a "Back to Dashboard" link so users can navigate away without submitting.

Include the same conditional error alert pattern used on the login page — if the route passes an error string, display it above the form so the user understands why their deposit was rejected.

### 3.5 Withdraw Form (`withdraw.html`)

The withdraw page is structurally identical to the deposit page. Change the heading, button label, and form action to reflect withdrawal. The error alert pattern is the same.

Optionally, display the current balance on this page (passed from the route) so the customer knows their limit before they type an amount. This is a minor UX improvement that avoids the "insufficient funds" error in many cases.

### 3.6 Template Variable Conventions

Agree on consistent variable names between the routes and templates so there is no confusion during wiring:

| Template Variable | Meaning | Set by |
|---|---|---|
| `error` | Error message string or None | Every route that can fail |
| `success` | Success message string or None | Dashboard route (post-redirect) |
| `balance` | Numeric account balance | Dashboard and Withdraw routes |
| `username` | Logged-in customer's display name | Dashboard route |

---

## Section 4 — Integration Steps

### 4.1 Connect Flask to the Template Folder

When constructing the Flask app object, pass the `template_folder` argument pointing to the absolute or relative path of `FRONTEND/templates/`. Flask will then find `login.html`, `dashboard.html`, etc. when `render_template()` is called. Verify this works by running the app and navigating to `/login` — if the page renders without a "template not found" error, the wiring is correct.

### 4.2 Connect Flask to SQLite

The database helper opens a connection to `banking.db` located in the `BACKEND/` folder. Use Python's `os.path` utilities to construct the path to the database file relative to the location of `database.py` — this ensures the path resolves correctly regardless of which directory the server is started from.

Ensure the models initialisation function is called inside the Flask app factory (in `app.py`) before the first request is served. This guarantees the tables exist whenever the app starts, even on a fresh machine.

### 4.3 Connect Routes to Services

Each route function in `app.py` should import and call exactly the service functions it needs from `services.py`. The route's job is: (1) read form data, (2) call a service, (3) act on the result. No SQL or business logic should appear inside a route function.

### 4.4 Connect Services to the Database Helper

Each service function in `services.py` should import the connection function from `database.py` and use it to open a connection, execute the required query, and close the connection. Keep each service function's database interaction self-contained — open, query, close, return result.

### 4.5 Pass Flash Messages Across Redirects

After a successful deposit or withdrawal, the route redirects to `/dashboard`. The challenge is passing a success message across a redirect — the template variables set in the current request are lost on redirect. Use Flask's built-in `flash()` mechanism or store a short message in the session before redirecting, then read and clear it in the dashboard route. This gives the user a "Deposit of $X was successful" confirmation on the dashboard page.

---

## Section 5 — Validation Rules

All validation logic lives in `services.py`, not in the route handlers or templates.

### 5.1 Login Validation

| Rule | What to Check | Error to Return |
|---|---|---|
| Username not empty | The submitted username field is not blank | "Username is required" |
| Password not empty | The submitted password field is not blank | "Password is required" |
| Credentials match | Username exists in database and password hash matches | "Invalid username or password" |

Always return the same generic message for both "username not found" and "wrong password". Returning different messages for each case reveals information about which usernames exist in the system.

### 5.2 Balance Validation

The balance check is used inside the withdrawal service:

| Rule | What to Check | Error to Return |
|---|---|---|
| Sufficient funds | Current balance ≥ requested withdrawal amount | "Insufficient funds. Your current balance is $X" |

### 5.3 Deposit Validation

| Rule | What to Check | Error to Return |
|---|---|---|
| Amount provided | The form field is not empty | "Deposit amount is required" |
| Amount is numeric | The value can be converted to a number | "Deposit amount must be a number" |
| Amount is positive | The numeric value is greater than zero | "Deposit amount must be greater than zero" |
| Amount is reasonable | The value does not exceed a sensible ceiling (e.g., 1,000,000) | "Deposit amount exceeds the allowed limit" |

### 5.4 Withdrawal Validation

| Rule | What to Check | Error to Return |
|---|---|---|
| Amount provided | The form field is not empty | "Withdrawal amount is required" |
| Amount is numeric | The value can be converted to a number | "Withdrawal amount must be a number" |
| Amount is positive | The numeric value is greater than zero | "Withdrawal amount must be greater than zero" |
| Sufficient funds | Current balance ≥ requested amount | "Insufficient funds. Your current balance is $X" |

### 5.5 Validation Order

Always validate in this order: (1) presence check, (2) type check, (3) range/business check. Stop at the first failure and return that error — do not accumulate multiple errors for these simple single-field forms.

---

## Section 6 — Testing

### 6.1 Unit Tests

Unit tests exercise individual service functions in isolation, without running the web server or using a real database.

**What to test in `services.py`:**
- `authenticate_customer` returns a success result when given valid credentials.
- `authenticate_customer` returns a failure result for an unknown username.
- `authenticate_customer` returns a failure result for a correct username but wrong password.
- `deposit` correctly adds an amount and returns the new balance.
- `deposit` rejects a zero or negative amount.
- `withdraw` correctly subtracts an amount when funds are sufficient.
- `withdraw` returns an insufficient-funds error when balance is too low.
- `withdraw` rejects a zero or negative amount.

**How to structure them:** Use Python's built-in `unittest` module or `pytest`. For each test, set up a temporary in-memory SQLite database (or a test-specific `banking.db` file), insert a known test record, call the service function, and assert the return value.

### 6.2 Integration Tests

Integration tests exercise the Flask routes end-to-end using Flask's built-in test client. The test client simulates HTTP requests without needing a running server.

**What to test:**
- `GET /login` returns a 200 status and the login page HTML.
- `POST /login` with valid credentials redirects to `/dashboard`.
- `POST /login` with invalid credentials returns a 200 with an error message in the body.
- `GET /dashboard` without a session redirects to `/login`.
- `GET /dashboard` with a valid session returns a 200 and shows a balance.
- `POST /deposit` with a valid amount updates the balance and redirects to `/dashboard`.
- `POST /deposit` with an invalid amount returns a 200 with an error message.
- `POST /withdraw` with a valid amount deducts the balance and redirects.
- `POST /withdraw` with an amount exceeding the balance returns a 200 with an insufficient-funds error.
- `GET /logout` clears the session and redirects to `/login`.

**Test database isolation:** Use a separate test database file (or in-memory SQLite) so integration tests do not corrupt the development database.

### 6.3 Manual Testing Checklist

After all automated tests pass, walk through the application manually in a browser:

**Authentication flow:**
- [ ] Opening `http://localhost:5000` shows the login page (or redirects to it).
- [ ] Submitting blank credentials shows the appropriate error message.
- [ ] Submitting wrong credentials shows the generic "Invalid username or password" message.
- [ ] Submitting correct credentials (from seed data) redirects to the dashboard.

**Dashboard:**
- [ ] The dashboard shows the correct account balance for the logged-in user.
- [ ] Deposit and Withdraw navigation links are visible and clickable.
- [ ] A "Logout" button or link is visible.

**Deposit:**
- [ ] Navigating to `/deposit` shows the deposit form.
- [ ] Submitting a blank amount shows an error.
- [ ] Submitting a negative amount shows an error.
- [ ] Submitting a valid amount redirects to the dashboard with a success message.
- [ ] The balance on the dashboard is increased by the deposited amount.

**Withdrawal:**
- [ ] Navigating to `/withdraw` shows the withdraw form.
- [ ] Submitting a blank amount shows an error.
- [ ] Submitting an amount larger than the balance shows "Insufficient funds".
- [ ] Submitting a valid amount redirects to the dashboard with a success message.
- [ ] The balance on the dashboard is decreased by the withdrawn amount.

**Logout:**
- [ ] Clicking Logout redirects to the login page.
- [ ] Pressing the browser back button and trying to access `/dashboard` redirects to login.

---

## Section 7 — Deployment

### 7.1 Run Locally

To start the application on a local machine:

1. Open a terminal and navigate to the `BACKEND` folder.
2. Activate the virtual environment (`venv\Scripts\activate` on Windows, `source venv/bin/activate` on macOS/Linux).
3. Run the application using `python app.py`.
4. Flask will start a development server, typically on `http://127.0.0.1:5000`.
5. Open a browser and navigate to `http://localhost:5000`. The login page should appear.
6. Use the seed data credentials to log in and verify the application is working.

The development server restarts automatically when Python files are changed (because `debug=True` is set). There is no need to stop and restart manually during development.

To stop the server, press `Ctrl + C` in the terminal.

### 7.2 Environment Notes for Local Development

- The `banking.db` file is created automatically in `BACKEND/` on first run. There is no manual database setup step.
- If the database becomes corrupted or needs to be reset, delete `banking.db` and restart the server. The models initialisation will recreate it with fresh seed data.
- The `venv/` folder and `banking.db` should be excluded from version control. Add both to `.gitignore`.

### 7.3 Production Considerations

The built-in Flask development server is **not suitable for production**. The following changes would be required before deploying to a real environment:

| Concern | Development Approach | Production Approach |
|---|---|---|
| **Web server** | Flask's built-in `app.run()` | A production WSGI server such as Gunicorn or Waitress |
| **Secret key** | Hard-coded string in `app.py` | Read from an environment variable or secrets manager |
| **Database** | SQLite file in the backend folder | A more robust database (PostgreSQL, MySQL) for multi-user load |
| **HTTPS** | Not used | TLS certificate required; typically handled by a reverse proxy (Nginx, Caddy) |
| **Debug mode** | `debug=True` | `debug=False` — never expose debug mode in production |
| **Password hashing** | Werkzeug default settings | Werkzeug settings are acceptable but review bcrypt work-factor |
| **Static files** | Served by Flask | Served by the web server or a CDN |

For the purposes of this lab, only local execution is required. The production considerations above are provided for awareness and would be addressed in a follow-on hardening phase.

---

*End of Step-by-Step Implementation Guide — proceed to Agent Mode (P3) to build the application.*
