#!/usr/bin/env bash
set -Eeo pipefail
echo "-- Starting module..."
ls /models/msnet/model19_prepost4s/

cp -r $MERCURE_IN_DIR/* data/1-input/

python3 -m src.run_pipeline \

cp -r data/6-output/* $MERCURE_OUT_DIR/

echo "-- Done."
