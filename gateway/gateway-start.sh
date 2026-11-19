#!/bin/sh
set -e
: "${GATEWAY_USERNAME:?GATEWAY_USERNAME is required}"
: "${GATEWAY_PASSWORD:?GATEWAY_PASSWORD is required}"
: "${UPSTREAM:?UPSTREAM is required (DB-GPT private host:port)}"
GATEWAY_PASSWORD_HASH="$(caddy hash-password --plaintext "$GATEWAY_PASSWORD")"
export GATEWAY_PASSWORD_HASH
unset GATEWAY_PASSWORD
exec caddy run --config /etc/caddy/Caddyfile --adapter caddyfile
