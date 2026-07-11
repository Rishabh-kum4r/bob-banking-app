# Banking Web Application — Build Plan

> **Reference:** `STEP_BY_STEP_IMPLEMENTATION_GUIDE.md` · `IMPLEMENTATION_PLAN.md`
> **Status:** Planning

---

## Top-Level Overview

Build a complete, locally-runnable Flask-based banking web application that lets a customer log in, view their balance, deposit funds, and withdraw funds. The app uses a strict three-tier architecture: Jinja2 HTML templates in `FRONTEND/templates/`, Python Flask routes + service logic in `BACKEND/`, and a SQLite file database at `BACKEND/banking.db`.

The build follows the 7-phase roadmap in the Implementation Plan. Each sub-task below maps to one phase and is designed to be implemented, reviewed, and confirmed independently before the next begins.

---

## Sub-Tasks

---

### Sub-Task 1 — Project Scaffold & Environment Setup

**Intent:** Create the folder structure, Python virtual environment, and `requirements.txt`. This establishes the workspace layout that all other sub-tasks depend on.

**Expected Outcomes:**
- `FRONTEND/templates/` folder exists.
- `BACKEND/` folder exists with `requirements.txt` listing `Flask` and `Werkzeug`.
- `BACKEND/venv/` Python virtual environment is created.
- Dependencies are installed inside the venv.
- A `.gitignore` at the workspace root excludes `venv/` and `banking.db`.

**Todo List:**
1. Create `FRONTEND/templates/` directory.
2. Create `BACKEND/` directory.
3. Create `BACKEND/requirements.txt` with `Flask` and `Werkzeug` entries.
4. Create `BACKEND/venv/` Python virtual environment using `python -m venv venv`.
5. Install dependencies via `pip install -r requirements.txt` inside the venv.
6. Create a `.gitignore` at the workspace root excluding `venv/` and `banking.db`.

**Relevant Context:**
- Guide Section 1 (1.1–1.5)
- Plan Section 4 (Folder Structure)

**Status:** [x] done

---

### Sub-Task 2 — Database Layer

**Intent:** Build the SQLite connection helper and the models initialisation file. These are the foundation for all data access and must be in place before any route or service is written.

**Expected Outcomes:**
- `BACKEND/database.py` exposes a `get_connection()` function that opens a connection to `BACKEND/banking.db` using a path resolved relative to the file's own location.
- `BACKEND/models.py` contains an `init_db()` function that:
  - Creates a `customers` table (columns: `id`, `username`, `password_hash`).
  - Creates an `accounts` table (columns: `id`, `customer_id` FK, `balance`).
  - Inserts one seed customer (`admin` / `password123` hashed with Werkzeug) with a starting balance of `1000.00` if the tables are empty.
  - Is idempotent — safe to call multiple times.

**Todo List:**
1. Create `BACKEND/database.py` with a `get_connection()` function using `os.path` to resolve the DB path.
2. Create `BACKEND/models.py` with an `init_db()` function covering table creation and seed data.
3. Hash the seed password using `werkzeug.security.generate_password_hash`.

**Relevant Context:**
- Guide Sections 2.1–2.2
- Plan Section 3 (Database Responsibilities)
- Schema: `customers(id, username, password_hash)` · `accounts(id, customer_id, balance)`

**Status:** [x] done

---

### Sub-Task 3 — Authentication Backend (Routes + Service Logic)

**Intent:** Implement login/logout Flask routes and the authentication service function. This is the first end-to-end slice of the app and gating mechanism for all protected pages.

**Expected Outcomes:**
- `BACKEND/services.py` exists with `authenticate_customer(username, password)` that:
  - Returns `(False, None)` for missing username/password or unmatched credentials.
  - Returns `(True, customer_id)` for valid credentials.
