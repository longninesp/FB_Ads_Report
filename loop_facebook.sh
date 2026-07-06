#!/usr/bin/env bash
set -u

for day in {1..31}; do
  date_str=$(printf "2026-07-%02d" "$day")
  echo "Running for date: $date_str"
  python3 fetch_facebook.py "$date_str"
done
