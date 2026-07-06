#!/usr/bin/env bash
set -u

BASE_DIR="/home/weina/FB_Ads_Report"
PYTHON_BIN="/usr/bin/python3"

cd "$BASE_DIR" || exit 1

run_one() {
  local dt="$1"
  echo "Running fetch_facebook.py for date: $dt"
  if ! $PYTHON_BIN fetch_facebook.py "$dt"; then
    echo "[ERROR] fetch_facebook.py failed for $dt"
  fi
}

for offset in 1 2 3 4; do
  dt=$(date -d "$offset days ago" +%F)
  run_one "$dt"
done

echo "Done."
