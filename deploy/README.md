# Deployment (VPS, no Docker)

Live at **https://predigle.arunsanjeev.dev** - the same stack as on a laptop:
Angular build served by Nginx, Django + Gunicorn, MongoDB 8, and the local Sentence Transformers model.

```
Browser ──HTTPS──> Cloudflare ──> Nginx (Let's Encrypt)
                                   ├── /            Angular build   (/var/www/predigle/current/frontend)
                                   ├── /static/     Django static   (/var/www/predigle/current/static)
                                   └── /api/ /admin/ ──> Gunicorn 127.0.0.1:8010 ──> MongoDB 127.0.0.1:27017
```

| File | Purpose |
|---|---|
| `server-setup.sh` | one-time setup: Python 3.13, MongoDB 8.0, 2 GB swap, the `predigle` user and folders |
| `mongod.conf` | MongoDB listens on 127.0.0.1 only, with a 0.25 GB cache for a 1 GB RAM server |
| `deploy.sh` | run on your PC: builds Angular, packs the committed backend, copies it with **scp**, installs it |
| `remote-release.sh` | runs on the server: packages, migrations, static files, AI index, switch, restart, health check, rollback |
| `systemd/predigle-api.service` | Gunicorn service (1 worker, 4 threads, restarts on failure) |
| `nginx/predigle.conf` | the Nginx site: HTTPS, security headers, `/api/` and `/admin/` proxy, single-page app fallback |
| `db_export.py` | exports a local MongoDB in `mongodump` format, to copy data to the server with `mongorestore` |

## Server requirements

- Ubuntu 22.04, about 1 GB RAM is enough with the 2 GB swap from `server-setup.sh`.
- A CPU with **AVX and SSE4.2** - MongoDB 5+ and NumPy / PyTorch need them. On a KVM VPS ask the provider for
  *host CPU passthrough* if `grep -o 'avx\|sse4_2' /proc/cpuinfo` prints nothing.
- A DNS A record for the domain pointing to the server, and a Let's Encrypt certificate (webroot
  `/var/www/predigle/acme`).

## Deploy an update

Commit your changes, then from the repo root in Git Bash:

```bash
bash deploy/deploy.sh
```

Each release goes to `/var/www/predigle/releases/<time>/`; `current` points at the live one and the last three are
kept. If the new release fails its health check, the previous one is switched back automatically.

## Settings on the server

`/var/www/predigle/shared/.env` (owner `predigle`, mode 600) holds the production settings and secrets - never commit
it. Besides the variables in `backend/.env.example` it sets:

```ini
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<long random value>
DJANGO_ALLOWED_HOSTS=predigle.arunsanjeev.dev,127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=https://predigle.arunsanjeev.dev
BEHIND_HTTPS_PROXY=True
FRONTEND_URL=https://predigle.arunsanjeev.dev
```

## Copy a local database to the server

```bash
backend/.venv/Scripts/python.exe deploy/db_export.py dump
scp -r dump root@SERVER:/tmp/dump
ssh root@SERVER 'mongorestore --drop --db smart_support_desk /tmp/dump'
```

## Useful commands on the server

| What | Command |
|---|---|
| API status / logs | `systemctl status predigle-api` · `journalctl -u predigle-api -f` |
| Restart the API | `systemctl restart predigle-api` |
| Django management | `cd /var/www/predigle/current/backend && sudo -u predigle ../../shared/venv/bin/python manage.py <command>` |
| MongoDB shell | `mongosh smart_support_desk` |
| Nginx check / reload | `nginx -t && systemctl reload nginx` |
