# Workflows

How Smart Support Desk behaves from the user's side and inside the system: who does what, how a ticket moves,
and what happens between the browser, Django and MongoDB for each main action. The diagrams are Mermaid, so they
render on GitHub and in VS Code's Markdown preview.

Contents

1. [Roles and what they can do](#1-roles-and-what-they-can-do)
2. [End-to-end ticket workflow](#2-end-to-end-ticket-workflow)
3. [Ticket status lifecycle](#3-ticket-status-lifecycle)
4. [Signing in and restoring a session](#4-signing-in-and-restoring-a-session)
5. [Raising a ticket (with similar ticket suggestions)](#5-raising-a-ticket-with-similar-ticket-suggestions)
6. [Working and resolving a ticket](#6-working-and-resolving-a-ticket)
7. [Comments](#7-comments)
8. [E-mail notifications](#8-e-mail-notifications)
9. [Exports: PDF, Excel and e-mail](#9-exports-pdf-excel-and-e-mail)
10. [Configuration changes](#10-configuration-changes)
11. [Inside one API request](#11-inside-one-api-request)
12. [Continuous integration](#12-continuous-integration)

---

## 1. Roles and what they can do

There are two roles, stored in `User.role`. Self sign-up always creates a **requester**; **support agents** are
created by an administrator in the Django admin. An administrator is an agent who can also open the Django admin.

```mermaid
flowchart LR
    R([Requester])
    A([Support agent])
    AD([Administrator])

    R --> R1[Sign up / sign in]
    R --> R2[Raise a ticket]
    R --> R3[Find similar resolved tickets]
    R --> R4[Follow own tickets and comment]
    R --> R5[Own dashboard and exports]

    A --> A1[See every ticket]
    A --> A2[Assign, change status, priority, category]
    A --> A3[Resolve with a resolution note]
    A --> A4[Reuse a note from a similar ticket]
    A --> A5[Activity log and user directory]
    A --> A6[Configuration screen]
    A --> A7[Team dashboard and exports]

    AD --> AD1[Everything an agent can do]
    AD --> AD2[Django admin: create agents, change roles]
```

| Screen | Requester | Agent |
|---|:---:|:---:|
| Dashboard | own numbers | whole queue |
| My tickets / All tickets | own tickets only | every ticket |
| New ticket | ✅ | ✅ |
| Ticket detail | own tickets, read + comment | any ticket, full *Manage ticket* panel |
| Activity log, Users, Configuration | hidden (blocked by `agentGuard` and by the API) | ✅ |

---

## 2. End-to-end ticket workflow

The main path from a reported problem to a resolution, across both roles.

```mermaid
flowchart TD
    S([Requester has a problem]) --> N[Opens New ticket and fills in title, category, priority, description]
    N --> F{Find similar tickets?}
    F -- yes --> SIM[Model suggests up to 3 resolved tickets]
    SIM --> H{One of them fixes it?}
    H -- yes --> DONE1([Problem solved without a ticket])
    H -- no --> SUB
    F -- no --> SUB[Submit ticket]
    SUB --> V{Valid?}
    V -- no --> ERR[Field messages from the browser and the API] --> N
    V -- yes --> T[Ticket SSD-xxxx saved as Open]
    T --> M1[/E-mail: Ticket received to requester/]
    T --> M2[/E-mail: New ticket alert to every agent/]
    T --> Q[Ticket appears in the agent queue]
    Q --> P[Agent clicks Start progress]
    P --> IP[Status In Progress, assigned to the agent]
    IP --> M3[/E-mail: Status changed to requester/]
    IP --> C{Need more information?}
    C -- yes --> CM[Comments go back and forth] --> IP
    C -- no --> RN[Agent writes a resolution note, or reuses one from a similar ticket]
    RN --> RS[Status Resolved]
    RS --> M4[/E-mail: Status changed, with the resolution note/]
    RS --> E{Problem comes back?}
    E -- yes --> RO[Agent re-opens: Open or In Progress] --> IP
    E -- no --> DONE2([Closed loop: the ticket now helps future suggestions])
```

Every step that changes a ticket writes a row to `tickets_ticketactivity`, which is the ticket's timeline and the
*Activity log* screen.

---

## 3. Ticket status lifecycle

```mermaid
stateDiagram-v2
    [*] --> Open: requester submits
    Open --> InProgress: agent starts work (auto-assigns if unassigned)
    Open --> Resolved: agent resolves (note required)
    InProgress --> Resolved: agent resolves (note required)
    InProgress --> Open: back to the queue
    Resolved --> InProgress: re-opened
    Resolved --> Open: re-opened
    Resolved --> [*]

    InProgress: In Progress
```

| Move | Who | Rule | Activity rows | E-mail |
|---|---|---|---|---|
| Submit | anyone signed in | title 5-150, description 20-5000 characters, active category | `created` | *Ticket received* to the requester, *New ticket alert* to agents |
| Open → In Progress | agent | if nobody has the ticket, it is assigned to the agent who moved it | `status_changed` (+ `assigned`) | *Status changed* to the requester |
| → Resolved | agent | resolution note of at least 10 characters | `status_changed` with the note | *Status changed* with the resolution note |
| Resolved → Open / In Progress | agent | `resolved_by` and `resolved_at` are cleared | `status_changed` | *Status changed* |
| In Progress → Open | agent | - | `status_changed` | *Status changed* |
| Edit the note of a resolved ticket | agent | - | `resolution_updated` | - |
| Change category or priority | agent | value must be active and of the right list | `details_updated` | *Ticket details changed* |
| Assign / re-assign | agent | assignee must be an active agent | `assigned` | *Ticket assigned* to the new assignee |

The allowed moves are `STATUS_TRANSITIONS` in `backend/apps/tickets/constants.py`. They are sent to the UI through
`GET /api/config/`, so the status menu only offers moves the API will accept. The rules themselves live in
`backend/apps/tickets/services.py`.

---

## 4. Signing in and restoring a session

```mermaid
sequenceDiagram
    actor U as User
    participant NG as Angular app
    participant API as Django API
    participant DB as MongoDB

    U->>NG: Enter username or email + password (or click a demo account)
    NG->>API: POST /api/auth/login/
    API->>API: Rate limit (30 per minute)
    API->>DB: Find user, check hashed password
    API->>DB: Get or create the user's token
    API-->>NG: token + user
    NG->>NG: Save token in localStorage
    NG->>API: GET /api/config/ (configGuard)
    API->>DB: Active categories, priorities, agents
    API-->>NG: statuses, transitions, lists, validation limits
    NG-->>U: Welcome animation, then the dashboard

    Note over NG,API: Later, on a page refresh
    NG->>API: GET /api/auth/me/ with the saved token
    alt token still valid
        API-->>NG: user
        NG-->>U: Same page again, no welcome animation
    else token invalid
        API-->>NG: 401
        NG-->>U: Sign-in page
    end
```

- Every later request carries `Authorization: Token <key>` (added by `core/interceptors/auth.interceptor.ts`).
- Any `401` from the API sends the user back to the sign-in page with the address they were on.
- **Sign out** calls `POST /api/auth/logout/`, which deletes the token on the server.
- **Sign up** (`POST /api/auth/register/`) validates the password with Django's password rules and creates a
  requester, then signs them in the same way.

---

## 5. Raising a ticket (with similar ticket suggestions)

```mermaid
sequenceDiagram
    actor R as Requester
    participant NG as New ticket page
    participant API as Django API
    participant AI as Similarity engine
    participant DB as MongoDB

    R->>NG: Type title and description
    R->>NG: Click Find similar tickets
    NG->>API: POST /api/tickets/similar/ (title, description)
    API->>AI: find_similar()
    AI->>DB: Resolved tickets + cached embeddings
    AI->>AI: Encode new or changed resolved tickets, store their embeddings
    AI->>AI: Encode the draft, cosine similarity with each resolved ticket
    AI-->>API: Best 3 with score at least 0.35
    API-->>NG: suggestions (score, strong or possible match, resolution note)
    NG-->>R: Cards - View details opens a dialog, the draft is kept

    R->>NG: Submit ticket
    NG->>NG: Browser validation
    NG->>API: POST /api/tickets/
    API->>API: Serializer validation (lengths, active category)
    API->>DB: findOneAndUpdate + $inc on core_counters (next SSD number)
    API->>DB: insert ticket, insert activity "created"
    API--)R: E-mails in a background thread
    API-->>NG: 201 + ticket
    NG-->>R: Toast, then the ticket's detail page
```

- Suggestions are advisory. They never change or close anything, and the ticket can always be submitted.
- If the model cannot be loaded, the same endpoint falls back to TF-IDF keyword matching and the panel says so.
- If validation fails the API answers `400` with `{"message": ..., "errors": {"field": [...]}}` and the message is
  shown under the matching form field.

---

## 6. Working and resolving a ticket

```mermaid
sequenceDiagram
    actor A as Agent
    participant NG as Ticket detail page
    participant API as Django API
    participant SV as services.update_ticket
    participant DB as MongoDB

    A->>NG: Open a ticket from the queue
    NG->>API: GET /api/tickets/{id}/ and /activities/
    NG->>API: POST /api/tickets/similar/ (exclude this ticket)
    API-->>NG: ticket, allowed statuses, timeline, similar resolved tickets

    A->>NG: Click Start progress
    NG->>API: PATCH /api/tickets/{id}/ status = in_progress
    API->>SV: update_ticket()
    SV->>SV: Check the move is allowed, assign to the agent if unassigned
    SV->>DB: save ticket, activity rows status_changed + assigned
    SV--)A: E-mail to the requester (background)
    API-->>NG: updated ticket

    A->>NG: Use this note on a similar ticket (optional)
    NG->>NG: Copy that resolution into the note field, nothing saved yet
    A->>NG: Status Resolved + note, click Resolve ticket
    NG->>API: PATCH status = resolved, resolution_note
    API->>SV: update_ticket()
    alt note missing or too short
        SV-->>NG: 400 with a message on resolution_note
    else valid
        SV->>DB: status, resolution_note, resolved_by, resolved_at, activity row
        SV--)A: E-mail with the resolution to the requester
        API-->>NG: resolved ticket
    end
```

A resolved ticket is immediately available to the similar ticket suggestions: its embedding is computed on the
next search and cached.

---

## 7. Comments

Both sides can comment on a ticket they can see, at any status (a requester can reply on a resolved ticket if the
problem comes back).

```mermaid
sequenceDiagram
    actor W as Writer
    participant API as Comments API
    participant DB as MongoDB
    participant M as Notifications

    W->>API: POST /api/tickets/{id}/comments/ with the message
    API->>DB: activity row (commented, text in note)
    API->>M: comment_added()
    alt the requester wrote
        M--)M: e-mail the assigned agent, or every agent if unassigned
    else an agent wrote
        M--)M: e-mail the requester
    end
    API-->>W: 201 + the new timeline entry
```

---

## 8. E-mail notifications

```mermaid
flowchart TD
    EV[Ticket event: created, assigned, status changed, comment, details changed] --> MS{EMAIL_NOTIFICATIONS on in .env?}
    MS -- no --> X1([No e-mail])
    MS -- yes --> ON{"Event switched on in the Email notifications list?"}
    ON -- no --> X1
    ON -- yes --> RC[Work out recipients]
    RC --> OWN{Recipient made the change?}
    OWN -- yes --> X2([Skip them])
    OWN -- no --> DOM{Address on a reserved domain, e.g. example.com or .test?}
    DOM -- yes --> X2
    DOM -- no --> RENDER[Render HTML + plain-text e-mail from the template]
    RENDER --> BG[Send in a background thread]
    BG --> BE{EMAIL_BACKEND}
    BE -- console --> CON[Printed in the Django terminal]
    BE -- smtp --> SMTP[Delivered through Gmail SMTP]
```

| Event (`notification_event` value) | Recipients |
|---|---|
| `ticket_received` | the requester |
| `new_ticket_alert` | every active agent |
| `ticket_assigned` | the new assignee (not when agents assign themselves) |
| `status_changed` | the requester, with the resolution note when resolved |
| `comment_added` | the requester when an agent comments; the assignee (or every agent if unassigned) when the requester comments |
| `details_updated` | the requester when the category or priority changes |

A mail server problem is logged and never breaks the request.

---

## 9. Exports: PDF, Excel and e-mail

Every table (tickets, activity log, users, configuration values) has an **Export** menu. The backend builds the
file from the same queryset as the table, so the export always matches what is on screen and respects the role.

```mermaid
sequenceDiagram
    actor U as User
    participant NG as Export menu
    participant API as ExportMixin
    participant W as PDF / Excel writer
    participant MAIL as SMTP or console

    alt Download PDF or Excel
        U->>NG: Export > Download PDF
        NG->>API: GET /api/tickets/export/?file_type=pdf + current search, filters, sort
        API->>API: Same role-aware queryset, max EXPORT_MAX_ROWS rows
        API->>W: rows + columns + filter summary
        W-->>API: file bytes
        API-->>NG: file with Content-Disposition name
        NG-->>U: Browser saves tickets-YYYYMMDD-HHMM.pdf
    else Email report
        U->>NG: Export > Email report, enter recipients, subject, message
        NG->>API: POST /api/tickets/export/email/
        API->>W: build the same file
        API->>MAIL: branded e-mail with the file attached
        API-->>NG: "PDF report sent to ..."
    end
```

---

## 10. Configuration changes

Nothing selectable is hard-coded in Angular. An agent changes a list on the Configuration screen and every form,
filter and badge picks it up.

```mermaid
sequenceDiagram
    actor A as Agent
    participant CFG as Configuration screen
    participant API as /api/lookups/values/
    participant DB as MongoDB
    participant UI as Every other screen

    A->>CFG: Add ticket category (label, code, icon, colour, order)
    CFG->>API: POST
    API->>DB: insert lookup value
    API-->>CFG: 201
    UI->>API: GET /api/config/ (on the next sign-in or page load)
    API-->>UI: the new category is in every form and filter

    A->>CFG: Delete a category used by tickets
    CFG->>API: DELETE
    API-->>CFG: 409 "used by existing tickets, deactivate it instead"
```

| Change | Effect |
|---|---|
| Deactivate a value | hidden from new tickets and filters; old tickets keep showing it |
| Mark a priority as default | pre-selected on the New ticket form and used by the API when no priority is sent; the previous default is cleared |
| Switch off an e-mail notification | that event stops sending e-mails at once |
| Delete a value in use | refused with `409 Conflict` |
| Delete or add a notification event | refused: they are built in and can only be renamed or switched off |

---

## 11. Inside one API request

What happens in Django for `PATCH /api/tickets/{id}/`, the same for every endpoint.

```mermaid
flowchart LR
    REQ[HTTP request] --> CORS[CORS middleware]
    CORS --> URL[URL router config/urls.py]
    URL --> AUTH[Token authentication]
    AUTH --> PERM[Permissions: signed in, agent only]
    PERM --> THR[Rate limit, on auth and similar]
    THR --> QS[Role-aware queryset: requesters see own tickets]
    QS --> SER[Serializer validation]
    SER --> SVC[Service layer: business rules + activity log]
    SVC --> ORM[Django ORM via Django MongoDB Backend]
    ORM --> DB[(MongoDB)]
    SVC -. background .-> MAIL[[E-mail]]
    SVC --> REN[MongoJSONRenderer: ObjectIds as strings]
    REN --> RES[JSON response]

    PERM -- 403 --> EH[One error format: message + errors]
    SER -- 400 --> EH
    THR -- 429 --> EH
    QS -- 404 --> EH
```

---

## 12. Continuous integration

`.github/workflows/ci.yml` runs on every push to `main`, on pull requests and on demand. A newer push to the same
branch cancels the run in progress.

```mermaid
flowchart LR
    PUSH([git push / pull request / manual run]) --> BE & FE

    subgraph BE["Backend job (Ubuntu + MongoDB 8 service)"]
        direction TB
        B1[Python 3.13, CPU PyTorch, requirements] --> B2[Cache the AI model]
        B2 --> B3[manage.py check]
        B3 --> B4["makemigrations --check"]
        B4 --> B5[90 tests]
        B5 --> B6[migrate + seed_demo smoke test]
    end

    subgraph FE["Frontend job (Ubuntu)"]
        direction TB
        F1[Node 24, npm ci] --> F2[37 unit tests with Vitest]
        F2 --> F3[Production build]
    end

    BE --> N
    FE --> N
    N[Notify job: HTML e-mail with each job's result, commit and log link]
```

The notify job runs whether the tests passed or failed. If the `MAIL_USERNAME` / `MAIL_PASSWORD` repository secrets
are missing it only prints a notice, so the pipeline stays green.
