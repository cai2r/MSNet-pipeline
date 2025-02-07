#!/usr/bin/env bash
set -Eeo pipefail

echo "-- Starting module..."
#ls /src/models/msnet/model19_prepost4s/

cp -r $MERCURE_IN_DIR/* data/1-input/
conda run -n glioma-seg-37 python3 -m src.run_pipeline \
cp -rp data/6-output/* $MERCURE_OUT_DIR/

echo "-- Done."
