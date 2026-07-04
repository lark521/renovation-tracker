#!/bin/bash
# Start renovation tracker if not running
APP_DIR="/home/shaohua/renovation-tracker"
VENV_PYTHON="/home/shaohua/.hermes/hermes-agent/venv/bin/python3"
LOG_FILE="$APP_DIR/server.log"
PID_FILE="$APP_DIR/.server.pid"

if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        exit 0
    fi
fi

cd "$APP_DIR"
$VENV_PYTHON app.py > "$LOG_FILE" 2>&1 &
echo $! > "$PID_FILE"
