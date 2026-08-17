#!/bin/sh
set -eu

BASE_URL="${1:-${SMOKE_BASE_URL:-http://127.0.0.1:3000}}"
BODY_FILE="$(mktemp)"

cleanup() {
  rm -f "$BODY_FILE"
}
trap cleanup EXIT

check_status() {
  path="$1"
  expected_status="$2"
  status="$(curl -sS -o "$BODY_FILE" -w "%{http_code}" "$BASE_URL$path")"

  if [ "$status" != "$expected_status" ]; then
    echo "NG $path expected $expected_status, got $status"
    cat "$BODY_FILE"
    exit 1
  fi

  echo "OK $path"
}

check_status "/" "200"
check_status "/login" "200"
check_status "/change-password" "200"
check_status "/forgot-password" "200"
check_status "/reset-password?token=dummy" "200"
check_status "/env.json" "200"

if ! grep -q '"API_URL"' "$BODY_FILE"; then
  echo "NG /env.json does not include API_URL"
  cat "$BODY_FILE"
  exit 1
fi
