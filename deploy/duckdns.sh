#!/usr/bin/env bash
# Point the DuckDNS name at this server's current public IP (run every 5 minutes
# from cron). Needs DOMAIN=<name>.duckdns.org and DUCKDNS_TOKEN in deploy/.env.
set -euo pipefail
cd "$(dirname "$0")"

value() { { grep -E "^$1=" .env || true; } | tail -n 1 | cut -d= -f2- | tr -d '"' ; }
domain="$(value DOMAIN)"
token="$(value DUCKDNS_TOKEN)"
case "$domain" in
  *.duckdns.org) ;;
  *) exit 0 ;;  # not a DuckDNS name: nothing to update
esac
[ -n "$token" ] || exit 0

answer="$(curl -fsS --max-time 20 "https://www.duckdns.org/update?domains=${domain%.duckdns.org}&token=${token}&ip=")"
if [ "$answer" != "OK" ]; then
  echo "$(date '+%F %T') DuckDNS update failed: $answer"
  exit 1
fi
