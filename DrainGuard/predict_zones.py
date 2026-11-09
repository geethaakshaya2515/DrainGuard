import pandas as pd
import pickle
import os

CSV_FILE = "sensor_inputs.csv"
MODEL_FILE = "drain_model.pkl"
OUTPUT_FILE = "ml_predictions.csv"

# ---------------------------------------------------------
# Load trained Random Forest
# ---------------------------------------------------------

with open(MODEL_FILE, "rb") as file:
    model = pickle.load(file)

# ---------------------------------------------------------
# Read actual iFogSim sensor readings
# ---------------------------------------------------------

if not os.path.exists(CSV_FILE):
    raise FileNotFoundError(
        "sensor_inputs.csv not found."
    )

data = pd.read_csv(CSV_FILE)

if len(data) < 6:
    raise ValueError(
        "Waiting for all 6 iFogSim sensor readings."
    )

# ---------------------------------------------------------
# Get latest simulation cycle
# ---------------------------------------------------------

latest_time = data["simulation_time"].max()

latest = data[
    data["simulation_time"] == latest_time
].copy()

# Safety: use latest six readings
latest = latest.tail(6)

if len(latest) < 6:
    raise ValueError(
        "Latest simulation cycle does not contain 6 zones."
    )

# ---------------------------------------------------------
# Random Forest prediction
# ---------------------------------------------------------

features = latest[
    [
        "water_level",
        "flow_rate",
        "rainfall",
        "pressure"
    ]
].to_numpy()

latest["predicted_risk"] = model.predict(features)

latest["confidence"] = (
    model.predict_proba(features)
    .max(axis=1) * 100
).round(2)

# ---------------------------------------------------------
# Fog gateway mapping
# ---------------------------------------------------------

latest["fog_node"] = latest["zone"].map({

    "Zone-1": "fog-1",
    "Zone-2": "fog-1",

    "Zone-3": "fog-2",
    "Zone-4": "fog-2",

    "Zone-5": "fog-3",
    "Zone-6": "fog-3"
})

# ---------------------------------------------------------
# Fog / Cloud decision
# ---------------------------------------------------------

latest["processing_location"] = latest[
    "predicted_risk"
].apply(
    lambda risk:
        "FOG"
        if risk in ["High", "Critical"]
        else "CLOUD"
)

# ---------------------------------------------------------
# Save latest predictions
# ---------------------------------------------------------

latest.to_csv(
    OUTPUT_FILE,
    index=False
)

# ---------------------------------------------------------
# Console output
# ---------------------------------------------------------

print("\n===== RANDOM FOREST PREDICTIONS =====")

for _, row in latest.iterrows():

    print(
        f"{row['zone']} | "
        f"Water={row['water_level']:.2f} | "
        f"Flow={row['flow_rate']:.2f} | "
        f"Rain={row['rainfall']:.2f} | "
        f"Pressure={row['pressure']:.2f} | "
        f"Risk={row['predicted_risk']} | "
        f"Confidence={row['confidence']:.2f}% | "
        f"{row['processing_location']}"
    )

print(
    "\nML predictions saved to "
    "ml_predictions.csv"
)