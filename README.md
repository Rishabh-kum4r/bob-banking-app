# SecureBank — Banking Web Application

A lightweight, browser-based banking application built with Python Flask and SQLite.  
Customers can log in, view their account balance, and perform deposit and withdrawal transactions.

---

## Project Structure

```
Banking_System/
├── FRONTEND/
│   └── templates/          ← Jinja2 HTML templates (Bootstrap 5)
│       ├── login.html
│       ├── dashboard.html
│       ├── deposit.html
│       └── withdraw.html
│
├── BACKEND/
│   ├── app.py              ← Flask entry point & route definitions
│   ├── services.py         ← Business logic (auth, balance, transactions)
│   ├── database.py         ← SQLite connection helper
│   ├── models.py           ← Table creation & seed data
│   ├── requirements.txt    ← Python dependencies
│   ├── banking.db          ← SQLite database (auto-created on first run)
│   └── tests/
│       ├── test_services.py  ← Unit tests (22 tests)
│       └── test_routes.py    ← Integration tests (23 tests)
│
├── README.md
└── .gitignore
```

---

## One-Time Setup

### Prerequisites
- Python 3.9 or higher (`py --version`)
- pip (included with Python)

### 1. Create the virtual environment

```powershell
# From the workspace root (Banking_System/)
py -m venv BACKEND\venv
```

### 2. Activate the virtual environment

**Windows (PowerShell):**
```powershell
BACKEND\venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
BACKEND\venv\Scripts\activate.bat
```

**macOS / Linux:**
```bash
source BACKEND/venv/bin/activate
```

### 3. Install dependencies

```powershell
pip install -r BACKEND\requirements.txt
```

---

## Running the Application

```powershell
# From the workspace root, with venv active:
BACKEND\venv\Scripts\python.exe BACKEND\app.py
```

Flask will start a development server:

```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

Open a browser and navigate to **http://localhost:5000**

The login page will appear automatically (the root `/` redirects to `/login`).

---

## Seed Credentials

| Username | Password    | Starting Balance |
|----------|-------------|-----------------|
| `admin`  | `password123` | $1,000.00      |

These credentials are pre-loaded into the database on first run.

---

## Available Pages

| URL          | Description                              |
|--------------|------------------------------------------|
| `/login`     | Customer login form                      |
| `/dashboard` | Account balance overview (protected)     |
| `/deposit`   | Deposit funds form (protected)           |
| `/withdraw`  | Withdraw funds form (protected)          |
| `/logout`    | Clears session and returns to login      |

---

## Running Tests

With the virtual environment active, run from the workspace root:

```powershell
BACKEND\venv\Scripts\python.exe -m pytest BACKEND\tests\ -v
```

Expected result: **45 passed** (22 unit tests + 23 integration tests)

---

## Resetting the Database

If the database becomes corrupted or you want to start fresh:

1. Stop the server (`Ctrl + C`)
2. Delete `BACKEND\banking.db`
3. Restart the server — tables and seed data are recreated automatically

---

## Stopping the Server

Press `Ctrl + C` in the terminal running `app.py`.

---

## Production Notes

The built-in Flask development server is **not suitable for production**. Before deploying:

- Replace `app.secret_key` with a value read from an environment variable
- Set `debug=False`
- Use a production WSGI server (Gunicorn, Waitress)
- Use PostgreSQL or MySQL instead of SQLite for multi-user load
- Serve over HTTPS via a reverse proxy (Nginx, Caddy)
