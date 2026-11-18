<a id="readme-top"></a>

<div align="center">

<img src="docs/assets/readme-banner.svg" alt="Smart Support Desk - raise, track and resolve tickets with local AI" width="100%">

<br>

[![CI](https://github.com/arunsanjeevms/Smart-Support-Desk/actions/workflows/ci.yml/badge.svg)](https://github.com/arunsanjeevms/Smart-Support-Desk/actions/workflows/ci.yml)
![Angular](https://img.shields.io/badge/Angular-21-DD0031?style=flat-square&logo=angular&logoColor=white)
![Django](https://img.shields.io/badge/Django-6.0-092E20?style=flat-square&logo=django&logoColor=white)
![DRF](https://img.shields.io/badge/REST%20Framework-3.18-A30000?style=flat-square&logo=django&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-8-47A248?style=flat-square&logo=mongodb&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=flat-square&logo=python&logoColor=white)
![AI model](https://img.shields.io/badge/AI-all--MiniLM--L6--v2-FFD21E?style=flat-square&logo=huggingface&logoColor=black)
![Tests](https://img.shields.io/badge/tests-112%20backend%20%C2%B7%2051%20frontend-0f766e?style=flat-square)

**A complete help desk: requesters raise tickets, the support team resolves them, and an open-source language model
running inside the backend suggests the category and finds similar fixes.**

[Features](#-features) · [Quick start](#-quick-start) · [Architecture](#-architecture) · [AI](#-ai-similar-tickets-and-category-suggestion) · [API](#-api-reference) · [Docs](#-documentation)

</div>

<br>

| | Technology |
|---|---|
| 🖥️ **Frontend** | Angular 21 (standalone components, signals, zoneless) + Angular Material 3, Poppins, Material Symbols |
| ⚙️ **Backend** | Django 6 + Django REST Framework (JSON REST API, token authentication) |
| 🍃 **Database** | MongoDB 8 through the official **Django MongoDB Backend**; files in **GridFS** |
| 🤖 **AI** | Sentence Transformers (`all-MiniLM-L6-v2`, open source) on the CPU, inside the Django backend |
| 📄 **Exports** | ReportLab (PDF), openpyxl (Excel), Django e-mail (SMTP / console) |
| ✅ **CI** | GitHub Actions - backend + frontend tests, production build, result e-mail |

Every technology with its version and the reason it was chosen: [docs/TECH_STACK.md](docs/TECH_STACK.md).

---

## ✨ Features

<table>
<tr>
<td width="33%" valign="top">

### 🎫 Ticketing
Raise tickets with validation, follow them on a timeline, comment both ways. Agents move tickets
**Open → In Progress → Resolved** with a required resolution note.

</td>
<td width="33%" valign="top">

### 🤖 Local AI
While typing, the **category is suggested** and up to **3 similar resolved tickets** are found - even with
completely different wording. Runs on the CPU; no data leaves the server.

</td>
<td width="33%" valign="top">

### 📎 Attachments
Screenshots, logs and documents on tickets and comments, stored in **MongoDB GridFS**, with image previews and
strict server-side checks.

</td>
</tr>
<tr>
<td valign="top">

### 📊 Tables &amp; exports
Every table has server-side **search, sort, filters and paging**, plus **PDF, Excel and e-mail** exports of
exactly what is on screen.

</td>
<td valign="top">

### ✉️ Notifications
HTML e-mails for six ticket events - each one switchable on the Configuration screen, sent in the background.

</td>
<td valign="top">

### 🎛️ Backend-managed options
Categories, priorities, statuses, limits and e-mail events all come from the backend - **nothing is hard-coded**
in the UI.

</td>
</tr>
</table>

<div align="center">
<img src="docs/assets/readme-workflow.svg" alt="The life of a ticket: raise, local AI helps, open, in progress, resolved - every step logged and e-mailed" width="100%">
</div>

### What each role can do

| Capability | Requester | Support agent |
|---|:---:|:---:|
| Sign up / sign in (one-click demo accounts) | ✅ | ✅ |
| Create a ticket (title, description, category, priority) with validation | ✅ | ✅ |
| Get the likely category suggested while typing a new ticket (AI) | ✅ | ✅ |
| Attach screenshots, logs and documents to a ticket or a comment, preview images | ✅ | ✅ |
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
| Manage categories, priorities and e-mail events (Configuration screen) | | ✅ |
| Django admin (users, agents, configuration, tickets) | | Admin only |

**Every table** (tickets, activity log, users, configuration values) has server-side **search**, **sorting**,
**pagination** and **filters**, plus **Export → PDF / Excel / Email report**. Exports always contain exactly what the
table shows - the same search, filters and sort order.

### Also included

- 🔔 **E-mail notifications** for six ticket events (ticket received, new ticket alert, assigned, status changed, new
  comment, details changed), each switchable on the Configuration screen.
- 🔢 **Human-friendly references** (`SSD-1001`) from an atomic MongoDB counter.
- 🧾 **Helpful validation** from both the UI and the API, shown under the matching field.
- ⏱️ **Live data** - the dashboard and every table refresh themselves every 30 seconds, with an *Updated* badge.
- 🥧 **Dashboard** with tinted stat tiles, an animated status pie chart, category bars and numbers that count up.
- 🧭 **Polished states** - loading, empty and error states on every screen, a friendly *Page not found* page and page
  titles in the browser tab.
- 📱 **Responsive** layout (slide-out menu on phones), keyboard-accessible tables and `prefers-reduced-motion`
  support.
- 🎨 **Small touches** - a welcome animation after signing in, a waving time-of-day greeting, a dark striped sidebar,
  alternating row colours and a favicon / home-screen icon set.

Every screen, with what to capture for screenshots, is described in [docs/SCREENS.md](docs/SCREENS.md).

<div align="right"><a href="#readme-top">↑ Back to top</a></div>

---

## 📚 Documentation

| Document | What is inside |
|---|---|
| [docs/TECH_STACK.md](docs/TECH_STACK.md) | every technology with its version, what it is used for and why; security measures; runtime requirements |
| [docs/WORKFLOWS.md](docs/WORKFLOWS.md) | role capabilities, end-to-end ticket workflow, status lifecycle, sequence diagrams (sign-in, raising, resolving, comments and files, exports, configuration), e-mail flow, request pipeline, CI pipeline |
| [docs/ER_DIAGRAMS.md](docs/ER_DIAGRAMS.md) | ER diagrams of every collection, relationships, indexes, data rules and example documents |
| [docs/SCREENS.md](docs/SCREENS.md) | all 34 screens with what to capture and an explanation, a screenshot checklist and an outline for a submission document |
| [docs/PROJECT_GUIDE.md](docs/PROJECT_GUIDE.md) | a guided tour of the code for people new to Angular, Django or MongoDB |
| [docs/DEMO.md](docs/DEMO.md) | a 3-minute demo script (ticket creation → AI suggestions → resolution → exports) |

<div align="right"><a href="#readme-top">↑ Back to top</a></div>

---

## 🚀 Quick start

> [!NOTE]
> Windows, **no Docker**. The commands work on macOS / Linux too - see the comments next to the two that differ.

### Prerequisites

| Tool | Version | Check |
|---|---|---|
| Python | 3.12 or newer | `python --version` |
| Node.js | 22.12+ or 24+ | `node --version` |
| MongoDB Server | 6.0 or newer, running locally (the server behind MongoDB Compass) | Windows *Services* shows **MongoDB Server** as *Running* |
| Git | any recent | `git --version` |
| CPU | 64-bit with AVX / SSE4.2 (any PC from the last decade) | needed by MongoDB 5+ and the AI libraries |

### 1 · Get the code

```powershell
git clone https://github.com/arunsanjeevms/Smart-Support-Desk.git
cd Smart-Support-Desk
```

### 2 · Backend (Django API) - terminal #1

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

> [!TIP]
> Check it works: <http://localhost:8000/api/health/> should return `{"status": "ok", "database": "up"}`.

### 3 · Frontend (Angular) - terminal #2

```powershell
cd frontend
npm install
npm start                         # http://localhost:4200
```

Open <http://localhost:4200> and click one of the demo accounts on the sign-in page. 🎉

> [!IMPORTANT]
> The Angular app talks to `http://localhost:8000/api` (see `frontend/src/environments/`). If you change the
> backend port, update that file and `CORS_ALLOWED_ORIGINS` in `backend/.env`.

### Useful commands

| What | Command (inside `backend/` with the venv active) |
|---|---|
| Reset demo data | `python manage.py seed_demo --reset` |
| Receive the demo accounts' e-mails in your inbox | `python manage.py seed_demo --inbox you@gmail.com` (riya gets `you+riya@gmail.com`, ...) |
| Create your own admin | `python manage.py createsuperuser` |
| Try the AI matching from the terminal | `python manage.py similar_tickets "The analytics page is painfully slow to open"` |
| (Re)build the AI index | `python manage.py build_similarity_index` (`--force` to encode everything again) |
| Django admin | <http://localhost:8000/admin/> (demo admin: `admin` / `Admin@12345`) |
| Browsable API | <http://localhost:8000/api/> (sign in to the admin first) |

<div align="right"><a href="#readme-top">↑ Back to top</a></div>

---

## 🍃 MongoDB configuration

The backend reads two settings from `backend/.env`:

```ini
MONGODB_URI=mongodb://127.0.0.1:27017     # the same connection string you use in MongoDB Compass
MONGODB_NAME=smart_support_desk           # database name - created automatically
```

> [!WARNING]
> Use `127.0.0.1` rather than `localhost`. A default MongoDB install on Windows only listens on IPv4
> (`bindIp: 127.0.0.1` in `mongod.cfg`), and `localhost` can resolve to the IPv6 address `::1`, which is refused.

Using MongoDB Atlas or a password-protected server? Put the full connection string in `MONGODB_URI`, e.g.
`mongodb+srv://user:password@cluster0.example.mongodb.net/?retryWrites=true`.

<details>
<summary><b>Viewing the data in MongoDB Compass</b></summary>

<br>

Compass only lists connections you have saved, so on a fresh install the list is empty even though the server is
running. Add one once:

1. Open **MongoDB Compass** → click **+ Add new connection** (or **New connection**).
2. In **URI** enter `mongodb://127.0.0.1:27017` and give it a name, e.g. *Local MongoDB*.
3. Click **Save & Connect**. The connection now stays in the left sidebar.
4. Expand **smart_support_desk** to browse the collections below (run `migrate` and `seed_demo` first).
   Click a collection, e.g. `tickets_ticket`, and filter with `{ "status": "open" }`.

If Compass says *connect ECONNREFUSED*: open **Services** (`Win + R` → `services.msc`), find **MongoDB Server**, and
click **Start**.

After `migrate` + `seed_demo`, refresh Compass and you will see the `smart_support_desk` database with these
collections:

| Collection | Contents |
|---|---|
| `accounts_user` | users (requesters, agents, admin) |
| `lookups_lookuptype` / `lookups_lookupvalue` | configurable lists - categories, priorities, e-mail events |
| `tickets_ticket` | tickets |
| `tickets_ticketactivity` | activity log / timeline (status changes, assignments, comments, files) |
| `attachments_ticketattachment` | details of attached files (name, type, size, who, when) |
| `attachments.files` / `attachments.chunks` | the attached files themselves, stored by GridFS |
| `core_counters` | atomic counter used for ticket references (`SSD-1001`, `SSD-1002`, ...) |
| `similarity_ticketembedding` | cached AI embeddings of tickets, for the similar-ticket and category suggestions |
| `authtoken_token` | API tokens of signed-in users |
| `auth_*`, `django_*` | Django's built-in tables (permissions, sessions, admin log, migrations) |

</details>

<div align="right"><a href="#readme-top">↑ Back to top</a></div>

---

## 🔧 Environment variables

All backend settings are read from `backend/.env` (copy `backend/.env.example`). Every variable has a default, so
the app runs with an empty file - only real e-mail delivery needs values.

<details>
<summary><b>Show all environment variables</b></summary>

<br>

**Django and database**

| Variable | Default | Meaning |
|---|---|---|
| `DJANGO_SECRET_KEY` | a development-only key | secret used to sign data; set a long random value outside development |
| `DJANGO_DEBUG` | `True` | debug pages; also lets the Angular app call the API from any local port (`localhost` / `127.0.0.1` / `[::1]`) |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | host names Django answers to |
| `DJANGO_TIME_ZONE` | `Asia/Kolkata` | time zone for dates, filters and e-mails |
| `MONGODB_URI` | `mongodb://127.0.0.1:27017` | MongoDB connection string (local, password-protected or Atlas) |
| `MONGODB_NAME` | `smart_support_desk` | database name |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:4200,http://127.0.0.1:4200` | where the Angular app is served from |

**E-mail**

| Variable | Default | Meaning |
|---|---|---|
| `EMAIL_BACKEND` | console | `django.core.mail.backends.smtp.EmailBackend` to really send |
| `EMAIL_HOST` / `EMAIL_PORT` / `EMAIL_USE_TLS` | `smtp.gmail.com` / `587` / `True` | SMTP server (connection timeout 20 s) |
| `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` | empty | SMTP account (for Gmail an App password) |
| `DEFAULT_FROM_EMAIL` | `Smart Support Desk <no-reply@smartsupportdesk.local>` | sender of every e-mail |
| `EMAIL_NOTIFICATIONS` | `True` | master switch for all notification e-mails (`NOTIFY_REQUESTER_ON_STATUS_CHANGE` is still accepted as an older name) |
| `FRONTEND_URL` | `http://localhost:4200` | used for the *View ticket* links in e-mails |

**Application**

| Variable | Default | Meaning |
|---|---|---|
| `TICKET_REFERENCE_PREFIX` | `SSD` | prefix of ticket references (numbers start at 1000) |
| `EXPORT_MAX_ROWS` | `5000` | maximum rows in one export |
| `DEMO_MODE` | `True` | one-click demo sign-in buttons on the login page |

**Rate limits**

| Variable | Default | Meaning |
|---|---|---|
| `AUTH_THROTTLE_RATE` | `30/minute` | sign-in and sign-up attempts per client |
| `SIMILAR_THROTTLE_RATE` | `60/minute` | similar ticket searches per user |
| `SUGGEST_THROTTLE_RATE` | `120/minute` | category suggestions per user (asked while typing) |

**Attachments**

| Variable | Default | Meaning |
|---|---|---|
| `ATTACHMENT_MAX_FILE_MB` | `10` | size limit per attached file |
| `ATTACHMENT_MAX_FILES` | `5` | files per upload |
| `ATTACHMENT_ALLOWED_EXTENSIONS` | `png,jpg,jpeg,gif,webp,pdf,txt,log,csv,json,xlsx,docx,zip` | allowed file types (can only narrow the types the app supports) |

**AI suggestions**

| Variable | Default | Meaning |
|---|---|---|
| `SIMILARITY_ENABLED` | `True` | show similar ticket suggestions |
| `SIMILARITY_ENGINE` | `semantic` | `semantic` (the model) or `keyword` (TF-IDF only) |
| `SIMILARITY_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | any Sentence Transformers model |
| `SIMILARITY_MAX_RESULTS` | `3` | number of suggestions (never more than 3) |
| `SIMILARITY_MIN_SCORE` | `0.35` | minimum cosine similarity for the model |
| `SIMILARITY_KEYWORD_MIN_SCORE` | `0.15` | minimum score for the keyword fallback |
| `SIMILARITY_PRELOAD` | `True` | load the model in the background when the server starts, so the first search is instant |
| `SIMILARITY_CATEGORY_SUGGESTIONS` | `True` | suggest the likely category while a new ticket is typed |
| `SIMILARITY_CATEGORY_MIN_SCORE` | `0.30` | how similar a past ticket must be to vote for its category |
| `SIMILARITY_CATEGORY_MIN_CONFIDENCE` | `0.5` | share of the vote the winning category needs |
| `SIMILARITY_CATEGORY_DESCRIPTION_MIN_SCORE` | `0.35` | minimum score when matching the category descriptions instead |
| `SIMILARITY_CATEGORY_MAX_TICKETS` | `2000` | how many recent tickets are compared |

</details>

The frontend has one setting, the API address, in `frontend/src/environments/environment*.ts`.

<div align="right"><a href="#readme-top">↑ Back to top</a></div>

---

## 👥 Demo accounts and sample data

`python manage.py seed_demo` creates (all safe to re-run):

| Role | Username | Password |
|---|---|---|
| 🙋 Requester | `riya` (also `karthik`, `emily`, `daniel`) | `Demo@12345` |
| 🎧 Support agent | `meera` (also `sam`) | `Demo@12345` |
| 🛡️ Admin (agent + Django admin) | `admin` | `Admin@12345` |

…plus **28 realistic tickets** across all categories and priorities - a mix of *Open*, *In Progress* and *Resolved*
tickets with resolution notes, comments, a log file and an invoice PDF attached, and a complete activity history
spread over the last six weeks. At the end the AI index is built, so the first suggestion is instant.

The sign-in page shows one-click demo buttons. They are controlled by the backend (`DEMO_MODE=True` in `.env`) and
only appear for accounts that exist.

<div align="right"><a href="#readme-top">↑ Back to top</a></div>

---

## 🧱 Architecture

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
        F[Attachments<br/>checks + GridFS storage]
        ADM[Django admin]
    end
    DB[(MongoDB<br/>smart_support_desk)]
    MAIL[[SMTP / console]]

    A -- "JSON + Token auth" --> B
    B --> S
    B --> X
    B --> AI
    B --> F
    AI --> DB
    F -- "GridFS files" --> DB
    S --> DB
    X --> DB
    ADM --> DB
    X -- attachments --> MAIL
    S -- status e-mails --> MAIL
```

<details>
<summary><b>Project structure</b></summary>

<br>

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
│   │   ├── similarity/          AI: similar tickets + category suggestion, embedding cache, commands
│   │   └── attachments/         files on tickets and comments: checks, GridFS storage, download
│   ├── mongo_migrations/        Django's built-in migrations adapted to ObjectId keys
│   ├── requirements.txt
│   └── .env.example
├── frontend/                    Angular workspace
│   └── src/app/
│       ├── core/                API/auth/config services, interceptor, guards, models
│       ├── shared/              DataTable, export menu, attachments (picker, list), badges, dialogs, pipes
│       ├── layout/              app shell (sidebar + top bar) and the welcome animation
│       └── features/            auth, dashboard, tickets, activity, users, configuration
├── docs/                        tech stack, workflows, ER diagrams, screen guide, project guide, demo script
│   └── assets/                  the animated README artwork (SVG)
└── .github/workflows/ci.yml     tests + build + result e-mail
```

</details>

A guided tour of the code is in [docs/PROJECT_GUIDE.md](docs/PROJECT_GUIDE.md).

<div align="right"><a href="#readme-top">↑ Back to top</a></div>

---

## 💾 Data model

A summary of the collections - [docs/ER_DIAGRAMS.md](docs/ER_DIAGRAMS.md) has the full version with every field,
delete rules, indexes and example documents.

<details>
<summary><b>Show the ER diagram</b></summary>

<br>

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
    TICKET ||--o{ TICKET_ATTACHMENT : "has files"
    TICKET_ACTIVITY |o--o{ TICKET_ATTACHMENT : "added with"
    USER |o--o{ TICKET_ATTACHMENT : "uploads"

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
    TICKET_ATTACHMENT {
        ObjectId _id PK
        ObjectId ticket_id FK
        ObjectId activity_id FK "comment or attached-files entry"
        ObjectId uploaded_by_id FK
        string file_name
        string extension "png | pdf | log | ..."
        string content_type "set by the server"
        int size "bytes"
        ObjectId file_id "GridFS file"
        datetime created_at
    }
    TICKET_EMBEDDING {
        ObjectId _id PK
        ObjectId ticket_id FK,UK "one per ticket"
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

</details>

**Ticket status workflow** (business rules live in `backend/apps/tickets/`):

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

<div align="right"><a href="#readme-top">↑ Back to top</a></div>

---

## 🧰 Configuration managed in the backend

Nothing selectable in the UI is hard-coded in Angular. On sign-in the app calls `GET /api/config/` and builds every
form, filter and badge from the response:

| Option | Where it is defined | How to change it |
|---|---|---|
| **Ticket categories** | `LookupValue` rows of type `ticket_category` | Configuration screen (agents) or Django admin → *Configuration* |
| **Ticket priorities** | `LookupValue` rows of type `ticket_priority` | same as above |
| Category / priority icon, colour, order, default, active | fields on each `LookupValue` | same as above |
| **E-mail notifications** (which actions send an e-mail) | `LookupValue` rows of type `notification_event` | Configuration screen → *Email notifications* (switch each event on/off) |
| Ticket statuses + allowed transitions | `apps/tickets/constants.py` (business rules depend on them) | code - served to the UI via `/api/config/` |
| Validation limits (title/description length, ...) | `apps/tickets/constants.py` | code - served to the UI via `/api/config/` |
| Roles | `User.Role` | Django admin (create agents, change roles) |
| Demo accounts, export row limit, e-mail master switch | `backend/.env` | environment variables |
| Similar ticket and category suggestions (on/off, model, thresholds) | `backend/.env` (`SIMILARITY_*`) | environment variables |
| Attachment size, number and allowed types | `backend/.env` (`ATTACHMENT_*`) | environment variables - the UI reads the limits from `/api/config/` |

> [!TIP]
> **Generic lookup pattern.** `LookupType` describes a list (e.g. *Ticket category*), `LookupValue` holds its
> options. To add a brand-new configurable list later (say *Product area*), add one `LookupType` row and reference it
> from a model - no new tables, admin screens or UI components are needed. Values that are already used by tickets
> cannot be deleted (the API answers `409 Conflict` and suggests deactivating instead), so history is never broken.

<div align="right"><a href="#readme-top">↑ Back to top</a></div>

---

## 📊 Tables, exports and e-mail

**Live data.** The dashboard and every table reload themselves in the background every 30 seconds (and as soon as you
return to the browser tab). The reload is silent: rows stay on screen, nothing flickers, and a failed refresh keeps the
current data. A small *Updated 10:42:05 AM* badge shows when the data was last refreshed. The interval is
`AUTO_REFRESH_MS` in `frontend/src/app/core/utils/auto-refresh.ts`.

All tables use one reusable Angular `DataTable` component backed by a `TableSource` that keeps search, sort, page
and filters in signals and calls the API. Sorting, searching, filtering and paging all run **in Django/MongoDB**, so
they work the same for 30 or 300,000 rows. Columns hide themselves on narrow screens, and rows alternate in colour.

Every list endpoint gets two extra endpoints from a single backend mixin (`apps/core/exports/ExportMixin`):

| Endpoint | Result |
|---|---|
| `GET /api/<table>/export/?file_type=pdf` | branded landscape PDF set in Poppins: running header and footer, a title block with a summary strip (records, generated, prepared by, filters), coloured status / priority, "Page x of y" |
| `GET /api/<table>/export/?file_type=xlsx` | Excel sheet with a styled header, frozen header row and auto-filter |
| `POST /api/<table>/export/email/` `{"file_type": "pdf", "recipients": ["a@b.com"], "subject": "", "message": ""}` | the same file sent as an e-mail attachment (up to 10 recipients) |

Both accept the same query parameters as the list (search, ordering, filters). Requesters can only ever export their
own tickets because exports reuse the role-aware queryset.

### Sending real e-mail

By default e-mails are printed in the Django terminal (`console` backend), so nothing is sent by accident. To really
send mail with Gmail:

1. Turn on 2-step verification for the Google account and create an **App password**.
2. In `backend/.env` set:

   ```ini
   EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
   EMAIL_HOST_USER=your.address@gmail.com
   EMAIL_HOST_PASSWORD=your-16-character-app-password
   DEFAULT_FROM_EMAIL=Smart Support Desk <your.address@gmail.com>
   ```

3. Restart `runserver`. Export e-mails and notifications are now delivered.

All e-mails are HTML (with a plain-text version) and share one branded layout. The templates are in
`backend/apps/core/templates/emails/`. The *View ticket* buttons link to `FRONTEND_URL` (default
`http://localhost:4200`); set it in `backend/.env` when the app runs somewhere else.

### Notification e-mails

Every ticket action can send an e-mail. Each event is a row in the **Email notifications** list on the
Configuration screen: switch it off to stop that e-mail, or rename it. `EMAIL_NOTIFICATIONS=False` in `backend/.env`
turns all of them off at once.

| Event | Sent to |
|---|---|
| 📥 Ticket received | the requester (confirmation with their description) |
| 🚨 New ticket alert | every active support agent |
| 👤 Ticket assigned | the agent it was assigned to (not when agents assign themselves) |
| 🔄 Status changed | the requester, including the resolution note when resolved |
| 💬 New comment | the requester when an agent comments; the assignee (or the whole team if unassigned) when the requester comments - with the names of any attached files |
| ✏️ Ticket details changed | the requester when the category or priority changes |

Nobody is e-mailed about their own action. E-mails are sent in a background thread so the app stays fast, a mail
server problem is logged and never breaks the request, and addresses on reserved demo domains (`example.com`,
`*.test`, ...) are skipped. To receive the demo e-mails yourself, run `seed_demo --inbox you@gmail.com`.

<div align="right"><a href="#readme-top">↑ Back to top</a></div>

---

## 📎 Attachments

Screenshots, logs and documents can be attached to a ticket - on the **New ticket** form (drag and drop), later from
the ticket's **Attachments** card, or together with a **comment**. Images show as thumbnails and open full size in a
preview; every file can be downloaded. The person who uploaded a file, or any support agent, can remove it.

| | |
|---|---|
| 🗄️ **Where the files live** | in MongoDB itself, with **GridFS** (bucket `attachments`: `attachments.files` + `attachments.chunks`). No separate file server or upload folder to back up. The `attachments_ticketattachment` collection holds the details (name, type, size, who, when) and the GridFS id. |
| 📑 **Allowed types** | `png, jpg, jpeg, gif, webp, pdf, txt, log, csv, json, xlsx, docx, zip` (`ATTACHMENT_ALLOWED_EXTENSIONS`). SVG, HTML and programs are never accepted. |
| 📏 **Limits** | 10 MB per file and 5 files per upload (`ATTACHMENT_MAX_FILE_MB`, `ATTACHMENT_MAX_FILES`). The browser checks them straight away, using the limits from `/api/config/`. |
| 🛡️ **Server checks** | every file is checked again: allowed type, size, number of files, and the **first bytes must match the type** (a `.png` must really be a PNG, Office files and `.zip` a ZIP, text files contain no binary data). A renamed `.exe` is rejected. If one file fails, nothing is stored. |
| ⬇️ **Downloads** | always as a download (`Content-Disposition: attachment`) with `X-Content-Type-Options: nosniff`; the type is decided by the server, never by the uploader's browser. The app fetches files with the sign-in token, so links cannot be shared. |
| 👀 **Who sees what** | the same rules as tickets: requesters only reach files on their own tickets (anything else is a `404`), agents see all. |
| 🕓 **History** | adding and removing files are recorded in the activity log (*Attached 2 files*, *Removed error.log*), and the comment e-mail lists the attached file names. Deleting a ticket removes its stored files too. |

The demo data includes a log file on the webhook ticket and an invoice PDF on the GST invoice ticket. The code is in
`backend/apps/attachments/` and `frontend/src/app/shared/attachments/`.

<div align="right"><a href="#readme-top">↑ Back to top</a></div>

---

## 🤖 AI: similar tickets and category suggestion

<div align="center">
<img src="docs/assets/readme-ai.svg" alt="Different wording, same problem: the new issue and a resolved ticket get similar embeddings, cosine similarity 0.68, while keyword matching scores 0.10" width="100%">
</div>

<br>

Two features share one open-source model that runs **locally on the CPU**:

| | Similar resolved tickets | Category suggestion |
|---|---|---|
| **When** | **Find similar tickets** button on the New ticket form; automatically for agents on open tickets | while a new ticket is being typed (after a 600 ms pause) |
| **What** | up to **3** resolved tickets with their resolution note and a % match | the likely **category**, *based on N similar tickets* |
| **Action** | **View details** (dialog, the draft is kept); agents can **Use this note** | **Use it** (or **Switch** if another category is chosen) |
| **Endpoint** | `POST /api/tickets/similar/` | `POST /api/tickets/suggest-category/` |

> [!NOTE]
> Both are **advisory**: nothing is closed, changed or selected automatically, every card says it may not fit, and the
> ticket can always be submitted. Only the problem, its category and the resolution are shared - never who raised the
> old ticket.

### How it works

1. **An open-source model, running locally.** [`sentence-transformers/all-MiniLM-L6-v2`](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
   (Apache 2.0) runs on the CPU inside Django through the `sentence-transformers` library. It is downloaded once
   (about 90 MB) and then loaded from the local cache, so no ticket text ever leaves the server. The server loads it
   in the background at start-up, so the first search is instant.
2. **Text to numbers.** The model turns `"<title>. <description>"` into an *embedding*: 384 numbers that describe
   the meaning of the text. Texts that mean the same thing get similar numbers even when they share no words.
3. **Cached embeddings.** Each ticket is encoded once and stored in the `similarity_ticketembedding` collection,
   with the model name and a hash of the text. A ticket is only encoded again if its text or the model changes.
4. **Ranking.** The new text is encoded and compared with every resolved ticket by **cosine similarity** (0 =
   unrelated, 1 = same meaning). Matches under `SIMILARITY_MIN_SCORE` (0.35) are dropped and the best three are
   returned. Scores of 0.60 and above are labelled *strong*.
5. **Fallback.** If the model cannot be loaded (for example no internet for the first download), the same endpoints
   fall back to TF-IDF keyword matching and the UI says so.

The code is in `backend/apps/similarity/` (`engines.py` for the model and the keyword fallback, `services.py` for
caching, ranking and the category vote) and `frontend/src/app/features/tickets/` (`similar-tickets/`,
`category-suggestion/`).

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

### Category suggestion while typing

A small line appears under the Category field: *Suggested category: Billing & Payments, based on 2 similar tickets*
with a **Use it** button. If a different category is already chosen it says *This reads like Billing & Payments*
with **Switch**. The category is never picked automatically.

How the backend decides (`suggest_category` in `apps/similarity/services.py`):

1. The text is compared with **past tickets of any status** (the 2,000 most recent), using the same cached embeddings.
2. The **10 most similar** tickets with a score of at least **0.30** each vote for their category, weighted by their
   score. Only active categories count.
3. If one category gets **at least half of the vote**, it is suggested. If the similar tickets disagree, nothing is
   suggested - a wrong guess is worse than none.
4. If no past ticket is similar enough, the text is compared with each category's **label and description** instead
   (minimum 0.35, and clearly ahead of the runner-up). This way a category just added on the Configuration screen
   can be suggested before any ticket uses it.

Only the category is returned, never anything about other people's tickets. Outdated requests are cancelled while
the user keeps typing.

**How well it works.** Each of the 29 tickets in the local database (the 28 demo tickets plus one test ticket) was
hidden in turn and its category predicted from all the others (leave-one-out): a category was suggested for **24**,
and **23 of those were right (96%)**. For the other 5 the vote was unsure, so nothing was suggested. Real answers
from the running app:

| Typed by the user | Suggested category | Based on |
|---|---|---|
| "Money was taken from our card twice" | Billing & Payments | 2 similar tickets |
| "The analytics page is painfully slow to open" | Performance | 4 similar tickets |
| "I cannot sign in to my account" | Login & Access | 5 similar tickets |
| "Webhook calls to our server keep failing" | Integrations & API | 2 similar tickets |
| "The office printer is out of toner" | *no suggestion* | - |

The first three are automated tests with the real model; the vote, the description fallback, inactive categories
and the on/off switch are tested with the keyword engine (`apps/similarity/tests/test_category_suggestion.py`).

### Settings (`backend/.env`)

| Variable | Default | Meaning |
|---|---|---|
| `SIMILARITY_ENABLED` | `True` | show the suggestions at all |
| `SIMILARITY_ENGINE` | `semantic` | `semantic` (the model) or `keyword` (TF-IDF only, no model) |
| `SIMILARITY_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | any Sentence Transformers model name |
| `SIMILARITY_MAX_RESULTS` | `3` | how many suggestions (never more than 3) |
| `SIMILARITY_MIN_SCORE` | `0.35` | minimum cosine similarity for a suggestion |
| `SIMILARITY_CATEGORY_SUGGESTIONS` | `True` | suggest the category while typing |
| `SIMILARITY_CATEGORY_MIN_SCORE` / `_MIN_CONFIDENCE` / `_DESCRIPTION_MIN_SCORE` | `0.30` / `0.5` / `0.35` | the thresholds above |

<div align="right"><a href="#readme-top">↑ Back to top</a></div>

---

## 🔌 API reference

All endpoints are under `http://localhost:8000/api/`. Send `Authorization: Token <token>` (returned by login).
Errors always look like `{"message": "...", "errors": {"field": ["..."]}}`.

List endpoints return `{"count", "page", "page_size", "total_pages", "results"}`. Pages hold 10 rows by default;
`page_size` changes it (up to 100). Lists also accept `search` and `ordering` (`-` for descending).

<details>
<summary><b>Status codes</b></summary>

<br>

| Status | Meaning |
|---|---|
| `400` | validation failed - `errors` has a message per field |
| `401` | missing or invalid token - the app goes back to the sign-in page |
| `403` | signed in, but the role is not allowed (e.g. a requester changing a ticket) |
| `404` | not found, or not visible to this user (a requester opening someone else's ticket) |
| `409` | a configuration value is used by tickets, or is built in, and cannot be deleted |
| `429` | too many sign-in attempts, similar ticket searches or category suggestions - try again in a minute |
| `503` | `/health/` only - MongoDB is down |

</details>

**Authentication and configuration**

| Method | Endpoint | Who | Purpose |
|---|---|---|---|
| GET | `/health/` | anyone | API + MongoDB health |
| POST | `/auth/login/` | anyone | `{username or email, password}` → `{token, user}` |
| POST | `/auth/register/` | anyone | create a requester account → `{token, user}` |
| POST | `/auth/logout/` | signed in | invalidate the token |
| GET | `/auth/me/` | signed in | current user |
| GET | `/auth/demo-accounts/` | anyone | demo sign-in buttons (when `DEMO_MODE`) |
| GET | `/config/` | signed in | statuses, categories, priorities, agents, validation limits, attachment limits, AI switches |

**Tickets**

| Method | Endpoint | Who | Purpose |
|---|---|---|---|
| GET | `/tickets/` | signed in | list - `search`, `ordering`, `page`, `page_size`, `status` (comma separated), `category`, `priority`, `assigned_to` (`me`, `unassigned`, id), `created_from`, `created_to` |
| POST | `/tickets/` | signed in | create `{title, description, category, priority?}` |
| GET | `/tickets/{id}/` | owner or agent | detail (+ `allowed_statuses`, `can_manage`, `attachments`) |
| PATCH | `/tickets/{id}/` | agent | `{status?, resolution_note?, assigned_to?, priority?, category?}` |
| GET | `/tickets/{id}/activities/` | owner or agent | timeline (each entry with its files) |
| POST | `/tickets/{id}/comments/` | owner or agent | `{message}`, or multipart with `message` and/or `files` |
| GET | `/tickets/stats/` | signed in | dashboard numbers (scoped to the user) |

**Attachments**

| Method | Endpoint | Who | Purpose |
|---|---|---|---|
| GET | `/tickets/{id}/attachments/` | owner or agent | the ticket's files |
| POST | `/tickets/{id}/attachments/` | owner or agent | upload: multipart field `files` (up to 5) |
| GET | `/attachments/{id}/download/` | owner or agent | the file itself |
| DELETE | `/attachments/{id}/` | uploader or agent | remove a file (recorded in the activity log) |

**AI suggestions**

| Method | Endpoint | Who | Purpose |
|---|---|---|---|
| POST | `/tickets/similar/` | signed in | `{title?, description?, exclude?}` → up to 3 similar resolved tickets with `score` and `match`, plus `engine` and `model` |
| POST | `/tickets/suggest-category/` | signed in | `{title?, description?}` → `{suggestion: {category, confidence, basis, matches} or null, engine, model}` |

**Team data and exports**

| Method | Endpoint | Who | Purpose |
|---|---|---|---|
| GET | `/activities/` | agent | audit log - `activity_type` filter |
| GET | `/users/` | agent | user directory - `role` filter |
| GET | `/lookups/types/` | signed in | configurable lists |
| GET, POST, PATCH, DELETE | `/lookups/values/` | read: signed in, write: agent | values - `type`, `is_active` filters |
| GET / POST | `/<table>/export/`, `/<table>/export/email/` | as the table | exports (see [Tables, exports and e-mail](#-tables-exports-and-e-mail)) |

<div align="right"><a href="#readme-top">↑ Back to top</a></div>

---

## 🔒 Security

| Area | How it is handled |
|---|---|
| 🔑 Passwords | hashed by Django; at least 8 characters, not common, not only digits, not close to the username |
| 🪪 Authentication | one API token per user in the `Authorization` header; signing out deletes it on the server; an expired session returns to the sign-in page |
| 👥 Roles | requesters only see and export their own tickets; activity log, users and configuration changes are agents only, checked by the API and by Angular route guards |
| 📝 Sign-up | always creates a requester; agents are created by an administrator |
| 🚦 Rate limits | sign-in / sign-up 30 per minute, similar ticket searches 60 per minute, category suggestions 120 per minute (`429` after that) |
| 📎 Uploads | allowed types only, size and count limits, file signature checked against the type, served as downloads with `nosniff`, visible only to the ticket's requester and agents |
| ✅ Validation | every input is validated by the API, and again in the browser for quick feedback |
| 🌐 CORS | only the configured frontend origins may call the API |
| 🤖 AI privacy | the model runs on the server, nothing is sent to an outside service; suggestions never show who raised the old ticket; the text is sent by POST, so it stays out of URLs and logs |
| 🗝️ Secrets | in `backend/.env` (ignored by Git) and GitHub repository secrets |

More detail in [docs/TECH_STACK.md](docs/TECH_STACK.md#8-security-measures).

<div align="right"><a href="#readme-top">↑ Back to top</a></div>

---

## 🧪 Running the tests

```powershell
# Backend - 112 tests against a temporary MongoDB database (test_smart_support_desk)
cd backend
.venv\Scripts\activate
python manage.py test

# Frontend - 51 Vitest unit tests + production build
cd frontend
npm run test:ci
npm run build
```

<details>
<summary><b>What the tests cover</b></summary>

<br>

**Backend (112)**

| Suite | Tests | Covers |
|---|:---:|---|
| `accounts/tests/test_auth.py` | 15 | sign-in with username or e-mail, sign-up rules, roles, logout, demo accounts, user directory |
| `tickets/tests/test_tickets.py` | 29 | validation messages, visibility, search / filter / sort / paging, the status workflow, auto-assignment, re-opening, comments, dashboard stats, the config endpoint |
| `tickets/tests/test_notifications.py` | 9 | who gets which e-mail, per-event switches, undeliverable demo addresses, built-in events that cannot be added or deleted |
| `lookups/tests/test_lookups.py` | 10 | default lists, one default per list, who may change configuration, validation and duplicate codes, hidden inactive values, the "in use" delete guard |
| `core/tests/test_exports.py` | 12 | PDF (with the embedded Poppins font) and Excel exports of the filtered rows, requesters exporting only their own tickets, e-mailed reports and recipient checks, the atomic reference counter, the health endpoint |
| `attachments/tests/test_attachments.py` | 14 | allowed types, fake file signatures, size and count limits, who may download or remove, comments with files, clean-up of stored files |
| `similarity/tests/test_similarity.py` | 16 | ranking, the limit of three, nothing is changed, the embedding cache, the real model matching differently worded issues |
| `similarity/tests/test_category_suggestion.py` | 7 | the category vote, open tickets counting, the description fallback, inactive categories, the on/off switch |

**Frontend (51)** - the auth service, mapping API errors onto form fields, the table state (`TableSource`), the
status badge, the relative time pipe, the count-up numbers, the welcome animation, the similar tickets panel, the
category suggestion (waiting for a pause in typing, Use it / Switch), the file picker checks, the attachment list and
the upload progress.

</details>

<div align="right"><a href="#readme-top">↑ Back to top</a></div>

---

## 🔄 Continuous integration

`.github/workflows/ci.yml` runs on every push to `main`, on pull requests and on demand:

```mermaid
flowchart LR
    P([push / pull request]) --> BE[Backend<br/>Python 3.13 + CPU PyTorch<br/>MongoDB 8 service<br/>checks, migrations, tests, seed]
    P --> FE[Frontend<br/>Node 24<br/>unit tests + production build]
    BE --> M[Email the result<br/>to msarunsanjeev@gmail.com]
    FE --> M
```

1. **Backend** - installs Python 3.13 and the CPU build of PyTorch, starts a temporary MongoDB 8 service, runs Django
   checks, verifies there are no missing migrations, runs the test suite and the seed command. The AI model is
   cached between runs.
2. **Frontend** - installs Node 24, runs the unit tests and a production build.
3. **Email the result** - always runs (except when a newer push cancels the run) and e-mails a summary: per-job
   result, commit and a link to the logs.

> [!TIP]
> To enable the e-mail, add two repository secrets in **GitHub → Settings → Secrets and variables → Actions**:
> `MAIL_USERNAME` (the Gmail address that sends the mail) and `MAIL_PASSWORD` (a Gmail **App password** for that
> account). Until the secrets exist the step is skipped with a notice, so the pipeline stays green.

<div align="right"><a href="#readme-top">↑ Back to top</a></div>

---

## 🧭 Key design decisions

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
10. **Token authentication with two roles** (`requester`, `agent`). It is simple, stateless for the SPA and easy to
    test. Agents are created by an administrator; self sign-up always creates requesters.
11. **A small local model with cached embeddings for suggestions.** `all-MiniLM-L6-v2` is fast on a normal CPU
    (milliseconds per ticket), open source and needs no API key or external service. Embeddings are cached per
    ticket, so a search only encodes the new text. The comparison runs in numpy because a local MongoDB server has no
    vector search; that is fast for tens of thousands of tickets.
12. **Attachments in GridFS.** Files are stored in the same MongoDB database as everything else, so a backup or a
    move to another server takes the files along, and there is no upload folder to secure. The file details sit in an
    ordinary model, so attachments follow the ticket permissions and delete rules like any other data.

<div align="right"><a href="#readme-top">↑ Back to top</a></div>

---

## 🚧 Limitations and next steps

- [ ] **Vector index for very large data.** Suggestions compare against tickets in memory; with millions of tickets,
  MongoDB Atlas Vector Search would replace the numpy comparison. The default model is English only - a multilingual
  Sentence Transformers model can be set with `SIMILARITY_MODEL`.
- [ ] **Faster search.** Search uses case-insensitive regular expressions; for very large data sets a MongoDB text or
  Atlas Search index would be faster.
- [ ] **Background exports.** Exports are generated synchronously and capped at `EXPORT_MAX_ROWS` (5,000 by default);
  a job queue would be the next step for much larger exports.
- [ ] **Virus scanning.** Attachments are checked for type, size and signature but not virus-scanned; a ClamAV scan
  before storing would be the next step for a public deployment.
- [ ] **SLA timers and instant updates.** No SLA timers yet; screens refresh every 30 seconds, and pushing changes
  instantly (WebSockets) would be the next step.
- [ ] **Expiring tokens.** Tokens do not expire; JWT with refresh tokens would be the next step before a public
  deployment.

<div align="right"><a href="#readme-top">↑ Back to top</a></div>

---

<div align="center">

**Smart Support Desk** · Angular · Django · MongoDB · local AI

Developed by **Arun Sanjeev M S**

<a href="#readme-top">↑ Back to top</a>

</div>
