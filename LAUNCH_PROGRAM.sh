#!/bin/bash

# Get script directory and set up logging
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$SCRIPT_DIR/Files"
LOGDIR="$APP_DIR/logs"
mkdir -p "$LOGDIR"
LOGFILE="$LOGDIR/launch_$(date +%Y%m%d_%H%M%S).log"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOGFILE"
}

# Check for test mode first
if [ "$1" = "--test" ]; then
    log "Test mode - skipping execution"
    exit 0
fi

# Change to app directory
if ! cd "$APP_DIR"; then
    log "ERROR: Failed to change to application directory"
    exit 1
fi

# Ensure start script is executable
if ! chmod +x "./start_notebook.sh"; then
    log "ERROR: Failed to make start_notebook.sh executable"
    exit 1
fi

# Launch the start_notebook.sh script
log "Starting notebook..."
exec "./start_notebook.sh"
