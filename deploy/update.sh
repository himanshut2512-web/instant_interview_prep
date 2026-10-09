#!/usr/bin/env bash
# Deploy the latest code: pull, rebuild and restart. Data stays in the prep-data volume.
#   cd ~/instant_interview_prep/deploy && ./update.sh
set -euo pipefail
cd "$(dirname "$0")"
docker info >/dev/null 2>&1 && DOCKER="docker" || DOCKER="sudo docker"  # before re-login, docker needs sudo
./backup.sh || echo "(backup skipped: is the app running?)"
git pull --ff-only
$DOCKER compose up -d --build
$DOCKER image prune -f >/dev/null
$DOCKER compose ps
