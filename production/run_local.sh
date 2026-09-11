#!/bin/bash
# SIGNIT local Mac launcher — venv + staged deps + GUI (see RUN_MAC.md).
# Usage: ./run_local.sh [--no-splash] [--history-db PATH]
set -e
cd "$(dirname "$0")"

if [ ! -x .venv/bin/python ]; then
  uv python install 3.10
  uv venv --python 3.10 .venv
fi
.venv/bin/python -m ensurepip >/dev/null 2>&1 || true
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install "numpy==1.26.4" "scipy==1.13.1" "scikit-learn==1.5.1"
.venv/bin/python -m pip install --no-build-isolation "pyldpc==0.7.7"
.venv/bin/python -m pip install -r requirements.txt

HISTDB="/tmp/signit.db"
ARGS=()
EXPECT_DB=0
SEEN_DB=0
for a in "$@"; do
  if [ "$EXPECT_DB" = 1 ]; then HISTDB="$a"; EXPECT_DB=0; SEEN_DB=1; continue; fi
  case "$a" in
    --history-db=*) HISTDB="${a#--history-db=}"; SEEN_DB=1 ;;
    --history-db) EXPECT_DB=1 ;;
    *) ARGS+=("$a") ;;
  esac
done

exec .venv/bin/python -m app.main --history-db "$HISTDB" "${ARGS[@]}"
