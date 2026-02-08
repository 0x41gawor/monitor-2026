#!/usr/bin/env bash

START_DATE="2025-09-12"
END_DATE="2025-09-21"

current="$START_DATE"

while [[ "$current" <="$END_DATE" ]]; do
  echo "Running job for $current"
  python3 job.py --date "$current"

  # next day
  current=$(date -I -d "$current + 1 day")
  sleep 15
done
