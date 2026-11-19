#!/usr/bin/env bash
# One-time setup of the VPS for Smart Support Desk (no Docker). Safe to run again.
#
#   scp deploy/server-setup.sh deploy/mongod.conf root@SERVER:/tmp/ && ssh root@SERVER 'bash /tmp/server-setup.sh'
#
# Installs Python 3.13 (deadsnakes), MongoDB 8.0 (official repo), a 2 GB swap file,
# the "predigle" app user and the folders the releases live in.
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

APP_USER=predigle
APP_DIR=/var/www/predigle

echo "== CPU check (MongoDB 5+ and NumPy need AVX / SSE4.2)"
grep -qw avx /proc/cpuinfo && grep -qw sse4_2 /proc/cpuinfo || { echo "This CPU lacks AVX/SSE4.2 - stopping."; exit 1; }

echo "== Swap: 2 GB (the server has about 1 GB of RAM)"
if [ "$(swapon --show=SIZE --noheadings --bytes | head -1)" != "2147483648" ]; then
  swapoff /swapfile 2>/dev/null || true
  fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile >/dev/null && swapon /swapfile
  grep -q '^/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

echo "== Python 3.13"
if ! command -v python3.13 >/dev/null; then
  apt-get update -qq
  apt-get install -y -qq software-properties-common >/dev/null
  add-apt-repository -y ppa:deadsnakes/ppa >/dev/null
  apt-get update -qq
fi
apt-get install -y -qq python3.13 python3.13-venv >/dev/null

echo "== MongoDB 8.0"
if ! command -v mongod >/dev/null; then
  apt-get install -y -qq gnupg curl >/dev/null
  curl -fsSL https://pgp.mongodb.com/server-8.0.asc | gpg --dearmor -o /usr/share/keyrings/mongodb-server-8.0.gpg --yes
  echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-8.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/8.0 multiverse" \
    > /etc/apt/sources.list.d/mongodb-org-8.0.list
  apt-get update -qq
  apt-get install -y -qq mongodb-org >/dev/null
fi
install -m 644 /tmp/mongod.conf /etc/mongod.conf
systemctl enable --now mongod
systemctl restart mongod

echo "== App user and folders"
id "$APP_USER" >/dev/null 2>&1 || useradd --system --create-home --shell /usr/sbin/nologin "$APP_USER"
mkdir -p "$APP_DIR"/{releases,shared/hf-cache,acme}
chown -R "$APP_USER:$APP_USER" "$APP_DIR"
chmod 750 "$APP_DIR/shared"

echo "== Python environment"
if [ ! -x "$APP_DIR/shared/venv/bin/python" ]; then
  sudo -u "$APP_USER" python3.13 -m venv "$APP_DIR/shared/venv"
fi

echo "== Done"
python3.13 --version; mongod --version | head -1; free -h | sed -n 2,3p