- `BACKEND/app.py` exists with:
  - Flask app configured with a secret key and `template_folder` pointing to `../FRONTEND/templates`.
  - `init_db()` called at startup.
  - `GET /login` renders `login.html`; redirects to dashboard if already logged in.
  - `POST /login` calls `authenticate_customer`, sets `session['customer_id']`, redirects to `/dashboard`.
  - `GET /logout` calls `session.clear()` and redirects to `/login`.
  - A `_require_login()` guard helper used in all protected routes.

**Todo List:**
1. Create `BACKEND/services.py` with `authenticate_customer(username, password)`.
2. Implement validation rules from Section 5.1 (presence check, then credential match).
3. Create `BACKEND/app.py` with Flask app factory, secret key, template folder path.
4. Call `init_db()` in `app.py` at startup.
5. Implement `GET /login`, `POST /login`, `GET /logout` routes.
6. Write `_require_login()` helper that redirects to `/login` when `customer_id` is absent from session.
7. Add `if __name__ == '__main__': app.run(debug=True)` guard.

**Relevant Context:**
- Guide Sections 2.3–2.5, 5.1
- Plan Sections 5 (Auth Module), 6 (Phase 3)

**Status:** [x] done

---

### Sub-Task 4 — Dashboard Backend

**Intent:** Add the balance retrieval service and the dashboard route. This completes the core read path of the application.

**Expected Outcomes:**
- `services.py` gains `get_balance(customer_id)` that queries the `accounts` table and returns the numeric balance.
- `GET /dashboard` route in `app.py` applies `_require_login()`, calls `get_balance`, passes `balance` and `username` to `dashboard.html`; also reads and clears a `success` message from the session if present.

**Todo List:**
1. Add `get_balance(customer_id)` to `BACKEND/services.py`.
2. Add `GET /dashboard` route to `app.py` with session guard.
3. Fetch the customer username from the session (store it at login time).
4. Read and clear any `session['success']` message to pass to the template.

**Relevant Context:**
- Guide Sections 2.6, 4.5
- Plan Section 5 (Dashboard Module)
- Template variable: `balance`, `username`, `success` (see Guide Table 3.6)

**Status:** [ ] pending

---

### Sub-Task 5 — Transactions Backend (Deposit & Withdraw)

**Intent:** Add deposit and withdrawal service functions and their corresponding routes. This completes the write path and enforces all business validation rules.

**Expected Outcomes:**
- `services.py` gains `deposit(customer_id, amount)` and `withdraw(customer_id, amount)`, each applying the validation rules from Sections 5.3 and 5.4.
- `deposit` returns `(True, new_balance)` on success or `(False, error_string)` on failure.
- `withdraw` returns `(True, new_balance)` on success or `(False, error_string)` on failure, including the insufficient-funds case.
- `GET /deposit`, `POST /deposit`, `GET /withdraw`, `POST /withdraw` routes added to `app.py`.
- Successful transactions store a success message in `session['success']` before redirecting to `/dashboard`.
- Failed transactions re-render the form with the `error` variable.

**Todo List:**
1. Add `deposit(customer_id, amount)` to `services.py` with full validation chain (Section 5.3).
2. Add `withdraw(customer_id, amount)` to `services.py` with full validation chain (Section 5.4).
3. Add `GET /deposit` and `POST /deposit` routes to `app.py`.
4. Add `GET /withdraw` and `POST /withdraw` routes to `app.py`; pass current balance to the withdraw template.
5. On success: set `session['success']` message and `redirect('/dashboard')`.
6. On failure: re-render form template with `error` variable.

**Relevant Context:**
- Guide Sections 2.7–2.8, 5.2–5.5
- Plan Section 5 (Transactions Module)

**Status:** [x] done

---

### Sub-Task 6 — Frontend Templates

**Intent:** Build the four Jinja2 HTML pages styled with Bootstrap 5 and wired to the backend variable conventions established in the previous sub-tasks.

