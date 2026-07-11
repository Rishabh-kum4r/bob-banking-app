# Banking Web Application — Implementation Plan

> **Status:** Planning  
> **Output of:** P1 — Architecture & Planning  
> **Next document:** `STEP_BY_STEP_IMPLEMENTATION_GUIDE.md`

---

## 1. Solution Overview

### Objective

Build a lightweight, browser-based banking application that allows customers to securely log in, view their account balance, and perform deposit and withdrawal transactions through a clean web interface.

### Scope

| In Scope | Out of Scope |
|---|---|
| Customer login and session management | Multi-factor authentication |
| View current account balance | Account creation / self-registration |
| Deposit funds | Inter-account transfers |
| Withdraw funds | Transaction history / statements |
| Logout | Admin portal |
| Single-page-per-feature UI | Mobile native apps |

### Users

| User Type | Description |
|---|---|
| **Customer** | A bank customer with an existing account who logs in to view balance and perform transactions |

### Functional Requirements

| ID | Requirement |
|---|---|
| FR-01 | A customer must authenticate with a username and password before accessing any feature |
| FR-02 | An authenticated customer can view their current account balance on the dashboard |
| FR-03 | An authenticated customer can deposit a positive monetary amount into their account |
| FR-04 | An authenticated customer can withdraw a monetary amount, provided sufficient funds exist |
| FR-05 | An authenticated customer can log out, which terminates their session |
| FR-06 | Unauthenticated requests to protected pages must redirect to the login page |

### Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR-01 | The application must run locally on a single machine without external services |
| NFR-02 | Pages must be readable and usable on standard desktop browsers |
| NFR-03 | Invalid or unauthorised actions must return a clear error message to the user |
| NFR-04 | Session data must not persist after logout |
| NFR-05 | The codebase must be organised into clearly separated frontend and backend layers |

### Assumptions

- Each customer has exactly one account; no multi-account support is required.
- Seed data (at least one valid customer record) will be pre-loaded into the database so the application can be demonstrated immediately.
- The application runs in a trusted local/development environment; production-grade TLS and secrets management are out of scope.
- Bootstrap CDN is acceptable; no offline/vendor copy is required.
- Python 3.9+ and pip are available in the development environment.

---

## 2. High-Level Architecture

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        BROWSER                              │
│                                                             │
│   ┌──────────────┐   ┌────────────┐   ┌─────────────────┐  │
│   │  login.html  │   │dashboard   │   │deposit /        │  │
│   │              │   │.html       │   │withdraw .html   │  │
│   └──────┬───────┘   └─────┬──────┘   └────────┬────────┘  │
│          │                 │                    │           │
└──────────┼─────────────────┼────────────────────┼───────────┘
           │  HTTP request   │                    │
           ▼                 ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│                  PYTHON FLASK BACKEND                        │
│                                                             │
│  ┌────────────┐  ┌─────────────┐  ┌──────────────────────┐ │
│  │   Auth     │  │  Dashboard  │  │  Transaction         │ │
│  │  Module    │  │  Module     │  │  Module              │ │
│  │ /login     │  │ /dashboard  │  │ /deposit /withdraw   │ │
│  │ /logout    │  │             │  │                      │ │
│  └─────┬──────┘  └──────┬──────┘  └──────────┬───────────┘ │
│        │                │                    │             │
│        └────────────────┴────────────────────┘             │
│                         │                                   │
│              ┌──────────▼──────────┐                        │
│              │   Service / Data    │                        │
│              │   Access Layer      │                        │
│              └──────────┬──────────┘                        │
└─────────────────────────┼───────────────────────────────────┘
                          │  SQL queries
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    SQLITE DATABASE                          │
│              BACKEND/banking.db                             │
│                                                             │
│         customers table   │   accounts table               │
└─────────────────────────────────────────────────────────────┘
```

### Frontend → Backend → Database Interaction

```
Browser                Flask Route            Service Layer         SQLite
   │                       │                       │                  │
   │── POST /login ────────▶│                       │                  │
   │                       │── validate creds ─────▶│                  │
   │                       │                       │── SELECT user ───▶│
   │                       │                       │◀─ user record ────│
   │                       │◀─ auth result ─────────│                  │
   │◀─ redirect/dashboard ─│                       │                  │
   │                       │                       │                  │
   │── GET /dashboard ─────▶│                       │                  │
   │                       │── get balance ─────────▶│                  │
   │                       │                       │── SELECT balance ▶│
   │                       │                       │◀─ balance value ──│
   │◀─ render dashboard ───│                       │                  │
