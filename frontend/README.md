# Smart Support Desk - Angular frontend

See the [main README](../README.md) for the full setup. Quick reference:

```powershell
npm install        # once
npm start          # dev server on http://localhost:4200 (expects the API on http://localhost:8000)
npm run test:ci    # unit tests (Vitest)
npm run build      # production build in dist/
```

The API address lives in `src/environments/environment*.ts`.

Code layout (`src/app/`):

| Folder | What is inside |
|---|---|
| `core/` | API, auth, config and export services, the auth interceptor, route guards, TypeScript models |
| `shared/` | reusable UI: `DataTable` + `TableSource`, export menu and e-mail dialog, badges, avatar, dialogs, pipes |
| `layout/` | the app shell (sidebar, top bar, account menu) |
| `features/` | one folder per screen: auth, dashboard, tickets, activity, users, configuration |
