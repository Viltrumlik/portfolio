#!/usr/bin/env bash
# Deploys one release of the portfolio, read as a .tar.gz from stdin, then health-checks it and
# rolls back on failure.
#
# Installed as /usr/local/bin/portfolio-deploy. GitHub Actions reaches it with a deploy key that
# root's authorized_keys locks to this one command:
#   command="/usr/local/bin/portfolio-deploy",restrict ssh-ed25519 AAAA... github-actions-deploy
# so that key can't open a shell, forward ports or run anything else.
# By hand, as root on the server:  portfolio-deploy < release.tar.gz
#
# Steps: unpack -> back up code and database -> sync files -> pip, migrate, collectstatic -> restart
# -> health check -> on failure, restore the code and database backups and restart again.
set -Eeuo pipefail

APP=/home/viltrumlik/portfolio
OWNER=guts
SERVICE=guts.service
SOCKET=guts.socket
JOBS_TIMER=guts-jobs.timer
BACKUPS=/var/backups/portfolio
WORK=/var/lib/portfolio-deploy
KEEP=10
SITE=viltrumlik.uz
HEALTH_PATHS=${PORTFOLIO_DEPLOY_HEALTH_PATHS:-"/ /work/ /writing/ /api/live/now.json"}

# Never touched by a deploy: secrets, the virtualenv, the database and its backups, uploads and
# collected static files, the job lock. This rsync runs on the server (GNU rsync), where --delete
# never removes excluded paths.
RSYNC_PROTECT=(--exclude='/.env*' --exclude='/.venv/' --exclude='/db.sqlite3*' --exclude='/public/'
               --exclude='/.run_jobs.lock' --exclude='/REVISION' --exclude='__pycache__/' --exclude='*.pyc')
TAR_PROTECT=(--exclude='./.env*' --exclude='./.venv' --exclude='./db.sqlite3*' --exclude='./public'
             --exclude='./.run_jobs.lock' --exclude='__pycache__' --exclude='*.pyc' --exclude='node_modules')

log() { printf '%s  %s\n' "$(date -u +%H:%M:%S)" "$*"; }
manage() { (cd "$APP" && sudo -u "$OWNER" "$APP/.venv/bin/python" manage.py "$@"); }

exec 9>/run/portfolio-deploy.lock
flock -n 9 || { log "another deploy is running"; exit 75; }

stamp=$(date -u +%Y%m%d-%H%M%S)
release="$WORK/release-$stamp"
install -d -m 700 "$WORK"
install -d -o "$OWNER" -g "$OWNER" -m 700 "$BACKUPS"
cleanup() { rm -rf "$release" "$WORK/rollback-$stamp"; systemctl start "$JOBS_TIMER" || true; }
trap cleanup EXIT

log "unpacking release"
mkdir -p "$release"
tar -xzf - -C "$release"
for required in manage.py requirements.txt static/dist/.vite/manifest.json; do
  [[ -e "$release/$required" ]] || { log "release is missing $required; nothing was changed"; exit 65; }
done
revision=$(cat "$release/REVISION" 2>/dev/null || echo unknown)
previous=$(cat "$APP/REVISION" 2>/dev/null || echo unknown)
log "release $revision (live: $previous)"

systemctl stop "$JOBS_TIMER"

log "backing up code and database"
code_backup="$BACKUPS/code-$stamp.tar.gz"
db_backup="$BACKUPS/db-$stamp.sqlite3"
tar -czf "$code_backup" -C "$APP" "${TAR_PROTECT[@]}" .
# As the owner, so SQLite's -wal/-shm files never end up owned by root.
sudo -u "$OWNER" "$APP/.venv/bin/python" -c \
  'import sqlite3, sys; a = sqlite3.connect(sys.argv[1]); b = sqlite3.connect(sys.argv[2]); a.backup(b); b.close(); a.close()' \
  "$APP/db.sqlite3" "$db_backup"

healthy() {
  local path code asset
  for path in $HEALTH_PATHS; do
    code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 --resolve "$SITE:443:127.0.0.1" "https://$SITE$path" || true)
    [[ "$code" == 200 ]] || { log "health: $path -> $code"; return 1; }
  done
  # The home page's own stylesheet must load too. nginx serves it straight from disk, so this catches
  # file-permission mistakes that the HTML pages (served by gunicorn) never show.
  asset=$(curl -s --max-time 10 --resolve "$SITE:443:127.0.0.1" "https://$SITE/" | grep -o '/static/[^"]*\.css' | head -1 || true)
  [[ -n "$asset" ]] || { log "health: no stylesheet linked from /"; return 1; }
  code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 --resolve "$SITE:443:127.0.0.1" "https://$SITE$asset" || true)
  [[ "$code" == 200 ]] || { log "health: $asset -> $code"; return 1; }
}

wait_healthy() {
  for _ in $(seq 1 15); do
    healthy 2>/dev/null && return 0
    sleep 2
  done
  healthy  # once more, logging which path failed
}

rollback() {
  log "ROLLING BACK to $previous"
  # Stop the socket too, or an incoming request would start the service mid-restore.
  systemctl stop "$SOCKET" "$SERVICE" || true
  local old="$WORK/rollback-$stamp"
  mkdir -p "$old"
  tar -xzf "$code_backup" -C "$old"
  rsync -a --no-owner --no-group --delete "${RSYNC_PROTECT[@]}" "$old/" "$APP/"
  rm -f "$APP/db.sqlite3-wal" "$APP/db.sqlite3-shm"
  install -o "$OWNER" -g "$OWNER" -m 644 "$db_backup" "$APP/db.sqlite3"
  echo "$previous" > "$APP/REVISION"
  chown -R "$OWNER:$OWNER" "$APP"
  chmod 755 "$APP"
  systemctl start "$SOCKET" "$SERVICE"
  if wait_healthy; then log "rolled back; the site is up on $previous"; else log "rolled back, but the site is STILL unhealthy"; fi
}

# Each step checks its own exit code: deploy() runs as an `if` condition, where bash ignores set -e.
step() { log "$1"; shift; "$@" || { log "step failed (exit $?): $*"; return 1; }; }

deploy() {
  step "syncing files" rsync -a --no-owner --no-group --delete "${RSYNC_PROTECT[@]}" "$release/" "$APP/" || return 1
  echo "$revision" > "$APP/REVISION"
  step "fixing ownership" chown -R "$OWNER:$OWNER" "$APP" || return 1
  # nginx (www-data) must be able to enter the app dir to serve /static/ and /media/.
  step "fixing permissions" chmod 755 "$APP" || return 1
  step "installing requirements" sudo -u "$OWNER" "$APP/.venv/bin/pip" install -q --disable-pip-version-check -r "$APP/requirements.txt" || return 1
  step "migrating" manage migrate --noinput || return 1
  # No --clear: pages already open in a browser keep their old hashed assets.
  step "collecting static files" manage collectstatic --noinput -v 0 || return 1
  step "restarting $SERVICE" systemctl restart "$SERVICE" || return 1
  log "health check"
  wait_healthy
}

if deploy; then
  log "DEPLOYED $revision"
else
  rollback
  log "FAILED: $revision was not deployed"
  exit 1
fi

# Keep the newest $KEEP backups of each kind.
for pattern in 'code-*.tar.gz' 'db-*.sqlite3'; do
  find "$BACKUPS" -maxdepth 1 -name "$pattern" -printf '%T@ %p\n' | sort -rn | tail -n +$((KEEP + 1)) | cut -d' ' -f2- | xargs -r rm -f
done
