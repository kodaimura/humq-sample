#!/bin/sh
set -eu

APP_API_URL="${APP_API_URL:-/api}"
ESCAPED_API_URL="$(printf '%s' "$APP_API_URL" | sed 's/\\/\\\\/g; s/"/\\"/g')"

cat > /usr/share/nginx/html/env.json <<EOF
{
  "API_URL": "$ESCAPED_API_URL"
}
EOF
