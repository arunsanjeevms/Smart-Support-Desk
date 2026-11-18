# Smart Support Desk

[![CI](https://github.com/arunsanjeevms/Smart-Support-Desk/actions/workflows/ci.yml/badge.svg)](https://github.com/arunsanjeevms/Smart-Support-Desk/actions/workflows/ci.yml)

A small, complete support desk: **requesters** report software issues, the **support team** works the queue,
changes the status and writes resolution notes. While a ticket is being written, an **open-source language model
running locally** suggests up to three similar tickets that were already resolved. Every table can be searched,
sorted, filtered and exported to **PDF**, **Excel** or **e-mail**, and every option in the UI (categories,
priorities, statuses, ...) is managed by the backend.

| | |
|---|---|
| **Frontend** | Angular 21 (standalone components, signals, zoneless) + Angular Material 3 |
| **Backend** | Django 6 + Django REST Framework (JSON REST API) |
| **Database** | MongoDB 8 through the official **Django MongoDB Backend** |
| **AI** | Sentence Transformers (`all-MiniLM-L6-v2`, open source) on the CPU, inside the Django backend |
| **Exports** | ReportLab (PDF), openpyxl (Excel), Django e-mail (SMTP / console) |
| **CI** | GitHub Actions - backend + frontend tests, build, e-mail with the result |

Full list with versions and the reason for each choice: [docs/TECH_STACK.md](docs/TECH_STACK.md).

---

## Contents

1. [Features](#features)
2. [Quick start (Windows, no Docker)](#quick-start-windows-no-docker)
3. [MongoDB configuration](#mongodb-configuration)
4. [Environment variables](#environment-variables)
5. [Demo accounts and sample data](#demo-accounts-and-sample-data)
6. [Architecture](#architecture)
7. [Data model (ER diagram)](#data-model-er-diagram)
8. [Configuration managed in the backend](#configuration-managed-in-the-backend)
9. [Tables, exports and e-mail](#tables-exports-and-e-mail)
10. [Similar ticket suggestions (AI)](#similar-ticket-suggestions-ai)
11. [API reference](#api-reference)
12. [Security](#security)
13. [Running the tests](#running-the-tests)
14. [Continuous integration and e-mail notifications](#continuous-integration-and-e-mail-notifications)
15. [Key design decisions](#key-design-decisions)
16. [Limitations and next steps](#limitations-and-next-steps)

More documentation:

| Document | What is inside |
|---|---|
| [docs/TECH_STACK.md](docs/TECH_STACK.md) | every technology with its version, what it is used for and why; security measures; runtime requirements |
| [docs/WORKFLOWS.md](docs/WORKFLOWS.md) | role capabilities, end-to-end ticket workflow, status lifecycle, sequence diagrams (sign-in, raising, resolving, comments, exports, configuration), e-mail notification flow, request pipeline, CI pipeline |
| [docs/ER_DIAGRAMS.md](docs/ER_DIAGRAMS.md) | ER diagrams of every collection, relationships, indexes, data rules and example documents |
| [docs/SCREENS.md](docs/SCREENS.md) | every screen with what to capture and an explanation, a screenshot checklist and a suggested outline for a submission document |
| [docs/PROJECT_GUIDE.md](docs/PROJECT_GUIDE.md) | a guided tour of the code for people new to Angular, Django or MongoDB |
| [docs/DEMO.md](docs/DEMO.md) | a 3-minute demo script (ticket creation → status update → resolution) |

---

## Features

**Two roles**

| Capability | Requester | Support agent |
|---|:---:|:---:|
| Sign up / sign in (one-click demo accounts) | ✅ | ✅ |
| Create a ticket (title, description, category, priority) with validation | ✅ | ✅ |
| Ask for up to 3 similar resolved tickets while writing one, and open their details | ✅ | ✅ |
| See similar resolved tickets on an open ticket and reuse a resolution note | | ✅ |
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

**Also included:**

- E-mail notifications for six ticket events (ticket received, new ticket alert, assigned, status changed, new
  comment, details changed), each switchable on the Configuration screen.
- Human-friendly ticket references (`SSD-1001`) from an atomic MongoDB counter.
- Helpful validation messages from both the UI and the API, shown under the matching field.
- Live data: the dashboard and every table refresh themselves every 30 seconds, with an *Updated* time badge.
- Loading, empty and error states on every screen, a friendly *Page not found* page, and page titles in the
  browser tab.
- Responsive layout (slide-out menu on phones) and keyboard-accessible tables.
- Small touches: a short welcome animation after signing in, a time-of-day greeting in the top bar and dashboard
  numbers that count up.

Every screen is described, with what to capture for screenshots, in [docs/SCREENS.md](docs/SCREENS.md).

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
pip install -r requirements.txt   # includes PyTorch (CPU) for the AI suggestions - about 1 GB
copy .env.example .env            # macOS/Linux: cp .env.example .env
python manage.py migrate          # creates the collections + default categories/priorities
python manage.py seed_demo        # demo users, ~28 realistic tickets, downloads the AI model once (~90 MB)
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
| Receive the demo accounts' e-mails in your inbox | `python manage.py seed_demo --inbox you@gmail.com` (riya gets `you+riya@gmail.com`, ...) |
| Create your own admin | `python manage.py createsuperuser` |
| Try the AI matching from the terminal | `python manage.py similar_tickets "The analytics page is painfully slow to open"` |
| (Re)build the similar-ticket index | `python manage.py build_similarity_index` (`--force` to encode everything again) |
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
| `similarity_ticketembedding` | cached AI embeddings of resolved tickets, for similar ticket suggestions |
| `authtoken_token` | API tokens of signed-in users |
| `auth_*`, `django_*` | Django's built-in tables (permissions, sessions, admin log, migrations) |

---

## Environment variables

All backend settings are read from `backend/.env` (copy `backend/.env.example`). Every variable has a default, so
the app runs with an empty file except for real e-mail delivery.

| Variable | Default | Meaning |
|---|---|---|
| `DJANGO_SECRET_KEY` | a development-only key | secret used to sign data; set a long random value outside development |
| `DJANGO_DEBUG` | `True` | debug pages and relaxed CORS for any local port |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | host names Django answers to |
| `DJANGO_TIME_ZONE` | `Asia/Kolkata` | time zone for dates, filters and e-mails |
| `MONGODB_URI` | `mongodb://127.0.0.1:27017` | MongoDB connection string (local, password-protected or Atlas) |
| `MONGODB_NAME` | `smart_support_desk` | database name |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:4200,http://127.0.0.1:4200` | where the Angular app is served from |
| `EMAIL_BACKEND` | console | `django.core.mail.backends.smtp.EmailBackend` to really send |
| `EMAIL_HOST` / `EMAIL_PORT` / `EMAIL_USE_TLS` | `smtp.gmail.com` / `587` / `True` | SMTP server |
| `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` | empty | SMTP account (for Gmail an App password) |
| `DEFAULT_FROM_EMAIL` | `Smart Support Desk <no-reply@smartsupportdesk.local>` | sender of every e-mail |
| `FRONTEND_URL` | `http://localhost:4200` | used for the *View ticket* links in e-mails |
| `TICKET_REFERENCE_PREFIX` | `SSD` | prefix of ticket references (numbers start at 1000) |
| `EXPORT_MAX_ROWS` | `5000` | maximum rows in one export |
| `EMAIL_NOTIFICATIONS` | `True` | master switch for all notification e-mails |
| `DEMO_MODE` | `True` | one-click demo sign-in buttons on the login page |
| `AUTH_THROTTLE_RATE` | `30/minute` | sign-in and sign-up attempts per client |
| `SIMILAR_THROTTLE_RATE` | `60/minute` | similar ticket searches per user |
| `SIMILARITY_ENABLED` | `True` | show similar ticket suggestions |
| `SIMILARITY_ENGINE` | `semantic` | `semantic` (the model) or `keyword` (TF-IDF only) |
| `SIMILARITY_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | any Sentence Transformers model |
| `SIMILARITY_MAX_RESULTS` | `3` | number of suggestions (never more than 3) |
| `SIMILARITY_MIN_SCORE` | `0.35` | minimum cosine similarity for the model |
| `SIMILARITY_KEYWORD_MIN_SCORE` | `0.15` | minimum score for the keyword fallback |
| `SIMILARITY_PRELOAD` | `True` | load the model in the background when the server starts, so the first search is instant |

The frontend has one setting, the API address, in `frontend/src/environments/environment*.ts`.

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
        AI[Similarity engine<br/>Sentence Transformers, CPU]
        ADM[Django admin]
    end
    DB[(MongoDB<br/>smart_support_desk)]
    MAIL[[SMTP / console]]

    A -- "JSON + Token auth" --> B
    B --> S
    B --> X
    B --> AI
    AI --> DB
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
│   │   ├── tickets/             Ticket + TicketActivity models, services, API, seed command
│   │   └── similarity/          similar-ticket suggestions: model, embedding cache, commands
│   ├── mongo_migrations/        Django's built-in migrations adapted to ObjectId keys
│   ├── requirements.txt
│   └── .env.example
├── frontend/                    Angular workspace
│   └── src/app/
│       ├── core/                API/auth/config services, interceptor, guards, models
│       ├── shared/              DataTable, export menu, badges, avatar, dialogs, pipes
│       ├── layout/              app shell (sidebar + top bar)
│       └── features/            auth, dashboard, tickets, activity, users, configuration
├── docs/                        tech stack, workflows, ER diagrams, screen guide, project guide, demo script
└── .github/workflows/ci.yml     tests + build + result e-mail
```

---

## Data model (ER diagram)

A summary of the collections. [docs/ER_DIAGRAMS.md](docs/ER_DIAGRAMS.md) has the full version with every
field, delete rules, indexes and example documents.

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
    TICKET ||--o| TICKET_EMBEDDING : "cached for suggestions"

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
    TICKET_EMBEDDING {
        ObjectId _id PK
        ObjectId ticket_id FK,UK "resolved ticket"
        string model_name "all-MiniLM-L6-v2"
        string text_hash "sha256 of title + description"
        float[] vector "384 numbers"
        datetime updated_at
    }
    LOOKUP_TYPE {
        ObjectId _id PK
        string code UK "ticket_category | ticket_priority | notification_event"
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

Who can make each move, what it records and which e-mail it sends, plus sequence diagrams for every main action, are
in [docs/WORKFLOWS.md](docs/WORKFLOWS.md).

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
| **E-mail notifications** (which actions send an e-mail) | `LookupValue` rows of type `notification_event` | Configuration screen → *Email notifications* (switch each event on/off) |
| Demo accounts, export row limit, e-mail notifications | `backend/.env` | environment variables |
| Similar ticket suggestions (on/off, model, minimum score) | `backend/.env` (`SIMILARITY_*`) | environment variables |

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
| `GET /api/<table>/export/?file_type=pdf` | branded landscape PDF set in Poppins: running header and footer, a title block with a summary strip (records, generated, prepared by, filters), coloured status/priority, "Page x of y" |
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

All e-mails are HTML (with a plain-text version) and share one branded layout. The templates are in
`backend/apps/core/templates/emails/`. The "View ticket" buttons link to `FRONTEND_URL` (default
`http://localhost:4200`); set it in `backend/.env` when the app runs somewhere else.

---

### Notification e-mails

Every ticket action can send an e-mail. Each event is a row in the **Email notifications** list on the
Configuration screen: switch it off to stop that e-mail, or rename it. `EMAIL_NOTIFICATIONS=False` in `backend/.env`
turns all of them off at once.

| Event | Sent to |
|---|---|
| Ticket received | the requester (confirmation with their description) |
| New ticket alert | every active support agent |
| Ticket assigned | the agent it was assigned to (not when agents assign themselves) |
| Status changed | the requester, including the resolution note when resolved |
| New comment | the requester when an agent comments; the assignee (or the whole team if unassigned) when the requester comments |
| Ticket details changed | the requester when the category or priority changes |

Nobody is e-mailed about their own action. E-mails are sent in the background so the app stays fast, and
addresses on reserved demo domains (`example.com`, `*.test`, ...) are skipped. To receive the demo e-mails
yourself, give a demo user your real address in the Django admin.

---

## Similar ticket suggestions (AI)

While someone writes a new ticket they can click **Find similar tickets**. The backend compares their title and
description with every **resolved** ticket and returns at most **three** that look alike, each with its resolution
note. A suggestion opens in a dialog, so the draft is never lost. Agents get the same list on every open ticket and
can copy a resolution note into the Manage form with **Use this note**.

The suggestions are **advisory**. Nothing is closed or changed automatically, every card says it may not fit the
issue, and the ticket can always be submitted. Only the problem, its category and the resolution are shared: never
who raised the old ticket.

### How it works

1. **An open-source model, running locally.** [`sentence-transformers/all-MiniLM-L6-v2`](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
   (Apache 2.0) runs on the CPU inside Django through the `sentence-transformers` library. It is downloaded once
   (about 90 MB) and then loaded from the local cache, so no ticket text ever leaves the server.
2. **Text to numbers.** The model turns `"<title>. <description>"` into an *embedding*: 384 numbers that describe
   the meaning of the text. Texts that mean the same thing get similar numbers even when they share no words.
3. **Cached embeddings.** Each resolved ticket is encoded once and stored in the `similarity_ticketembedding` collection,
   with the model name and a hash of the text. A ticket is only encoded again if its text or the model changes.
4. **Ranking.** The new text is encoded and compared with every resolved ticket by **cosine similarity** (0 =
   unrelated, 1 = same meaning). Matches under `SIMILARITY_MIN_SCORE` (0.35) are dropped and the best three are
   returned. Scores of 0.60 and above are labelled *strong*.
5. **Fallback.** If the model cannot be loaded (for example no internet for the first download), the same endpoint
   falls back to TF-IDF keyword matching and the UI says so.

The code is in `backend/apps/similarity/` (`engines.py` for the model and the keyword fallback, `services.py` for
caching and ranking) and `frontend/src/app/features/tickets/similar-tickets/`.

### Different wording, same problem

Real scores on the demo data (`python manage.py similar_tickets "<text>"` prints this comparison). The new issues
share almost no words with the resolved tickets, yet the model ranks the right one first. Keyword matching misses
them, or picks the wrong ticket:

| New issue typed by the user | Resolved ticket suggested by the model | Model score | Keyword matching |
|---|---|:---:|---|
| "The analytics page is painfully slow to open" | Dashboard takes more than a minute to load | **0.68** | 0.10, not suggested |
| "Unable to get into my account since I changed my credentials" | Cannot log in after resetting my password | **0.66** | 0.08, not suggested |
| "The verification number from my phone is never valid" | Two-factor codes not accepted | **0.48** | 0.00, suggests *Invoice PDF is missing our GST number* instead |
| "I was billed two times for this month's plan" | Charged twice for the monthly subscription | **0.68** | 0.27 |
| "The office printer is out of toner" | *nothing* (best is 0.28, under 0.35) | - | - |

The first four are also automated tests (`apps/similarity/tests/test_similarity.py`) that run the real model in CI.

### Settings (`backend/.env`)

| Variable | Default | Meaning |
|---|---|---|
| `SIMILARITY_ENABLED` | `True` | show the suggestions at all |
| `SIMILARITY_ENGINE` | `semantic` | `semantic` (the model) or `keyword` (TF-IDF only, no model) |
| `SIMILARITY_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | any Sentence Transformers model name |
| `SIMILARITY_MAX_RESULTS` | `3` | how many suggestions (never more than 3) |
| `SIMILARITY_MIN_SCORE` | `0.35` | minimum cosine similarity for a suggestion |

---

## API reference

All endpoints are under `http://localhost:8000/api/`. Send `Authorization: Token <token>` (returned by login).
Errors always look like `{"message": "...", "errors": {"field": ["..."]}}`.

| Status | Meaning |
|---|---|
| `400` | validation failed - `errors` has a message per field |
| `401` | missing or invalid token - the app goes back to the sign-in page |
| `403` | signed in, but the role is not allowed (e.g. a requester changing a ticket) |
| `404` | not found, or not visible to this user (a requester opening someone else's ticket) |
| `409` | a configuration value is used by tickets, or is built in, and cannot be deleted |
| `429` | too many sign-in attempts or similar ticket searches - try again in a minute |

List endpoints return `{"count", "page", "page_size", "total_pages", "results"}`. Pages hold 10 rows by default;
`page_size` changes it (up to 100).

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
| POST | `/tickets/similar/` | signed in | `{title?, description?, exclude?}` → up to 3 similar resolved tickets with `score` and `match`, plus `engine` and `model` |
| GET | `/activities/` | agent | audit log - `activity_type` filter |
| GET | `/users/` | agent | user directory - `role` filter |
| GET | `/lookups/types/` | signed in | configurable lists |
| GET, POST, PATCH, DELETE | `/lookups/values/` | read: signed in, write: agent | values - `type`, `is_active` filters |
| GET / POST | `/<table>/export/`, `/<table>/export/email/` | as the table | exports (see above) |

---

## Security

| Area | How it is handled |
|---|---|
| Passwords | hashed by Django; at least 8 characters, not common, not only digits, not close to the username |
| Authentication | one API token per user in the `Authorization` header; signing out deletes it on the server |
| Roles | requesters only see and export their own tickets; activity log, users and configuration changes are agents only, checked by the API and by Angular route guards |
| Sign-up | always creates a requester; agents are created by an administrator |
| Rate limits | sign-in / sign-up 30 per minute, similar ticket searches 60 per minute (`429` after that) |
| Validation | every input is validated by the API, and again in the browser for quick feedback |
| CORS | only the configured frontend origins may call the API |
| AI privacy | the model runs on the server, nothing is sent to an outside service; suggestions never show who raised the old ticket |
| Secrets | in `backend/.env` (ignored by Git) and GitHub repository secrets |

More detail in [docs/TECH_STACK.md](docs/TECH_STACK.md#8-security-measures).

---

## Running the tests

```powershell
# Backend - 90 tests against a temporary MongoDB database (test_smart_support_desk)
cd backend
.venv\Scripts\activate
python manage.py test

# Frontend - 37 Vitest unit tests + production build
cd frontend
npm run test:ci
npm run build
```

The backend tests cover authentication and roles, ticket validation messages, visibility rules, search / filter /
sort / pagination, the status workflow (resolution note required, auto-assignment, re-opening), notifications,
comments, configuration CRUD and the "in use" delete guard, the atomic reference counter, PDF/Excel/e-mail
exports (opening the generated workbook to check its rows), and the similar-ticket suggestions: ranking, the limit
of three, that nothing is changed, the embedding cache, and the real model matching differently worded issues.

The frontend tests cover the auth service, mapping API errors onto form fields, the table state (`TableSource`), the
status badge, the relative time pipe, the count-up numbers, the welcome animation and the similar tickets panel.

---

## Continuous integration and e-mail notifications

`.github/workflows/ci.yml` runs on every push to `main`, on pull requests and on demand:

1. **Backend** - installs Python 3.13 and the CPU build of PyTorch, starts a temporary MongoDB 8 service, runs Django
   checks, verifies there are no missing migrations, runs the test suite and the seed command. The AI model is
   cached between runs.
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
11. **A small local model with cached embeddings for suggestions.** `all-MiniLM-L6-v2` is fast on a normal CPU
    (milliseconds per ticket), open source and needs no API key or external service. Embeddings are cached per
    ticket, so a search only encodes the new text. The comparison runs in numpy because a local MongoDB server has no
    vector search; that is fast for tens of thousands of resolved tickets.

---

## Limitations and next steps

- Similar-ticket suggestions compare against all resolved tickets in memory. With millions of tickets, a vector
  index (MongoDB Atlas Vector Search) would replace the numpy comparison. The default model is English only; a
  multilingual Sentence Transformers model can be set with `SIMILARITY_MODEL`.
- Search uses case-insensitive regular expressions. For very large data sets a MongoDB text or Atlas Search index
  would be faster.
- Exports are generated synchronously and capped at `EXPORT_MAX_ROWS` (5,000 by default). A background job queue
  would be the next step for much larger exports.
- No file attachments or SLA timers yet. Screens refresh every 30 seconds; pushing changes instantly (WebSockets)
  would be the next step.
- Tokens do not expire; JWT with refresh tokens would be the next step before a public deployment.