```

### Request Lifecycle

1. **Browser** sends an HTTP request (form submit or page load) to a Flask route.
2. **Flask route handler** checks session validity; unauthenticated requests redirect to `/login`.
3. **Route handler** delegates business logic to the **service layer**.
4. **Service layer** queries or updates the **SQLite database** using the data-access helper.
5. **Route handler** renders a Jinja2 template (or returns a redirect) with the result.
6. **Browser** displays the rendered HTML page to the customer.

---

## 3. Component Design

### Frontend Responsibilities

| Concern | Detail |
|---|---|
| **Presentation** | Render HTML pages styled with Bootstrap 5 — no custom CSS frameworks |
| **Forms** | Collect login credentials, deposit amount, and withdrawal amount via HTML forms |
| **Feedback** | Display success banners and error alerts returned by the backend in the template context |
| **Navigation** | Provide links between dashboard, deposit, withdraw, and logout |
| **State** | Hold no application state; all state lives in the Flask server-side session |
| **Templating** | Jinja2 templates served by Flask — no separate SPA framework required |

### Backend Responsibilities

| Concern | Detail |
|---|---|
| **Routing** | Define URL routes for login, logout, dashboard, deposit, and withdraw |
| **Authentication** | Verify credentials against the database; store user identity in a server-side session |
| **Session management** | Create session on login, destroy session on logout, guard all protected routes |
| **Business logic** | Validate deposit/withdrawal inputs; enforce sufficient-funds rule on withdrawals |
| **Data access** | Abstract all database reads and writes behind service/helper functions |
| **Template rendering** | Pass context variables (balance, error messages) to Jinja2 templates |
| **Error handling** | Return user-friendly error messages on validation failures or unexpected states |

### Database Responsibilities

| Concern | Detail |
|---|---|
| **Persistence** | Store customer credentials and account balances in a file-based SQLite database |
| **Integrity** | Enforce data types and constraints at the database level |
| **Isolation** | Single file (`banking.db`) lives inside the `BACKEND/` folder |
| **Seed data** | Pre-populated with at least one customer account for demonstration |

---

## 4. Folder Structure

```
Banking_System/
│
├── IMPLEMENTATION_PLAN.md          ← This document (planning artefact)
│
├── FRONTEND/                       ← All browser-facing assets
│   └── templates/                  ← Jinja2 HTML templates
│       ├── login.html              ← Login form page
│       ├── dashboard.html          ← Balance display & navigation hub
│       ├── deposit.html            ← Deposit funds form
│       └── withdraw.html           ← Withdraw funds form
│
├── BACKEND/                        ← All server-side Python code
│   ├── app.py                      ← Flask application entry point; route definitions
│   ├── models.py                   ← Database initialisation and schema creation
│   ├── services.py                 ← Business logic (auth, balance, transactions)
│   ├── database.py                 ← SQLite connection helper and query utilities
│   ├── banking.db                  ← SQLite database file (generated at runtime)
│   └── requirements.txt            ← Python dependency list
│
└── docs/                           ← Lab documentation (not part of the application)
    └── demo-setup/
