#!/usr/bin/env bash
# One-time setup of a fresh Ubuntu server (e.g. a Google Cloud e2-micro): swap,
# Docker, the app's code, deploy/.env, daily database backups and DuckDNS updates.
#
#   curl -fsSL https://raw.githubusercontent.com/himanshut2512-web/instant_interview_prep/develop/deploy/setup-server.sh | bash
set -euo pipefail

REPO="${REPO:-https://github.com/himanshut2512-web/instant_interview_prep.git}"
BRANCH="${BRANCH:-develop}"
DIR="${DIR:-$HOME/instant_interview_prep}"

echo "==> Swap (a 1 GB machine needs it to build the frontend)"
if ! swapon --show | grep -q .; then
  sudo fallocate -l 2G /swapfile
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile >/dev/null
  sudo swapon /swapfile
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab >/dev/null
fi

echo "==> Docker"
if ! command -v docker >/dev/null; then
  curl -fsSL https://get.docker.com | sudo sh
fi
sudo usermod -aG docker "$USER"
command -v git >/dev/null || sudo apt-get install -y git

echo "==> Code ($BRANCH)"
if [ -d "$DIR/.git" ]; then
  git -C "$DIR" pull --ff-only
else
  git clone --branch "$BRANCH" "$REPO" "$DIR"
fi
cd "$DIR/deploy"
chmod +x ./*.sh
if [ ! -f .env ]; then
  cp .env.example .env
  chmod 600 .env
fi

echo "==> Scheduled jobs: database backup daily at 03:00, DuckDNS update every 5 minutes"
( crontab -l 2>/dev/null | grep -v "$DIR/deploy/" || true
  echo "0 3 * * * $DIR/deploy/backup.sh >> $HOME/instantprep-backup.log 2>&1"
  echo "*/5 * * * * $DIR/deploy/duckdns.sh >> $HOME/instantprep-duckdns.log 2>&1"
) | crontab -

cat <<EOF

Done. Next:
  1. Fill in your settings:   nano $DIR/deploy/.env
  2. Start the site:          cd $DIR/deploy && sudo docker compose up -d --build
     (the first build takes several minutes on a small machine)
  3. Check it:                sudo docker compose exec app python -m app.setup_auth --check
EOF
