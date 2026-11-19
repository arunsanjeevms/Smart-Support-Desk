#!/usr/bin/env bash
# Deploy the committed code to the VPS (run from the repo root in Git Bash).
#
#   bash deploy/deploy.sh
#
# Builds the Angular app, packs it with the backend (from Git - never .env or
# .venv), copies the bundle with scp and runs deploy/remote-release.sh on the server.
set -euo pipefail

SERVER=${DEPLOY_SERVER:-root@45.195.129.71}
SSH_KEY=${DEPLOY_SSH_KEY:-$HOME/.ssh/predigle_vps_admin}
SSH_OPTS=(-i "$SSH_KEY" -o BatchMode=yes)

ROOT=$(git rev-parse --show-toplevel)
cd "$ROOT"
if ! git diff --quiet HEAD -- backend frontend deploy; then
  echo "Uncommitted changes in backend/, frontend/ or deploy/ - commit them first so the server runs what is in Git."
  exit 1
fi

STAMP=$(date +%Y%m%d-%H%M%S)
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

echo "== Build the Angular app"
(cd frontend && npm run build --silent)

echo "== Pack the release"
mkdir -p "$WORK/release/frontend"
git archive HEAD backend deploy | tar -x -C "$WORK/release"
cp -r frontend/dist/frontend/browser/. "$WORK/release/frontend/"
tar -czf "$WORK/release.tar.gz" -C "$WORK/release" .
echo "   $(du -h "$WORK/release.tar.gz" | cut -f1) for commit $(git rev-parse --short HEAD)"

echo "== Upload and install"
scp "${SSH_OPTS[@]}" -q "$WORK/release.tar.gz" "$SERVER:/tmp/predigle-release-$STAMP.tar.gz"
scp "${SSH_OPTS[@]}" -q deploy/remote-release.sh "$SERVER:/tmp/remote-release.sh"
ssh "${SSH_OPTS[@]}" "$SERVER" "sed -i 's/\r$//' /tmp/remote-release.sh && bash /tmp/remote-release.sh /tmp/predigle-release-$STAMP.tar.gz"
