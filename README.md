# viltrumlik.uz — Atlas portfolio

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

## Deploy (viltrumlik.uz)

Live app dir: `/home/viltrumlik/portfolio`, user `guts`, gunicorn on `/run/guts.sock` (socket-activated by `guts.socket`).

### Automatic

Every push to `main` runs `.github/workflows/deploy.yml`. It runs shellcheck, pytest, vitest, the typecheck and the frontend build. If they all pass, it packs a release with `deploy/make-release.sh` and pipes it over SSH to the server. Pushes that only touch docs or Markdown are skipped, and you can also start a run by hand from the Actions tab.

On the server, `/usr/local/bin/portfolio-deploy` (`deploy/portfolio-deploy.sh`) takes over:
1. Back up the code and the database to `/var/backups/portfolio/` (the newest 10 of each are kept).
2. Sync the files, then run pip, `migrate` and `collectstatic`.
3. Restart `guts.service` and check that `/`, `/work/`, `/writing/` and `/api/live/now.json` return 200.
4. If any step or the health check fails, restore that code and database and restart, and the workflow goes red.

`.env`, `.venv`, `db.sqlite3*`, `public/` and the job lock are never touched. The live revision is in `REVISION`.

### By hand

```bash
npm --prefix frontend run build
deploy/make-release.sh > release.tar.gz
ssh root@viltrumlik.uz portfolio-deploy < release.tar.gz
```

Don't rsync from a Mac with `--delete`: macOS openrsync deletes excluded files. `portfolio-deploy` runs rsync on the server, where `--delete` respects the exclusions.

### One-time server setup

1. `.env` additions:
   - `ATLAS_FERNET_KEYS`: generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`. Put the newest key first and keep old keys listed so you can rotate.
   - `SITE_URL=https://viltrumlik.uz`
2. nginx (`/etc/nginx/sites-available/viltrumlik`, inside the proxy `location`): `proxy_set_header X-Real-IP $remote_addr;`. The contact-form and studio-login rate limits read the client IP from it.
3. Job timer: copy `deploy/guts-jobs.service` and `deploy/guts-jobs.timer` to `/etc/systemd/system/`, then `systemctl daemon-reload && systemctl enable --now guts-jobs.timer`.
4. Deploy script: `install -m 755 deploy/portfolio-deploy.sh /usr/local/bin/portfolio-deploy`. Reinstall it by hand when it changes; a deploy never replaces its own script.
5. Deploy key: create it with `ssh-keygen -t ed25519 -N "" -f deploy_key`.
   - Add the public key to root's `~/.ssh/authorized_keys` as `command="/usr/local/bin/portfolio-deploy",restrict ssh-ed25519 AAAA… github-actions-deploy`. That key can then only run the deploy: no shell, no port forwarding.
   - Store the private key as the `DEPLOY_SSH_KEY` repository secret, then delete the local copy.
6. Connect services in `/studio/`.

### Rollback

A failed deploy rolls itself back. To return to an earlier release on purpose, run `portfolio-deploy` again with that commit's release, or restore a pair from `/var/backups/portfolio/` by hand:
1. Stop `guts.socket` and `guts.service`.
2. Extract `code-<time>.tar.gz` over the app dir.
3. Copy `db-<time>.sqlite3` to `db.sqlite3` as `guts`, and remove the `-wal` and `-shm` files.
4. Start the socket and the service.

## License

This project is open source and available under the [MIT License](LICENSE).

Third-party assets keep their own licenses: Bricolage Grotesque and Martian Mono (SIL Open Font License, via Google Fonts) and Preact (MIT).
