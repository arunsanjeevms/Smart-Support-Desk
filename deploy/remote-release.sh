#!/usr/bin/env bash
# Runs ON THE SERVER (as root) to install one release that deploy.sh uploaded.
#
#   bash remote-release.sh /tmp/predigle-release-<stamp>.tar.gz
#
# Unpacks the release, installs Python packages, runs migrations, collects static
# files, builds the AI index, switches the "current" link, restarts the API and
# checks it is healthy - switching back to the previous release if it is not.
set -euo pipefail

ARCHIVE=$1
APP_USER=predigle
APP_DIR=/var/www/predigle
STAMP=$(date +%Y%m%d-%H%M%S)
RELEASE=$APP_DIR/releases/$STAMP
VENV=$APP_DIR/shared/venv
SHARED_ENV=$APP_DIR/shared/.env
KEEP=3

[ -f "$SHARED_ENV" ] || { echo "Missing $SHARED_ENV - create it first (see deploy/README.md)."; exit 1; }

echo "== Unpack $STAMP"
mkdir -p "$RELEASE"
tar -xzf "$ARCHIVE" -C "$RELEASE"
ln -sfn "$SHARED_ENV" "$RELEASE/backend/.env"
chown -R "$APP_USER:$APP_USER" "$RELEASE"

as_app() { sudo -u "$APP_USER" env HF_HOME=$APP_DIR/shared/hf-cache OMP_NUM_THREADS=1 "$@"; }
manage() { (cd "$RELEASE/backend" && as_app "$VENV/bin/python" manage.py "$@"); }

echo "== Python packages (CPU-only PyTorch first, to avoid the large CUDA build)"
TORCH=$(grep '^torch==' "$RELEASE/backend/requirements.txt")
as_app "$VENV/bin/pip" install -q --upgrade pip
as_app "$VENV/bin/pip" install -q "$TORCH" --index-url https://download.pytorch.org/whl/cpu
as_app "$VENV/bin/pip" install -q -r "$RELEASE/backend/requirements.txt" gunicorn==23.0.0

echo "== Database migrations and static files"
manage migrate --no-input
manage collectstatic --no-input --verbosity 0
ln -sfn "$RELEASE/backend/staticfiles" "$RELEASE/static"

echo "== AI index (downloads the model on the first release)"
manage build_similarity_index

echo "== Switch to the new release"
PREVIOUS=$(readlink "$APP_DIR/current" || true)
ln -sfn "$RELEASE" "$APP_DIR/current.new" && mv -Tf "$APP_DIR/current.new" "$APP_DIR/current"
install -m 644 "$RELEASE/deploy/systemd/predigle-api.service" /etc/systemd/system/predigle-api.service
systemctl daemon-reload
systemctl enable predigle-api >/dev/null 2>&1
systemctl restart predigle-api

echo "== Health check"
for i in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:8010/api/health/ >/dev/null 2>&1; then
    echo "API is healthy: $(curl -fsS http://127.0.0.1:8010/api/health/)"
    break
  fi
  sleep 2
  if [ "$i" = 30 ]; then
    echo "API did not become healthy - switching back."
    journalctl -u predigle-api -n 30 --no-pager || true
    if [ -n "$PREVIOUS" ] && [ -d "$PREVIOUS/backend" ]; then
      ln -sfn "$PREVIOUS" "$APP_DIR/current"
      systemctl restart predigle-api
    fi
    exit 1
  fi
done

echo "== Nginx"
install -m 644 "$RELEASE/deploy/nginx/predigle.conf" /etc/nginx/sites-available/predigle
ln -sfn /etc/nginx/sites-available/predigle /etc/nginx/sites-enabled/predigle
nginx -t && systemctl reload nginx

echo "== Keep the last $KEEP releases"
ls -1dt "$APP_DIR"/releases/*/ | tail -n +$((KEEP + 1)) | grep -v bootstrap | xargs -r rm -rf
rm -f "$ARCHIVE"
echo "Release $STAMP is live."
