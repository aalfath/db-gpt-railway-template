#!/bin/sh
# Start script for DB-GPT on Railway. Keeps every piece of state on the volume at /data.
set -e

: "${OPENAI_API_KEY:?OPENAI_API_KEY is required: set it on the DB-GPT service (any OpenAI compatible key)}"
: "${DBGPT_ENCRYPT_KEY:?DBGPT_ENCRYPT_KEY is required}"
: "${MYSQL_HOST:?MYSQL_HOST is required (reference the MySQL service)}"
: "${MYSQL_PASSWORD:?MYSQL_PASSWORD is required (reference the MySQL service)}"

# Embeddings use the chat key unless a separate one is set.
export EMBEDDING_MODEL_API_KEY="${EMBEDDING_MODEL_API_KEY:-$OPENAI_API_KEY}"

DATA="${DBGPT_DATA_DIR:-/data}"
mkdir -p "$DATA/pilot/data" "$DATA/pilot/tmp" "$DATA/pilot/message" "$DATA/skills-user" "$DATA/home"

# Move a directory of the image onto the volume, keeping anything already there.
link_dir() { # <path in image> <path on volume>
  if [ ! -L "$1" ]; then
    if [ -d "$1" ]; then cp -an "$1/." "$2/" 2>/dev/null || true; rm -r "$1"; fi
    mkdir -p "$(dirname "$1")"
    ln -s "$2" "$1"
  fi
}
link_dir /app/pilot/data "$DATA/pilot/data"         # Chroma vectors, uploaded files, Excel/DuckDB work files
link_dir /app/pilot/tmp "$DATA/pilot/tmp"           # agent work dirs and uploads
link_dir /app/pilot/message "$DATA/pilot/message"   # generated chart images
link_dir /app/skills/user "$DATA/skills-user"       # skills you upload or create
# Agent workspace (~/.dbgpt) and the file service cache (~/.cache/dbgpt) live under HOME.
export HOME="$DATA/home"

python /railway/railway_db_init.py

exec dbgpt start webserver --config /app/configs/dbgpt-railway.toml
