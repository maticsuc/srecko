#!/usr/bin/env bash
#
# Deploy Srecko to Hetzner.
#
# Usage:
#   ./deploy-hetzner.sh
#
# Optional overrides:
#   DEPLOY_HOST=root@hetzner DEPLOY_DIR=/root/srecko ./deploy-hetzner.sh

set -euo pipefail

DEPLOY_HOST="${DEPLOY_HOST:-root@hetzner}"
DEPLOY_DIR="${DEPLOY_DIR:-/root/srecko}"

log() {
    printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

run_remote() {
    log "Connecting to $DEPLOY_HOST"

    ssh "$DEPLOY_HOST" "DEPLOY_DIR='$DEPLOY_DIR' bash -s" <<'REMOTE_SCRIPT'
set -euo pipefail

log() {
    printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

run_step() {
    log "START: $*"
    "$@"
    log "DONE:  $*"
}

log "Deploying from $(hostname) in $DEPLOY_DIR"
cd "$DEPLOY_DIR"

run_step git pull
run_step docker compose down
run_step docker compose up -d --build

log "Current containers:"
docker compose ps

log "Deployment finished successfully"
REMOTE_SCRIPT
}

log "Starting Hetzner deploy"
run_remote
log "Hetzner deploy complete"
