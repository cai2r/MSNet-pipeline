#!/usr/bin/env bash
set -Eeo pipefail
export PYTHONUNBUFFERED=1

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') -- $1"
}

error_exit() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') -- ERROR: $1" >&2
    exit 1
}

log "Starting module..."

# Validate input directory
if [ ! -d "$MERCURE_IN_DIR" ]; then
    error_exit "Input directory '$MERCURE_IN_DIR' does not exist."
fi

# Copy input data
log "Copying input data..."
cp -r "$MERCURE_IN_DIR"/* /data/1-input/ || error_exit "Failed to copy input data."

# Run the Python pipeline
log "Running Python pipeline..."
conda run -n glioma-seg-37 python3 -m src.run_pipeline || error_exit "Pipeline execution failed."

# Prepare output directory
mkdir -p "$MERCURE_OUT_DIR" || error_exit "Failed to create output directory '$MERCURE_OUT_DIR'."

# Copy output data
if [ "$(ls -A /data/6-output/ 2>/dev/null)" ]; then
    log "Copying output data..."
    cp -rp /data/6-output/* "$MERCURE_OUT_DIR"/ || error_exit "Failed to copy output data."
else
    log "Warning: No output files found in /data/6-output."
fi

log "Done."
