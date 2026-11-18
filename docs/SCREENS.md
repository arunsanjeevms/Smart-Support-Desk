# Screen guide

A tour of every screen in Smart Support Desk, written so it can be turned into a submission document with
screenshots. For each screen it lists the address, who can open it, how to set up the screenshot and a short
explanation to place under it.

Contents

1. [Before taking screenshots](#1-before-taking-screenshots)
2. [Suggested document outline](#2-suggested-document-outline)
3. [Screenshot checklist](#3-screenshot-checklist)
4. [Screens in detail](#4-screens-in-detail)

---

## 1. Before taking screenshots

```powershell
cd backend; .venv\Scripts\activate
python manage.py seed_demo --reset     # fresh, predictable demo data (28 tickets, 7 users)
python manage.py runserver             # terminal 1 - http://localhost:8000
cd ..\frontend; npm start              # terminal 2 - http://localhost:4200
```

- Use a browser window of about **1440 × 900** at 100 % zoom, with the bookmarks bar hidden.
- Sign in with the one-click demo buttons: **Requester** (`riya`) and **Support Agent** (`meera`). The admin is
  `admin` / `Admin@12345`.
- Windows: `Win + Shift + S` takes a screenshot of a region. Chrome DevTools (`F12` → `Ctrl + Shift + P` →
  *Capture full size screenshot*) captures a whole long page.
- Save the images as `docs/screenshots/NN-name.png` using the numbers in the checklist below, so they sort in
  the order of the document.

---

## 2. Suggested document outline

| # | Chapter | Source |
|---|---|---|
| 1 | Introduction: the problem, the two roles, the main features | README - intro and *Features* |
| 2 | Technology stack | [TECH_STACK.md](TECH_STACK.md) |
| 3 | Architecture and project structure | README - *Architecture*, [PROJECT_GUIDE.md](PROJECT_GUIDE.md) |
| 4 | Data model and ER diagrams | [ER_DIAGRAMS.md](ER_DIAGRAMS.md) |
| 5 | Workflows: ticket lifecycle, sequences, notifications | [WORKFLOWS.md](WORKFLOWS.md) |
| 6 | Screens with screenshots | this page, section 4 |
| 7 | AI: similar ticket and category suggestions | README - *Similar ticket suggestions (AI)* |
| 8 | Attachments | README - *Attachments* |
| 9 | Configuration managed in the backend | README - *Configuration managed in the backend* |
| 10 | Exports and e-mail | README - *Tables, exports and e-mail* |
| 11 | API reference | README - *API reference* |
| 12 | Testing and continuous integration | README - *Running the tests*, *Continuous integration* |
| 13 | Setup guide | README - *Quick start*, *MongoDB configuration* |
| 14 | Design decisions, limitations and next steps | README - last two sections |

Mermaid diagrams can be saved as images by opening the Markdown file on GitHub (or pasting the diagram into
<https://mermaid.live>) and exporting PNG or SVG.

---

## 3. Screenshot checklist

| # | Screen | Signed in as | Address |
|---|---|---|---|
| 01 | Sign-in page with demo accounts | - | `/login` |
| 02 | Sign-up page with validation messages | - | `/register` |
| 03 | Welcome animation after signing in | Requester | right after sign-in |
| 04 | Requester dashboard | Requester | `/dashboard` |
| 05 | My tickets | Requester | `/tickets` |
| 06 | New ticket - validation messages | Requester | `/tickets/new` |
| 07 | New ticket - suggested category | Requester | `/tickets/new` |
| 08 | New ticket - attachments (with a rejected file) | Requester | `/tickets/new` |
| 09 | New ticket - similar resolved tickets | Requester | `/tickets/new` |
| 10 | Similar ticket details dialog | Requester | `/tickets/new` |
| 11 | Ticket detail - requester view | Requester | `/tickets/<id>` |
| 12 | Ticket attachments and image preview | Requester | `/tickets/<id>` |
| 13 | Agent dashboard | Agent | `/dashboard` |
| 14 | All tickets with filters | Agent | `/tickets?status=open&assigned_to=unassigned` |
| 15 | Ticket detail - agent view with Manage ticket | Agent | `/tickets/<id>` |
| 16 | Resolve without a note - error | Agent | `/tickets/<id>` |
| 17 | Resolved ticket with resolution and timeline | Agent | `/tickets/<id>` |
| 18 | Export menu | Agent | `/tickets` |
| 19 | Exported PDF report | Agent | downloaded file |
| 20 | Exported Excel workbook | Agent | downloaded file |
| 21 | Email report dialog | Agent | `/tickets` |
| 22 | Notification e-mail | - | inbox or Django terminal |
| 23 | Activity log | Agent | `/activity` |
| 24 | Users | Agent | `/users` |
| 25 | Configuration - ticket categories | Agent | `/configuration` |
| 26 | Configuration - add / edit value dialog | Agent | `/configuration` |
| 27 | Configuration - e-mail notifications | Agent | `/configuration` |
| 28 | Account menu and greeting | Agent | any page |
| 29 | Mobile layout | any | any page, narrow window |
| 30 | Page not found | any | `/does-not-exist` |
| 31 | Django admin | Admin | `http://localhost:8000/admin/` |
| 32 | MongoDB Compass collections | - | Compass |
| 33 | AI comparison in the terminal | - | `python manage.py similar_tickets "..."` |
| 34 | GitHub Actions run and CI e-mail | - | GitHub → Actions |

---

## 4. Screens in detail

### 01 - Sign-in page

- **Address:** `/login` · **Who:** everyone
- **Capture:** the full page, with the demo account buttons visible.
- **Explanation:** The sign-in page accepts a username or e-mail address and a password. The left panel
  introduces the product. The one-click **demo account** buttons come from the backend (`GET
  /api/auth/demo-accounts/`) and only appear when `DEMO_MODE=True` and the accounts exist, so they can be switched
  off without changing the frontend. Wrong credentials show a clear message, and sign-in attempts are rate limited.

### 02 - Sign-up page

- **Address:** `/register` · **Who:** everyone
- **Capture:** click **Create account** with some fields empty or a weak password, so the messages show.
- **Explanation:** Anyone can create an account. Self sign-up always creates a **requester**; support agents are
  created by an administrator. The password must pass Django's password rules (at least 8 characters, not common,
  not only digits, not similar to the username). Errors from the API appear under the matching field.

### 03 - Welcome animation

- **Address:** shown once right after signing in or signing up · **Who:** everyone
- **Capture:** take the screenshot about one second after clicking a demo account.
- **Explanation:** A short welcome screen with the user's name plays once after signing in, then the app fades in.
  It can be skipped with a click or `Esc` and does not play again on a page refresh.

### 04 - Requester dashboard

- **Address:** `/dashboard` · **Who:** requester (`riya`)
- **Capture:** the whole page.
- **Explanation:** A requester's own overview: tiles for **My tickets**, **Open**, **In progress** and **Resolved**,
  their tickets by status and by category, and the latest tickets. Every tile and bar links to the matching
  filtered ticket list. The numbers count up when the page opens, and the page refreshes itself every 30 seconds
  (see the *Updated* badge next to **New ticket**).

### 05 - My tickets

- **Address:** `/tickets` · **Who:** requester
- **Capture:** type a word such as `invoice` in the search box, or sort by a column.
- **Explanation:** Requesters only ever see the tickets they raised. The table has search, sorting, paging and
  filters (status, category, priority, created date). All of it runs on the server, and the filters are kept in the
  address so a view can be bookmarked. **Export** downloads exactly what the table shows.

### 06 - New ticket: validation

- **Address:** `/tickets/new` · **Who:** everyone
- **Capture:** click **Submit ticket** with the form empty.
- **Explanation:** A ticket has a title (5-150 characters), a category, a priority (pre-selected with the default
  priority) and a description (20-5000 characters). Character counters and hints guide the user, and every field
  explains what is missing. The same rules are enforced again by the API. The categories and priorities, with their
  icons and colours, come from the backend. The side panel gives tips and explains what happens next.

### 07 - New ticket: suggested category

- **Address:** `/tickets/new` · **Who:** everyone
- **Capture:** type the title `Money was taken from our card twice`, leave **Category** empty and wait a moment for
  the line under the field.
- **Explanation:** While the ticket is being typed, the same AI model suggests the likely category: the most similar
  past tickets vote for their category. Here it shows *Suggested category: Billing & Payments, based on 2 similar
  tickets*. **Use it** fills the field. If another category is already chosen the line reads *This reads like
  Billing & Payments* with **Switch**. The category is never picked automatically, and nothing is suggested when
  the similar tickets disagree. (96% of suggestions were right when tested on the demo data.)

### 08 - New ticket: attachments

- **Address:** `/tickets/new` · **Who:** everyone
- **Capture:** drop a screenshot and a `.log` file on the **Attachments** area, then also pick an `.exe` so the
  error shows.
- **Explanation:** Screenshots, logs and documents can be attached while raising a ticket (PNG, JPG, PDF, TXT, LOG,
  CSV, JSON, XLSX, DOCX, ZIP - up to 10 MB each and 5 files). The browser checks them straight away with the limits
  from the backend; the server checks them again, including that each file really is what its name says. The files
  are uploaded right after the ticket is created, with a progress bar.

### 09 - New ticket: similar resolved tickets

- **Address:** `/tickets/new` · **Who:** everyone
- **Capture:** title `The analytics page is painfully slow to open`, a description of a sentence or two, then
  **Find similar tickets**.
- **Explanation:** An open-source language model (`all-MiniLM-L6-v2`) running inside Django compares the draft with
  every resolved ticket and shows up to three that mean the same thing, even with different words. Here it finds
  *Dashboard takes more than a minute to load*. Each card shows a match label (strong or possible) and the
  resolution. The suggestions are advisory: nothing is changed and the ticket can still be submitted.

### 10 - Similar ticket details

- **Address:** `/tickets/new` · **Who:** everyone
- **Capture:** click **View details** on a suggestion.
- **Explanation:** The full problem and resolution of the suggested ticket open in a dialog, so the draft is not
  lost. Only the problem, category and resolution are shared, never who raised the old ticket.

### 11 - Ticket detail: requester view

- **Address:** `/tickets/<id>` · **Who:** the requester who raised it
- **Capture:** one of Riya's tickets that has comments and a status change.
- **Explanation:** The header shows the reference (`SSD-1001`), status, category, priority, who raised it, when, and
  who is assigned. Below are the description, the **activity timeline** (status changes, assignments, comments) and
  a comment box. The side panel explains the current status in plain words. The **Details** card lists every
  field across the page.

### 12 - Ticket attachments and image preview

- **Address:** `/tickets/<id>` · **Who:** the requester of the ticket, or an agent
- **Capture:** the **Attachments** card with an image thumbnail, then click the image to open the preview. The demo
  tickets *Webhook deliveries failing with 401 Unauthorized* (a log file) and *Invoice PDF is missing our GST
  number* (a PDF) already have files.
- **Explanation:** Images show as thumbnails and open full size; every file can be downloaded. **Add files** uploads
  more, and files can also be attached to a comment - the timeline shows them under that entry. The person who
  uploaded a file, or any agent, can remove it after a confirmation; both are recorded in the activity log. The
  files are stored in MongoDB itself (GridFS) and only the ticket's requester and the support team can open them.

### 13 - Agent dashboard

- **Address:** `/dashboard` · **Who:** agent (`meera`)
- **Capture:** the whole page.
- **Explanation:** The team overview: **Open queue**, **Assigned to me**, **Resolved this week** and **Avg.
  resolution time**, tickets by status and by category, and the latest tickets. Clicking a tile opens the ticket list
  already filtered.

### 14 - All tickets with filters

- **Address:** `/tickets?status=open&assigned_to=unassigned` · **Who:** agent
- **Capture:** the filtered list with the filter row visible.
- **Explanation:** Agents see every ticket, with extra **Raised by** and **Assignee** columns and an **Assignee**
  filter (me, unassigned or a named agent). Filters combine freely and are stored in the address. Searching,
  sorting and paging run in MongoDB, so they work the same for 30 or 300,000 tickets.

### 15 - Ticket detail: agent view

- **Address:** `/tickets/<id>` · **Who:** agent
- **Capture:** an open, unassigned ticket.
- **Explanation:** Agents get the **Manage ticket** panel: quick actions (**Assign to me**, **Start progress**) and a
  form for status, resolution note, assignee, priority and category. The status menu only offers the moves allowed
  from the current status. **Similar resolved tickets** are listed automatically, and **Use this note** copies an
  old resolution into the form for the agent to review; nothing is saved until they click save.

### 16 - Resolve without a note

- **Address:** `/tickets/<id>` · **Who:** agent
- **Capture:** set **Status = Resolved**, leave the note empty, click **Resolve ticket**.
- **Explanation:** A ticket cannot be resolved without a resolution note of at least 10 characters. The form says so
  under the field, and the API enforces the same rule.

### 17 - Resolved ticket

- **Address:** `/tickets/<id>` · **Who:** agent or requester
- **Capture:** after resolving a ticket with a note.
- **Explanation:** The green **Resolution** card shows the note, who resolved the ticket and when. The timeline
  records every step. The requester receives the resolution by e-mail, and the ticket can be re-opened if the
  problem comes back.

### 18 - Export menu

- **Address:** any table · **Who:** everyone (requesters export their own tickets only)
- **Capture:** open **Export** above the ticket table.
- **Explanation:** Every table offers **Download PDF**, **Download Excel** and **Email report**. The file is built by
  the backend from the same search, filters and sort order as the table.

### 19 - PDF report

- **Capture:** open the downloaded PDF.
- **Explanation:** A branded landscape report set in Poppins: a title block with a summary strip (records,
  generated, prepared by, active filters), coloured status and priority, a running header and footer, and *Page x of
  y*.

### 20 - Excel workbook

- **Capture:** open the downloaded `.xlsx` in Excel.
- **Explanation:** The same rows as a spreadsheet with a styled header row, frozen header and auto-filter, ready for
  further analysis.

### 21 - Email report dialog

- **Capture:** **Export → Email report…** with one or two addresses entered.
- **Explanation:** Any table can be e-mailed as a PDF or Excel attachment, with an optional subject and message.
  Addresses are entered as chips and checked before sending.

### 22 - Notification e-mail

- **Capture:** an e-mail in an inbox (see *Receive the demo accounts' e-mails* in the README) or the e-mail
  printed in the Django terminal.
- **Explanation:** Ticket events send branded HTML e-mails with a **View ticket** button: ticket received, new
  ticket alert, ticket assigned, status changed (with the resolution note), new comment and details changed.
  Nobody is e-mailed about their own action.

### 23 - Activity log

- **Address:** `/activity` · **Who:** agents only
- **Capture:** filter **Activity = Status changed**.
- **Explanation:** The audit trail of every change on every ticket: when, which ticket, what happened and who did
  it. It can be searched, filtered by activity type, sorted and exported like any other table.

### 24 - Users

- **Address:** `/users` · **Who:** agents only
- **Capture:** filter **Role = Support Agent** or leave all users.
- **Explanation:** The user directory with role, job title, status, join date and last sign-in, with search, role
  filter, sorting and export.

### 25 - Configuration: ticket categories

- **Address:** `/configuration` · **Who:** agents only
- **Capture:** the **Ticket category** list selected.
- **Explanation:** Nothing selectable is hard-coded in the frontend. The configurable lists (**Ticket category**,
  **Ticket priority**, **Email notifications**) are cards at the top; the table shows the selected list's values
  with their icon, colour, order and an **Active** switch. Deactivating a value hides it from new tickets but keeps
  old tickets intact. A value that tickets use cannot be deleted.

### 26 - Add / edit value dialog

- **Capture:** **Add ticket category** with a label, an icon such as `devices` and a colour.
- **Explanation:** A live preview shows the badge as it will appear. Suggested icons and colours can be picked with
  one click. After saving, the new category appears in every form and filter without any frontend change.

### 27 - Configuration: e-mail notifications

- **Capture:** the **Email notifications** list selected.
- **Explanation:** Each row is an action that sends an e-mail. Switching **Active** off stops that e-mail
  immediately. These rows are built in, so they can be renamed and switched on or off but not added or deleted.

### 28 - Account menu and greeting

- **Capture:** open the account menu in the top-right corner.
- **Explanation:** The top bar greets the user by time of day with a waving hand, shows their role, and the account
  menu offers shortcuts (*My tickets*, *Assigned to me* for agents) and **Sign out**. The sidebar shows the agents-only
  pages under *Support team*.

### 29 - Mobile layout

- **Capture:** narrow the window to about 400 px (or use DevTools device mode) and open the menu.
- **Explanation:** The layout is responsive: the sidebar becomes a slide-out menu, less important table columns are
  hidden, and forms stack into one column.

### 30 - Page not found

- **Address:** `/does-not-exist`
- **Explanation:** Unknown addresses show a friendly page with a link back to the app.

### 31 - Django admin

- **Address:** `http://localhost:8000/admin/` · **Who:** `admin` / `Admin@12345`
- **Capture:** the admin home page, or the user list.
- **Explanation:** Administrators create support agents, change roles, and manage configuration lists and tickets
  in the Django admin, which comes with Django.

### 32 - MongoDB Compass

- **Capture:** the `smart_support_desk` database with its collections, and a ticket document in `tickets_ticket`.
- **Explanation:** All data is stored in MongoDB. Each Django model is a collection, references are ObjectIds, and
  the indexes are created by `migrate`. See [ER_DIAGRAMS.md](ER_DIAGRAMS.md) for every collection.

### 33 - AI comparison in the terminal

- **Capture:** `python manage.py similar_tickets "The analytics page is painfully slow to open"` in the backend
  terminal.
- **Explanation:** The command prints the model's matches next to plain keyword matching, showing why a language
  model is used: the right ticket is found even though the two texts share almost no words.

### 34 - Continuous integration

- **Capture:** a green run on GitHub → **Actions**, and the result e-mail.
- **Explanation:** Every push runs the backend tests against a real MongoDB 8, the frontend unit tests and a
  production build, then e-mails the result with a link to the log.
