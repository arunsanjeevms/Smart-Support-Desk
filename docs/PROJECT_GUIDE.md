# Project guide - how the code fits together

This guide is for anyone opening the project without much Angular, Django or MongoDB experience. It follows one
request from the browser to the database and back, then lists where to look when you want to change something.

---

## 1. The three pieces in one minute

| Piece | Role | Think of it as |
|---|---|---|
| **MongoDB** | stores documents (JSON-like records) in *collections* | the filing cabinet |
| **Django + Django REST Framework** | Python web framework; exposes a JSON API, enforces rules and permissions | the office clerk who checks every form |
| **Angular** | TypeScript framework that runs in the browser and renders the screens | the front desk people talk to |

The browser never talks to MongoDB directly. Angular calls `http://localhost:8000/api/...`, Django validates the
request, reads/writes MongoDB and answers with JSON.

---

## 2. Follow one request: "create a ticket"

1. **Screen** - `frontend/src/app/features/tickets/ticket-create-page.ts` + `.html`
   A reactive form (`FormBuilder`) with validators for title, category and description. The category list comes
   from `ConfigService.categories()` - i.e. from the backend, not from the code.
2. **Service** - `frontend/src/app/core/services/ticket.service.ts` → `create()` posts JSON to `tickets/`.
3. **Interceptor** - `core/interceptors/auth.interceptor.ts` adds `Authorization: Token <token>` to the request.
4. **URL routing (backend)** - `backend/config/urls.py` maps `/api/tickets/` to `TicketViewSet`.
5. **View** - `backend/apps/tickets/views.py` → `TicketViewSet.create()` runs the serializer.
6. **Validation** - `backend/apps/tickets/serializers.py` → `TicketCreateSerializer` checks lengths and that the
   category is an *active* value of the *ticket category* list. Errors return as
   `{"message": ..., "errors": {"title": ["..."]}}` and the Angular form shows them under the field
   (`core/utils/api-errors.ts → applyServerErrors`).
7. **Business rules** - `backend/apps/tickets/services.py` → `create_ticket()` reserves the next `SSD-` reference
   (atomic MongoDB counter in `apps/core/sequences.py`), saves the ticket and writes a *Ticket created* activity.
8. **Database** - the Django MongoDB Backend turns the model save into an `insertOne` in the `tickets_ticket`
   collection. Open MongoDB Compass to see the new document.
9. **Response** - the ticket JSON comes back, Angular shows a toast and navigates to `/tickets/<id>`.

---

## 3. Backend tour (`backend/`)

```
config/settings.py      every setting; values from .env (MongoDB URI, e-mail, demo mode, ...)
config/urls.py          URL map of the whole API
config/apps.py          makes Django's own apps use MongoDB ObjectIds
apps/core/              code shared by all apps
    models.py           TimeStampedModel (created_at / updated_at)
    serializers.py      ObjectId <-> string conversion for DRF
    exceptions.py       one error format for the whole API
    pagination.py       ?page=&page_size= for every table
    sequences.py        atomic counters in MongoDB
    exports/            PDF + Excel writers and the ExportMixin (export + email endpoints)
apps/accounts/          the User model (with role), login/register/logout, user directory, permissions
apps/lookups/           LookupType / LookupValue = configurable lists (categories, priorities)
    migrations/0002_*   creates the default categories and priorities
apps/tickets/
    constants.py        statuses, allowed transitions, validation limits, activity types
    models.py           Ticket and TicketActivity
    services.py         create / update / comment - all business rules
    notifications.py    e-mail to the requester when the status changes
    serializers.py      input validation and JSON output
    views.py            TicketViewSet, ActivityViewSet, ConfigView
    management/commands/seed_demo.py   python manage.py seed_demo
    tests/              API tests
```

Django vocabulary:

- **Model** - a Python class describing one collection (`Ticket`). Fields become document keys.
- **Migration** - a file describing how models changed; `python manage.py migrate` applies them (creates
  collections and indexes in MongoDB).
- **Serializer** - converts JSON ↔ Python and validates input.
- **ViewSet** - a group of API endpoints (list, create, retrieve, update) for one resource.
- **Admin** - automatic back-office UI at `/admin/`, configured in each app's `admin.py`.

## 4. Frontend tour (`frontend/src/app/`)

```
app.config.ts           global providers: router, HTTP + interceptor, Material defaults, session restore
app.routes.ts           URL → page map; guards decide who may open what; pages are lazy loaded
core/
    models/api.models.ts    TypeScript types for every API response
    services/               api, auth, config, ticket, lookup, export, notify
    guards/auth.guards.ts   authGuard, guestGuard, agentGuard, configGuard
    interceptors/           adds the token, handles expired sessions
shared/
    data-table/             DataTable component + TableSource (search/sort/filter/page state)
    export-menu/            "Export" button and the e-mail dialog
    components/             status badge, category/priority badge, avatar, page header, confirm dialog
layout/shell.*          sidebar + top bar around every signed-in page
features/               one folder per screen
styles/                 design tokens (_tokens.scss), Material theme (_material.scss), helpers
```

Angular vocabulary:

- **Component** - a class + HTML template + styles that renders part of the screen (`TicketListPage`).
- **Signal** - a value that updates the screen automatically when it changes (`loading = signal(false)`).
- **Service** - a class shared across components, usually for talking to the API (`TicketService`).
- **Guard** - a function that allows or blocks navigation to a route (`agentGuard`).
- **Interceptor** - code that runs for every HTTP request (adds the token).

## 5. MongoDB tour

- Each Django model is a **collection**; each saved object is a **document** with an `_id` of type ObjectId.
- Foreign keys are stored as ObjectIds (e.g. `category_id`), and Django joins them with `$lookup` when needed.
- Indexes are declared on the models (`Meta.indexes`, `unique=True`) and created by `migrate`.
- In **Compass** open `smart_support_desk → tickets_ticket` to browse tickets; filter with
  `{ "status": "open" }`.

---

## 6. Common changes - where to look

| I want to... | Change |
|---|---|
| add a category or priority | Configuration screen (as an agent) or Django admin → Configuration. No code. |
| add a new configurable list | add a `LookupType` code in `apps/lookups/constants.py`, a data migration or an admin row, then reference it from a model |
| change validation limits | `apps/tickets/constants.py` (the UI reads them from `/api/config/`) |
| add a ticket field | `apps/tickets/models.py` → `makemigrations` / `migrate` → serializers → `api.models.ts` → the page template |
| add a column to a table | the page's `columns` array (+ an `appCell` template if it needs custom HTML) and the view's `ordering_fields` / `export_columns` |
| add a new exportable table | DRF `ViewSet` + `ExportMixin` + `export_columns`; in Angular a `TableSource` + `<app-data-table>` |
| change colours / fonts | `frontend/src/styles/_tokens.scss` and `_material.scss` |
| send real e-mails | SMTP settings in `backend/.env` (see the README) |
