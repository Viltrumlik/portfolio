#!/usr/bin/env bash
# Writes a release for portfolio-deploy to stdout as .tar.gz: the committed tree at HEAD, the built
# frontend (static/dist, which git ignores) and a REVISION file. Build the frontend first:
#   npm --prefix frontend run build && deploy/make-release.sh > release.tar.gz
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
[[ -f static/dist/.vite/manifest.json ]] || { echo "static/dist is missing: run npm --prefix frontend run build" >&2; exit 1; }
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
# mktemp makes the folder 0700, and the archive root carries that mode onto the app dir on the server,
# where nginx (www-data) then can't reach /static/ or /media/.
chmod 755 "$tmp"
git archive --format=tar HEAD | tar -x -C "$tmp"
mkdir -p "$tmp/static"
rsync -a --exclude='.DS_Store' static/dist/ "$tmp/static/dist/"
git rev-parse --short=12 HEAD > "$tmp/REVISION"
COPYFILE_DISABLE=1 tar --no-xattrs -czf - -C "$tmp" .
