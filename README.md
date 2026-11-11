# guts.uz — Atlas portfolio

A self-updating developer portfolio. The home page is a desk of draggable windows (about, GitHub graph, now playing) built on the **Atlas** design system. The site syncs from connected services (GitHub, Telegram, Last.fm, outgoing webhooks) and runs small "When → Then" automations.

- Design system docs: [`docs/atlas/`](docs/atlas/README.md) (source artifact: https://claude.ai/artifact/TndfdnbUBDitsktiuHwtJQ)
- Stack: Django 5.2 LTS, SQLite (WAL), server-rendered templates + Preact islands (Vite), background jobs via a systemd timer.

## Apps

| App | What it does |
|---|---|
| `web` | Public pages, Atlas template tags (`{% load atlas %}`), RSS, sitemap, OG images, contact form, `/api/live/*.json`, CSP |
| `content` | Profile, experience, skills, services, posts, projects; `import_legacy` command |
| `integrations` | GitHub / Telegram / Last.fm connections (encrypted credentials), sync, `/hooks/github/`, outgoing webhooks with SSRF guard |
| `automations` | Events and rules (When → Then), built-in rules |
| `jobs` | Database job queue + `run_jobs` runner (retries with backoff) |
| `studio` | Owner-only `/studio/`: connections, webhooks, automations, content, inbox, jobs |
| `frontend/` | Vite + TypeScript + Preact: Atlas CSS (generated from `tokens.json`) and islands (desk drag, clock, now, ⌘K palette, theme, template preview) |

`legacy/` holds the previous site's code until it is deleted.

## Local development

```bash
python -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py import_legacy        # one-time: old content → new models
npm --prefix frontend install
npm --prefix frontend run build                 # or: npm --prefix frontend run dev + VITE_DEV_SERVER=http://localhost:5173
.venv/bin/python manage.py runserver
```

Studio: `/studio/` (staff users only; create one with `createsuperuser`). Connect GitHub with a read-only fine-grained token, then press "Sync now".

Tests:

```bash
.venv/bin/python -m pytest
npm --prefix frontend test
```

## Background jobs

`manage.py run_jobs` schedules periodic syncs (GitHub hourly + public events every 5 min, Last.fm every minute) and runs due jobs for ~50 s. Production runs it every minute with `deploy/guts-jobs.timer`. `manage.py sync_now <provider>` forces a sync.

## Deploy (guts.uz)

Live app dir: `/home/viltrumlik/portfolio`, user `guts`, gunicorn on `/run/guts.sock`.

1. Build the frontend locally: `npm --prefix frontend run build` (writes `static/dist/`).
2. Back up the server database: `cp db.sqlite3 db.sqlite3.pre-atlas`.
3. rsync the code **without `--delete`** (macOS openrsync deletes excluded files), excluding `.venv .git __pycache__ '*.pyc' .env db.sqlite3* graphify-out .claude .DS_Store public frontend/node_modules`. Include `static/dist/`.
4. On the server (as `guts`): `pip install -r requirements.txt`, `python manage.py migrate`, `python manage.py import_legacy` (first deploy only), `python manage.py collectstatic --noinput`.
5. `.env` additions:
   - `ATLAS_FERNET_KEYS` — generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`. Newest key first; keep old keys listed to rotate.
   - `SITE_URL=https://guts.uz`
6. nginx (`/etc/nginx/sites-available/guts`, inside the proxy `location`): `proxy_set_header X-Real-IP $remote_addr;` — the contact-form and studio-login rate limits read the client IP from it.
7. Install the job timer: copy `deploy/guts-jobs.service` and `deploy/guts-jobs.timer` to `/etc/systemd/system/`, then `systemctl daemon-reload && systemctl enable --now guts-jobs.timer`.
8. `systemctl restart guts.service`, then connect services in `/studio/`.

Rollback: restore the previous code and `db.sqlite3.pre-atlas`, `systemctl disable --now guts-jobs.timer`, restart `guts.service`. The old tables stay in the database until a later cleanup release.
