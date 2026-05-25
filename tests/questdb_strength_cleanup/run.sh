#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TESTS_DIR="${REPO_ROOT}/tests"
PROJECT_NAME="garmin-qdb-strength-cleanup"
COMPOSE_FILE="${TESTS_DIR}/compose.yml"
QUESTDB_HTTP_URL="http://127.0.0.1:19001"

cleanup() {
  docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" down -v --remove-orphans >/dev/null 2>&1 || true
}
trap cleanup EXIT

docker compose -p "${PROJECT_NAME}" -f "${COMPOSE_FILE}" up -d --quiet-pull

for _ in {1..60}; do
  if curl -fsS "${QUESTDB_HTTP_URL}/exec?query=select%201" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

curl -fsS "${QUESTDB_HTTP_URL}/exec?query=select%201" >/dev/null

cd "${REPO_ROOT}"
INFLUXDB_HOST=127.0.0.1 \
INFLUXDB_PORT=19001 \
INFLUXDB_ENDPOINT_IS_HTTP=True \
INFLUXDB_DATABASE=GarminStats \
PYTHONPATH=src \
uv run python "${SCRIPT_DIR}/questdb_strength_cleanup_test.py"
