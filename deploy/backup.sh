#!/usr/bin/env bash
# Back up the database (users, sessions, prep kits) inside the data volume and keep
# the 14 newest copies. Runs daily from cron; safe to run by hand: ./backup.sh
#
# Copy the newest backup to the server's disk, e.g. to download it:
#   sudo docker compose cp app:/app/data/backups/<file> .
set -euo pipefail
cd "$(dirname "$0")"
docker info >/dev/null 2>&1 && DOCKER="docker" || DOCKER="sudo docker"  # before re-login, docker needs sudo

$DOCKER compose exec -T app python - <<'PY'
import pathlib
import sqlite3
import time

data = pathlib.Path("/app/data")
backups = data / "backups"
backups.mkdir(exist_ok=True)
target = backups / time.strftime("prep-%Y%m%d-%H%M%S.db")
source = sqlite3.connect(data / "prep.db")
copy = sqlite3.connect(target)
with copy:
    source.backup(copy)  # a consistent copy, safe while the app is running
source.close()
copy.close()
for old in sorted(backups.glob("prep-*.db"))[:-14]:
    old.unlink()
print(f"{time.strftime('%Y-%m-%d %H:%M')} backup written: {target.name}")
PY