**Expected Outcomes:**
- `FRONTEND/templates/login.html` — Bootstrap card, username + password form, conditional `alert-danger` for `error`.
- `FRONTEND/templates/dashboard.html` — Welcome message with `username`, formatted `balance`, Deposit/Withdraw/Logout links, conditional `alert-success` for `success`.
- `FRONTEND/templates/deposit.html` — Amount input form, conditional `alert-danger` for `error`, Back to Dashboard link.
- `FRONTEND/templates/withdraw.html` — Amount input form, optional balance display, conditional `alert-danger` for `error`, Back to Dashboard link.
- All templates use Bootstrap 5 CDN, responsive `container → row → col-md-6` layout, and card components.

**Todo List:**
1. Create `FRONTEND/templates/login.html` with form action `/login`, method POST, error alert block.
2. Create `FRONTEND/templates/dashboard.html` with balance display, success alert block, navigation links.
3. Create `FRONTEND/templates/deposit.html` with form action `/deposit`, method POST, error alert block.
4. Create `FRONTEND/templates/withdraw.html` with form action `/withdraw`, method POST, balance display, error alert block.
5. Verify template variable names match the conventions in Guide Table 3.6: `error`, `success`, `balance`, `username`.

**Relevant Context:**
- Guide Sections 3.1–3.6
- Bootstrap 5 CDN: `https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css`

**Status:** [x] done

---

### Sub-Task 7 — Automated Tests

**Intent:** Add unit tests for service functions and integration tests for Flask routes to verify correctness of all business logic and HTTP flows.

**Expected Outcomes:**
- `BACKEND/tests/` folder with `test_services.py` (unit) and `test_routes.py` (integration).
- Unit tests cover all cases listed in Guide Section 6.1 using an in-memory SQLite database.
- Integration tests cover all cases listed in Guide Section 6.2 using Flask's test client.
- All tests pass when run with `python -m pytest` from inside `BACKEND/`.

**Todo List:**
1. Create `BACKEND/tests/__init__.py`.
2. Create `BACKEND/tests/test_services.py` with unit tests for `authenticate_customer`, `deposit`, and `withdraw` using in-memory SQLite.
3. Create `BACKEND/tests/test_routes.py` with integration tests using `app.test_client()` and a test database.
4. Add `pytest` to `requirements.txt`.
5. Confirm all tests pass.

**Relevant Context:**
- Guide Section 6.1–6.2
- Test isolation: use `sqlite3.connect(':memory:')` or a temp file; never use `banking.db`.

**Status:** [ ] pending

---

### Sub-Task 8 — Integration Verification & Startup Instructions

**Intent:** Smoke-test the full end-to-end application manually, confirm the manual testing checklist passes, and add a clear `README.md` with startup instructions.

**Expected Outcomes:**
- Application starts cleanly with `python app.py` from `BACKEND/` (venv active).
- Login with seed credentials (`admin` / `password123`) works.
- Deposit and withdrawal flows work end-to-end with correct balance updates.
- Session is destroyed on logout; back-button navigation after logout redirects to login.
- `README.md` at workspace root explains how to set up and run the app.

**Todo List:**
1. Run the application and walk through the full manual testing checklist (Guide Section 6.3).
2. Fix any wiring issues discovered during smoke testing.
3. Create `README.md` at workspace root with:
   - One-time setup steps (create venv, install requirements).
   - Run command (`python app.py`).
   - Seed credentials.
   - How to reset the database.

**Relevant Context:**
- Guide Sections 7.1–7.2
- Manual checklist: Guide Section 6.3

**Status:** [x] done

---

## Implementation Notes

- All sub-tasks must be implemented in order (1 → 8); each depends on the previous.
- After each sub-task, update its `Status` from `[ ] pending` to `[x] done` before moving on.
- No SQL or business logic should appear inside `app.py` route handlers — delegate to `services.py`.
- Password hashing must use `werkzeug.security.generate_password_hash` / `check_password_hash`.
- Template folder path in `app.py` must point to `../FRONTEND/templates` (relative to `BACKEND/app.py`).
- The session key for the logged-in user is `customer_id`; username should also be stored in session at login time for display on the dashboard.
