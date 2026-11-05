#!/usr/bin/env sh
# Bootstraps the node DB from Mithril on first run, then starts everything.
set -eu
cd "$(dirname "$0")"

# Pick up EGC_CARDANO_DIR etc. from .env so the script and compose agree
if [ -f .env ]; then set -a; . ./.env; set +a; fi

NODE_DB_DIR="${EGC_CARDANO_DIR:-./cardano}/data/node-db"

if [ -n "$(ls -A "$NODE_DB_DIR/db" 2>/dev/null)" ]; then
  echo "Existing node DB in $NODE_DB_DIR/db, skipping Mithril bootstrap."
else
  echo "No node DB found, downloading Mithril snapshot..."
  # Create it ourselves so Docker doesn't make it root-owned
  mkdir -p "$NODE_DB_DIR"
  MITHRIL_UID="$(id -u)" MITHRIL_GID="$(id -g)" \
    docker compose --profile quickstart run --rm mithril
fi

exec docker compose up "$@"