```

### Folder Responsibility Summary

| Folder / File | Responsibility |
|---|---|
| `FRONTEND/templates/` | Contains all HTML pages; served by Flask's template engine |
| `BACKEND/app.py` | Flask app factory, route registration, session guards |
| `BACKEND/services.py` | Pure-Python business logic; no Flask imports |
| `BACKEND/database.py` | Opens the SQLite connection, runs queries, closes connection |
| `BACKEND/models.py` | Creates tables and inserts seed data on first run |
| `BACKEND/banking.db` | Runtime-generated SQLite file; excluded from version control |
| `BACKEND/requirements.txt` | Pinned Python dependencies (`flask`, etc.) |

---

## 5. Module Breakdown

### Authentication Module

**Purpose:** Control who can access the application.

| Item | Detail |
|---|---|
| Pages | `login.html` |
| Routes | `GET /login` — show form · `POST /login` — verify credentials · `GET /logout` — clear session |
| Logic | Hash-compare submitted password against stored credential; set/clear session cookie |
| Guards | Decorator or check at the top of every protected route to redirect unauthenticated users |

### Dashboard Module

**Purpose:** Give the authenticated customer a central view of their account.

| Item | Detail |
|---|---|
| Pages | `dashboard.html` |
| Routes | `GET /dashboard` |
| Logic | Retrieve current balance for the logged-in customer from the database |
| Display | Show account balance; provide navigation links to Deposit, Withdraw, and Logout |

### Account Management Module

**Purpose:** Provide read access to account state.

| Item | Detail |
|---|---|
| Responsibility | Look up the account record associated with the session user |
| Used by | Dashboard module (balance display) and Transaction module (pre/post balance check) |

### Transactions Module

**Purpose:** Process deposits and withdrawals.

| Item | Detail |
|---|---|
| Pages | `deposit.html` · `withdraw.html` |
| Routes | `GET /deposit` · `POST /deposit` · `GET /withdraw` · `POST /withdraw` |
| Logic — Deposit | Validate amount is a positive number; add to current balance; persist to database |
| Logic — Withdraw | Validate amount is a positive number; check balance ≥ amount; deduct and persist |
| Feedback | Redirect to dashboard with a success message, or re-render form with an error message |

---

## 6. Implementation Roadmap

### Development Phases

| Phase | Name | What Gets Built | Dependencies |
|---|---|---|---|
| **1** | Environment Setup | Python virtual environment, Flask installation, project folder scaffold, `requirements.txt` | None |
| **2** | Database Layer | SQLite connection helper, table creation script, seed data | Phase 1 |
| **3** | Backend — Auth | Login and logout routes, session management, credential validation | Phase 2 |
| **4** | Backend — Dashboard & Balance | Dashboard route, balance retrieval service | Phase 3 |
| **5** | Backend — Transactions | Deposit and withdraw routes, business logic, validation | Phase 4 |
| **6** | Frontend — Templates | All four HTML pages styled with Bootstrap; wired to backend routes | Phase 3 (login), Phase 4 (dashboard), Phase 5 (deposit/withdraw) |
| **7** | Integration & Manual Testing | End-to-end smoke test of all user flows in a browser | Phases 1–6 |

### Estimated Effort

| Phase | Relative Effort |
|---|---|
| Environment Setup | Small |
| Database Layer | Small |
| Backend — Auth | Medium |
| Backend — Dashboard & Balance | Small |
| Backend — Transactions | Medium |
| Frontend — Templates | Medium |
| Integration & Manual Testing | Small |

### Dependencies

```
Phase 1 (Environment)
    └── Phase 2 (Database)
            └── Phase 3 (Auth Backend)
                    ├── Phase 4 (Dashboard Backend)
                    │       └── Phase 5 (Transactions Backend)
                    │               └── Phase 6 (Frontend Templates)
                    │                       └── Phase 7 (Integration Testing)
                    └── Phase 6 (Login Template — can start in parallel with Phase 4)
```

**Key dependency rules:**
- No backend route can be written before the database layer exists (Phase 2 before 3+).
- No frontend template can be meaningfully tested before its corresponding backend route exists.
- Integration testing (Phase 7) requires all prior phases to be functionally complete.

---

*End of Implementation Plan — proceed to `STEP_BY_STEP_IMPLEMENTATION_GUIDE.md` for detailed instructions.*
