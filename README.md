# Smart Support Desk

[![CI](https://github.com/arunsanjeevms/Smart-Support-Desk/actions/workflows/ci.yml/badge.svg)](https://github.com/arunsanjeevms/Smart-Support-Desk/actions/workflows/ci.yml)

A small, complete support desk: **requesters** report software issues, the **support team** works the queue,
changes the status and writes resolution notes. Every table can be searched, sorted, filtered and exported to
**PDF**, **Excel** or **e-mail**, and every option in the UI (categories, priorities, statuses, ...) is managed by
the backend.

| | |
|---|---|
| **Frontend** | Angular 21 (standalone components, signals, zoneless) + Angular Material 3 |
| **Backend** | Django 6 + Django REST Framework (JSON REST API) |
| **Database** | MongoDB 8 through the official **Django MongoDB Backend** |
| **Exports** | ReportLab (PDF), openpyxl (Excel), Django e-mail (SMTP / console) |
| **CI** | GitHub Actions - backend + frontend tests, build, e-mail with the result |

---

## Contents

1. [Features](#features)
2. [Quick start (Windows, no Docker)](#quick-start-windows-no-docker)
3. [MongoDB configuration](#mongodb-configuration)
4. [Demo accounts and sample data](#demo-accounts-and-sample-data)
5. [Architecture](#architecture)
6. [Data model (ER diagram)](#data-model-er-diagram)
7. [Configuration managed in the backend](#configuration-managed-in-the-backend)
8. [Tables, exports and e-mail](#tables-exports-and-e-mail)
9. [API reference](#api-reference)
10. [Running the tests](#running-the-tests)
11. [Continuous integration and e-mail notifications](#continuous-integration-and-e-mail-notifications)
12. [Key design decisions](#key-design-decisions)
13. [Limitations and next steps](#limitations-and-next-steps)

More documentation:

- [docs/PROJECT_GUIDE.md](docs/PROJECT_GUIDE.md) - a guided tour of the code for people new to Angular, Django or MongoDB
- [docs/DEMO.md](docs/DEMO.md) - a 3-minute demo script (ticket creation → status update → resolution)

---

## Features

**Two roles**

| Capability | Requester | Support agent |
|---|:---:|:---:|
| Sign up / sign in (one-click demo accounts) | ✅ | ✅ |
| Create a ticket (title, description, category, priority) with validation | ✅ | ✅ |
| See tickets | Own tickets | All tickets |
| Filter by status, category, priority, assignee, created date | ✅ | ✅ |
| Ticket detail with activity timeline and comments | ✅ | ✅ |
| Change status *Open → In Progress → Resolved* (and re-open) | | ✅ |
| Write a resolution note (required to resolve) | | ✅ |
| Assign / re-assign, change priority or category | | ✅ |
| Dashboard | Own numbers | Queue, workload, resolution time |
| Activity log (audit trail) | | ✅ |
| User directory | | ✅ |
| Manage categories / priorities (Configuration screen) | | ✅ |
| Django admin (users, agents, configuration, tickets) | | Admin only |

**Every table** (tickets, activity log, users, configuration values) has server-side **search**, **sorting**,
**pagination** and **filters**, plus **Export → PDF / Excel / Email report**. Exports always contain exactly what the
table shows (same search, filters and sort order).

**Also included:** requester e-mail notification when a ticket changes status, human-friendly ticket references
(`SSD-1001`), helpful validation messages from both the UI and the API, loading / empty / error states, responsive
layout, keyboard-accessible tables.

---

## Quick start (Windows, no Docker)

### Prerequisites

| Tool | Version | Check |
|---|---|---|
| Python | 3.12 or newer | `python --version` |
| Node.js | 22.12+ or 24+ | `node --version` |
| MongoDB Server | 6.0 or newer, running locally (the server behind MongoDB Compass) | Windows *Services* shows **MongoDB Server** as *Running* |
| Git | any recent | `git --version` |

### 1. Get the code

```powershell
git clone https://github.com/arunsanjeevms/Smart-Support-Desk.git
cd Smart-Support-Desk
```

### 2. Backend (Django API) - terminal #1

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env            # macOS/Linux: cp .env.example .env
python manage.py migrate          # creates the collections + default categories/priorities
python manage.py seed_demo        # demo users and ~28 realistic tickets
python manage.py runserver        # http://localhost:8000
```

Check it works: <http://localhost:8000/api/health/> should return `{"status": "ok", "database": "up"}`.

### 3. Frontend (Angular) - terminal #2

```powershell
cd frontend
npm install
npm start                         # http://localhost:4200
```

Open <http://localhost:4200> and click one of the demo accounts on the sign-in page.

> The Angular app talks to `http://localhost:8000/api` (see `frontend/src/environments/`). If you change the
> backend port, update that file and `CORS_ALLOWED_ORIGINS` in `backend/.env`.

### Useful commands

| What | Command (inside `backend/` with the venv active) |
|---|---|
| Reset demo data | `python manage.py seed_demo --reset` |
| Create your own admin | `python manage.py createsuperuser` |
| Django admin | <http://localhost:8000/admin/> (demo admin: `admin` / `Admin@12345`) |
| Browsable API | <http://localhost:8000/api/> (sign in to the admin first) |

---

## MongoDB configuration

The backend reads two settings from `backend/.env`:

```ini
MONGODB_URI=mongodb://127.0.0.1:27017     # the same connection string you use in MongoDB Compass
MONGODB_NAME=smart_support_desk           # database name - created automatically
```

> Use `127.0.0.1` rather than `localhost`. A default MongoDB install on Windows only listens on IPv4
> (`bindIp: 127.0.0.1` in `mongod.cfg`), and `localhost` can resolve to the IPv6 address `::1`, which is refused.

### Viewing the data in MongoDB Compass

Compass only lists connections you have saved, so on a fresh install the list is empty even though the server is
running. Add one once:

1. Open **MongoDB Compass** → click **+ Add new connection** (or **New connection**).
2. In **URI** enter `mongodb://127.0.0.1:27017` and give it a name, e.g. *Local MongoDB*.
3. Click **Save & Connect**. The connection now stays in the left sidebar.
4. Expand **smart_support_desk** to browse the collections below (run `migrate` and `seed_demo` first).
   Click a collection, e.g. `tickets_ticket`, and filter with `{ "status": "open" }`.

If Compass says *connect ECONNREFUSED*: open **Services** (`Win + R` → `services.msc`), find **MongoDB Server**, and
click **Start**.

Using MongoDB Atlas or a password-protected server? Put the full connection string in `MONGODB_URI`, e.g.
`mongodb+srv://user:password@cluster0.example.mongodb.net/?retryWrites=true`.

After `migrate` + `seed_demo`, refresh Compass and you will see the `smart_support_desk` database with these
collections:

| Collection | Contents |
|---|---|
| `accounts_user` | users (requesters, agents, admin) |
| `lookups_lookuptype` / `lookups_lookupvalue` | configurable lists - categories, priorities |
| `tickets_ticket` | tickets |
| `tickets_ticketactivity` | activity log / timeline (status changes, assignments, comments) |
| `core_counters` | atomic counter used for ticket references (`SSD-1001`, `SSD-1002`, ...) |
| `authtoken_token` | API tokens of signed-in users |
| `auth_*`, `django_*` | Django's built-in tables (permissions, sessions, admin log, migrations) |

---

## Demo accounts and sample data

`python manage.py seed_demo` creates (all safe to re-run):

| Role | Username | Password |
|---|---|---|
| Requester | `riya` (also `karthik`, `emily`, `daniel`) | `Demo@12345` |
| Support agent | `meera` (also `sam`) | `Demo@12345` |
| Admin (agent + Django admin) | `admin` | `Admin@12345` |

…and 28 realistic tickets across all categories and priorities, with a mix of *Open*, *In Progress* and *Resolved*
tickets, resolution notes, comments and a complete activity history spread over the last six weeks.

The sign-in page shows one-click demo buttons. They are controlled by the backend (`DEMO_MODE=True` in `.env`) and
only appear for accounts that exist.

---

## Architecture

```mermaid
flowchart LR
    subgraph Browser
        A[Angular 21 SPA<br/>Material UI, signals]
    end
    subgraph Backend["Django 6 + DRF"]
        B[REST API<br/>/api/...]
        S[Service layer<br/>ticket workflow, activity log]
        X[Export engine<br/>PDF / Excel / e-mail]
        ADM[Django admin]
    end
    DB[(MongoDB<br/>smart_support_desk)]
    MAIL[[SMTP / console]]

    A -- "JSON + Token auth" --> B
    B --> S
    B --> X
    S --> DB
    X --> DB
    ADM --> DB
    X -- attachments --> MAIL
    S -- status e-mails --> MAIL
```

```
Smart-Support-Desk/
├── backend/                     Django project
│   ├── config/                  settings, URL map, MongoDB app configs
│   ├── apps/
│   │   ├── core/                shared code: base model, ObjectId serializers, errors,
│   │   │   └── exports/         pagination, atomic counters, the PDF/Excel/e-mail export engine
│   │   ├── accounts/            custom User (role), login/register/logout, user directory
│   │   ├── lookups/             generic configurable lists (categories, priorities, ...)
│   │   └── tickets/             Ticket + TicketActivity models, services, API, seed command
│   ├── mongo_migrations/        Django's built-in migrations adapted to ObjectId keys
│   ├── requirements.txt
│   └── .env.example
├── frontend/                    Angular workspace
│   └── src/app/
│       ├── core/                API/auth/config services, interceptor, guards, models
│       ├── shared/              DataTable, export menu, badges, avatar, dialogs, pipes
│       ├── layout/              app shell (sidebar + top bar)
│       └── features/            auth, dashboard, tickets, activity, users, configuration
├── docs/                        project guide and demo script
└── .github/workflows/ci.yml     tests + build + result e-mail
```

---

## Data model (ER diagram)

```mermaid
erDiagram
    USER ||--o{ TICKET : "raises (created_by)"
    USER |o--o{ TICKET : "is assigned (assigned_to)"
    USER |o--o{ TICKET : "resolves (resolved_by)"
    USER |o--o{ TICKET_ACTIVITY : "performs (actor)"
    TICKET ||--o{ TICKET_ACTIVITY : "has history"
    LOOKUP_TYPE ||--o{ LOOKUP_VALUE : "contains"
    LOOKUP_VALUE ||--o{ TICKET : "category"
    LOOKUP_VALUE |o--o{ TICKET : "priority"

    USER {
        ObjectId _id PK
        string username UK
        string email UK
        string first_name
        string last_name
        string role "requester | agent"
        string job_title
        bool is_active
        datetime date_joined
    }
    TICKET {
        ObjectId _id PK
        string reference UK "SSD-1001"
        string title "5-150 chars"
        string description "20-5000 chars"
        ObjectId category_id FK
        ObjectId priority_id FK
        string status "open | in_progress | resolved"
        string resolution_note "required to resolve"
        ObjectId created_by_id FK
        ObjectId assigned_to_id FK
        ObjectId resolved_by_id FK
        datetime resolved_at
        datetime created_at
        datetime updated_at
    }
    TICKET_ACTIVITY {
        ObjectId _id PK
        ObjectId ticket_id FK
        ObjectId actor_id FK
        string activity_type "created | status_changed | assigned | commented | ..."
        string message
        string from_status
        string to_status
        string note "comment or resolution text"
        datetime created_at
    }
    LOOKUP_TYPE {
        ObjectId _id PK
        string code UK "ticket_category | ticket_priority"
        string name
        string description
        bool is_system
    }
    LOOKUP_VALUE {
        ObjectId _id PK
        ObjectId lookup_type_id FK
        string code "unique per type"
        string label
        string description
        string icon "Material Symbols name"
        string color "#RRGGBB"
        int sort_order
        bool is_active
        bool is_default
    }
```

Ticket status workflow (business rules live in `backend/apps/tickets/`):

```mermaid
stateDiagram-v2
    [*] --> Open: requester submits
    Open --> InProgress: agent starts work (auto-assigns)
    Open --> Resolved: agent resolves (note required)
    InProgress --> Resolved: agent resolves (note required)
    InProgress --> Open: back to queue
    Resolved --> InProgress: re-opened
    Resolved --> Open: re-opened
```

---

## Configuration managed in the backend

Nothing selectable in the UI is hard-coded in Angular. On sign-in the app calls `GET /api/config/` and builds every
form, filter and badge from the response:

| Option | Where it is defined | How to change it |
|---|---|---|
| **Ticket categories** | `LookupValue` rows of type `ticket_category` | Configuration screen (agents) or Django admin → *Configuration* |
| **Ticket priorities** | `LookupValue` rows of type `ticket_priority` | same as above |
| Category / priority icon, colour, order, default, active | fields on each `LookupValue` | same as above |
| Ticket statuses + allowed transitions | `apps/tickets/constants.py` (business rules depend on them) | code - served to the UI via `/api/config/` |
| Validation limits (title/description length, ...) | `apps/tickets/constants.py` | code - served to the UI via `/api/config/` |
| Roles | `User.Role` | Django admin (create agents, change roles) |
| Demo accounts, export row limit, e-mail notifications | `backend/.env` | environment variables |

**Generic lookup pattern.** `LookupType` describes a list (e.g. *Ticket category*), `LookupValue` holds its options.
To add a brand-new configurable list later (say *Product area*), add one `LookupType` row and reference it from a
model - no new tables, admin screens or UI components are needed. Values that are already used by tickets cannot be
deleted (the API answers `409 Conflict` and suggests deactivating instead), so history is never broken.

---

## Tables, exports and e-mail

**Live data.** The dashboard and every table reload themselves in the background every 30 seconds (and as soon as you
return to the browser tab). The reload is silent: rows stay on screen, nothing flickers, and a failed refresh keeps the
current data. A small "Updated 10:42:05 AM" badge shows when the data was last refreshed. The interval is
`AUTO_REFRESH_MS` in `frontend/src/app/core/utils/auto-refresh.ts`.

All tables use one reusable Angular `DataTable` component backed by a `TableSource` that keeps search, sort, page
and filters in signals and calls the API. Sorting, searching, filtering and paging all run **in Django/MongoDB**,
so they work the same for 30 or 300,000 rows.

Every list endpoint gets two extra endpoints from a single backend mixin (`apps/core/exports/ExportMixin`):

| Endpoint | Result |
|---|---|
| `GET /api/<table>/export/?file_type=pdf` | landscape PDF with title, filters summary, zebra rows, page numbers |
| `GET /api/<table>/export/?file_type=xlsx` | Excel sheet with styled header, frozen header row, auto-filter |
| `POST /api/<table>/export/email/` `{"file_type": "pdf", "recipients": ["a@b.com"], "subject": "", "message": ""}` | the same file sent as an e-mail attachment |

Both accept the same query parameters as the list (search, ordering, filters). Requesters can only ever export their
own tickets because exports reuse the role-aware queryset.

**E-mail delivery.** By default e-mails are printed in the Django terminal (`console` backend) so nothing is sent by
accident. To really send mail with Gmail:

1. Turn on 2-step verification for the Google account and create an **App password**.
2. In `backend/.env` set:

   ```ini
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   EMAIL_HOST_USER=your.address@gmail.com
   EMAIL_HOST_PASSWORD=your-16-character-app-password
   DEFAULT_FROM_EMAIL=Smart Support Desk <your.address@gmail.com>
   ```

3. Restart `runserver`. Export e-mails and status-change notifications are now delivered.

---

## API reference

All endpoints are under `http://localhost:8000/api/`. Send `Authorization: Token <token>` (returned by login).
Errors always look like `{"message": "...", "errors": {"field": ["..."]}}`.

| Method | Endpoint | Who | Purpose |
|---|---|---|---|
| GET | `/health/` | anyone | API + MongoDB health |
| POST | `/auth/login/` | anyone | `{username or email, password}` → `{token, user}` |
| POST | `/auth/register/` | anyone | create a requester account → `{token, user}` |
| POST | `/auth/logout/` | signed in | invalidate the token |
| GET | `/auth/me/` | signed in | current user |
| GET | `/auth/demo-accounts/` | anyone | demo sign-in buttons (when `DEMO_MODE`) |
| GET | `/config/` | signed in | statuses, categories, priorities, agents, validation limits |
| GET | `/tickets/` | signed in | list - `search`, `ordering`, `page`, `page_size`, `status` (comma separated), `category`, `priority`, `assigned_to` (`me`, `unassigned`, id), `created_from`, `created_to` |
| POST | `/tickets/` | signed in | create `{title, description, category, priority?}` |
| GET | `/tickets/{id}/` | owner or agent | detail (+ `allowed_statuses`, `can_manage`) |
| PATCH | `/tickets/{id}/` | agent | `{status?, resolution_note?, assigned_to?, priority?, category?}` |
| GET | `/tickets/{id}/activities/` | owner or agent | timeline |
| POST | `/tickets/{id}/comments/` | owner or agent | `{message}` |
| GET | `/tickets/stats/` | signed in | dashboard numbers (scoped to the user) |
| GET | `/activities/` | agent | audit log - `activity_type` filter |
| GET | `/users/` | agent | user directory - `role` filter |
| GET | `/lookups/types/` | signed in | configurable lists |
| GET, POST, PATCH, DELETE | `/lookups/values/` | read: signed in, write: agent | values - `type`, `is_active` filters |
| GET / POST | `/<table>/export/`, `/<table>/export/email/` | as the table | exports (see above) |

---

## Running the tests

```powershell
# Backend - 63 API tests against a temporary MongoDB database (test_smart_support_desk)
cd backend
.venv\Scripts\activate
python manage.py test

# Frontend - Vitest unit tests + production build
cd frontend
npm run test:ci
npm run build
```

The backend tests cover authentication and roles, ticket validation messages, visibility rules, search / filter /
sort / pagination, the status workflow (resolution note required, auto-assignment, re-opening), notifications,
comments, configuration CRUD and the "in use" delete guard, the atomic reference counter, and PDF/Excel/e-mail
exports (opening the generated workbook to check its rows).

---

## Continuous integration and e-mail notifications

`.github/workflows/ci.yml` runs on every push to `main`, on pull requests and on demand:

1. **Backend** - installs Python 3.13, starts a temporary MongoDB 8 service, runs Django checks, verifies there are
   no missing migrations, runs the test suite and the seed command.
2. **Frontend** - installs Node 24, runs the unit tests and a production build.
3. **Email the result** - always runs and e-mails a summary (per-job result, commit, link to the logs) to
   `msarunsanjeev@gmail.com`.

To enable the e-mail, add two repository secrets in **GitHub → Settings → Secrets and variables → Actions**:

| Secret | Value |
|---|---|
| `MAIL_USERNAME` | the Gmail address that sends the mail |
| `MAIL_PASSWORD` | a Gmail **App password** for that account |

Until the secrets exist the step is skipped with a notice, so the pipeline stays green.

---

## Key design decisions

1. **Django MongoDB Backend instead of plain PyMongo.** The official backend lets us keep Django's ORM, migrations,
   authentication, the admin and Django REST Framework while storing everything in MongoDB. That gave us user roles,
   token auth, an admin for configuration and model validation for free. PyMongo is still used directly where
   MongoDB shines: the ticket reference counter uses an atomic `findOneAndUpdate` + `$inc`, so two requests can never
   get the same `SSD-` number even without multi-document transactions.
2. **No reliance on transactions.** A standalone MongoDB server (what Compass usually connects to) does not support
   multi-document transactions, and the backend treats `atomic()` as a no-op. Writes are therefore designed to be
   safe one by one: the ticket is saved first and the activity entries are append-only.
3. **Generic configuration tables** (`LookupType` / `LookupValue`) instead of one table per dropdown. New categories
   or whole new lists need no code change, icons/colours/order live with the data, and the UI reads everything from
   `/api/config/`.
4. **Statuses stay in code but are served by the API.** The workflow rules (resolve needs a note, allowed transitions,
   auto-assign) depend on them, so they are not editable data - yet the frontend still never hard-codes them.
5. **Business rules in a service layer** (`apps/tickets/services.py`), not in views or serializers. The API, the seed
   command and the tests all go through the same functions, and every change writes an activity entry.
6. **Activity log as its own collection** rather than an array embedded in the ticket: it can be searched, sorted,
   paginated and exported across all tickets like any other table.
7. **Server-side tables and exports.** Search, sort, filter and pagination run in the database, and exports are
   generated by the backend from the same queryset - consistent results, role-aware by construction, and they scale.
8. **One error format** for the whole API (`message` + per-field `errors`) so the Angular forms can show the backend's
   message right under the matching field.
9. **Angular with standalone components, signals and lazy routes.** Each page is downloaded only when opened
   (≈140 kB initial transfer). Reusable building blocks (DataTable, ExportMenu, badges) keep the pages small.
10. **Token authentication with two roles** (`requester`, `agent`). It is simple, stateless for the SPA and easy to test.
    Agents are created by an administrator; self sign-up always creates requesters.

---

## Limitations and next steps

- **Similar-ticket suggestions** (text similarity on resolved tickets) are not part of this version. The ticket form,
  `/api/config/` and the service layer are structured so a `/api/tickets/similar/` endpoint and a suggestions panel
  can be added without touching the existing flows.
- Search uses case-insensitive regular expressions. For very large data sets a MongoDB text or Atlas Search index
  would be faster.
- Exports are generated synchronously and capped at `EXPORT_MAX_ROWS` (5,000 by default). A background job queue
  would be the next step for much larger exports.
- No file attachments, SLA timers or real-time updates yet.
- Tokens do not expire; JWT with refresh tokens would be the next step before a public deployment.
