#!/usr/bin/env bash
set -Eeuo pipefail

# Deploy Mayan EDMS on Ubuntu using Docker Compose.
# Default public port is 4444; override with: MAYAN_HTTP_PORT=8080 ./deploy.sh

APP_PORT="${MAYAN_HTTP_PORT:-4444}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_DIR="${SCRIPT_DIR}/docker"
COMPOSE_FILE="${COMPOSE_DIR}/docker-compose.yml"
ENV_FILE="${COMPOSE_DIR}/.env"
BACKUP_FILE="${COMPOSE_FILE}.bak"

log() {
  printf '\n\033[1;34m==> %s\033[0m\n' "$*"
}

fail() {
  printf '\n\033[1;31mERROR: %s\033[0m\n' "$*" >&2
  exit 1
}

if [[ ! "${APP_PORT}" =~ ^[0-9]+$ ]] || (( APP_PORT < 1 || APP_PORT > 65535 )); then
  fail "MAYAN_HTTP_PORT must be a valid TCP port number. Got: ${APP_PORT}"
fi

[[ -f "${COMPOSE_FILE}" ]] || fail "Cannot find ${COMPOSE_FILE}"

log "Checking Docker"
if ! command -v docker >/dev/null 2>&1; then
  fail "Docker is not installed. Install Docker first, then run this script again."
fi

if ! docker compose version >/dev/null 2>&1; then
  fail "Docker Compose plugin is not available. Install docker-compose-plugin, then run this script again."
fi

log "Preparing ${ENV_FILE}"
if [[ ! -f "${ENV_FILE}" ]]; then
  cat > "${ENV_FILE}" <<'ENVEOF'
MAYAN_DOCKER_IMAGE_NAME=mayanedms/mayanedms
MAYAN_DOCKER_IMAGE_TAG=s4.3

MAYAN_DATABASE_NAME=mayan
MAYAN_DATABASE_USER=mayan
MAYAN_DATABASE_PASSWORD=change_this_db_password

MAYAN_RABBITMQ_USER=mayan
MAYAN_RABBITMQ_PASSWORD=change_this_rabbitmq_password
MAYAN_RABBITMQ_VHOST=mayan

MAYAN_REDIS_PASSWORD=change_this_redis_password
ENVEOF
  chmod 600 "${ENV_FILE}"
  log "Created ${ENV_FILE}. Edit it later to use stronger production passwords."
else
  log "Using existing ${ENV_FILE}"
fi

log "Configuring Mayan HTTP port ${APP_PORT}"
if [[ ! -f "${BACKUP_FILE}" ]]; then
  cp "${COMPOSE_FILE}" "${BACKUP_FILE}"
fi

python3 - "${COMPOSE_FILE}" "${APP_PORT}" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
port = sys.argv[2]
text = path.read_text()
old = '      - "80:8000"'
new = f'      - "{port}:8000"'
if new in text:
    print(f"Port mapping already set to {port}:8000")
elif old in text:
    text = text.replace(old, new, 1)
    path.write_text(text)
    print(f"Updated first Mayan app port mapping to {port}:8000")
else:
    raise SystemExit('Could not find app port mapping "80:8000" in docker-compose.yml')
PY

log "Opening firewall port ${APP_PORT} if UFW is active"
if command -v ufw >/dev/null 2>&1; then
  if sudo ufw status | grep -q "Status: active"; then
    sudo ufw allow "${APP_PORT}/tcp"
  else
    log "UFW is installed but inactive; skipping firewall update"
  fi
else
  log "UFW is not installed; skipping firewall update"
fi

log "Pulling Docker images"
cd "${COMPOSE_DIR}"
docker compose --profile all_in_one --profile postgresql --profile redis --profile rabbitmq pull

log "Running Mayan setup/upgrade task"
docker compose --profile postgresql --profile redis --profile rabbitmq --profile extra_setup_or_upgrade run --rm setup_or_upgrade

log "Starting Mayan EDMS"
docker compose --profile all_in_one --profile postgresql --profile redis --profile rabbitmq up -d

log "Deployment complete"
docker compose ps
printf '\nMayan EDMS should be available at: http://<server-ip>:%s\n' "${APP_PORT}"
