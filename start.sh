#!/bin/bash

cd /app

# Fresh deployment starts from Cycle 1
rm -f DrainGuard/sensor_inputs.csv
rm -f DrainGuard/ml_predictions.csv

echo "=============================================="
echo "        DRAINGUARD STARTING"
echo "=============================================="
echo "Starting iFogSim IoT + Fog + ML simulation..."

java \
  -cp "bin:jars/*:jars/commons-math3-3.5/commons-math3-3.5.jar" \
  org.fog.test.perfeval.DrainGuardFogApp \
  > /tmp/ifogsim.log 2>&1 &

echo "iFogSim started."

echo "Starting Streamlit dashboard..."

exec streamlit run \
  DrainGuard/app_combined_iFogSim.py \
  --server.address 0.0.0.0 \
  --server.port "${PORT:-8501}"
