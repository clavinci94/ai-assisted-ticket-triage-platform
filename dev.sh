#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_HOST="${FRONTEND_HOST:-127.0.0.1}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

if [[ ! -x "${ROOT_DIR}/.venv/bin/python" ]]; then
  echo "Missing virtualenv interpreter at .venv/bin/python"
  echo "Create it with: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

if [[ ! -d "${ROOT_DIR}/frontend/node_modules" ]]; then
  echo "Missing frontend dependencies in frontend/node_modules"
  echo "Install them with: cd frontend && npm install"
  exit 1
fi

backend_pid=""
frontend_pid=""

cleanup() {
  trap - EXIT INT TERM

  if [[ -n "${backend_pid}" ]] && kill -0 "${backend_pid}" 2>/dev/null; then
    kill "${backend_pid}" 2>/dev/null || true
  fi

  if [[ -n "${frontend_pid}" ]] && kill -0 "${frontend_pid}" 2>/dev/null; then
    kill "${frontend_pid}" 2>/dev/null || true
  fi

  wait "${backend_pid}" 2>/dev/null || true
  wait "${frontend_pid}" 2>/dev/null || true
}

trap cleanup EXIT INT TERM

echo "Starting backend on http://${BACKEND_HOST}:${BACKEND_PORT}"
"${ROOT_DIR}/.venv/bin/python" -m uvicorn app.main:app --reload --host "${BACKEND_HOST}" --port "${BACKEND_PORT}" &
backend_pid=$!

echo "Starting frontend from ${ROOT_DIR}/frontend on http://${FRONTEND_HOST}:${FRONTEND_PORT}"
(
  cd "${ROOT_DIR}/frontend"
  npm run dev -- --host "${FRONTEND_HOST}" --port "${FRONTEND_PORT}"
) &
frontend_pid=$!

while true; do
  if ! kill -0 "${backend_pid}" 2>/dev/null; then
    wait "${backend_pid}"
    exit $?
  fi

  if ! kill -0 "${frontend_pid}" 2>/dev/null; then
    wait "${frontend_pid}"
    exit $?
  fi

  sleep 1
done
