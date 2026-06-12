#!/bin/bash

cd "$(dirname "$0")"

echo "===============================" >> checkin.log
echo "Run at $(date '+%Y-%m-%d %H:%M:%S')" >> checkin.log

source .venv/bin/activate
export PYTHONIOENCODING=utf-8

python daily_checkin.py >> checkin.log 2>&1

echo "Finished at $(date '+%Y-%m-%d %H:%M:%S')" >> checkin.log
echo "" >> checkin.log
