
import streamlit as st
import pandas as pd
import numpy as np
import joblib
import time
from pathlib import Path
from datetime import datetime

st.set_page_config(
    page_title="DrainGuard | Live Monitoring",
    page_icon="🌊",
    layout="wide"
)

MODEL_PATH = Path(__file__).parent / "drain_model.pkl"
DATA_PATH = Path(__file__).parent / "drainage_data.csv"

st.markdown("""
<style>
.stApp {background:#0b1220;color:#f1f5f9}
[data-testid="stMetric"] {
    background:#172338;padding:15px;border-radius:12px;
    border:1px solid #30445f;
}
.zone-card {
    background:#172338;border:1px solid #30445f;
    border-radius:13px;padding:16px;margin-bottom:10px;
}
</style>
""", unsafe_allow_html=True)

st.title("🌊 DrainGuard")
st.caption("LIVE SIMULATED DRAINAGE MONITORING | ML + FOG COMPUTING")
st.markdown("---")

if not MODEL_PATH.exists() or not DATA_PATH.exists():
    st.error("Model or training dataset not found.")
    st.stop()

@st.cache_resource
def load_model():
    return joblib.load(MODEL_PATH)

@st.cache_data
def load_training_data():
    return pd.read_csv(DATA_PATH)

model = load_model()
training_data = load_training_data()

FEATURES = ["water_level", "flow_rate", "rainfall", "pressure"]

if "history" not in st.session_state:
    st.session_state.history = []

if "cycle" not in st.session_state:
    st.session_state.cycle = 0

if "previous_risks" not in st.session_state:
    st.session_state.previous_risks = {}

if "running" not in st.session_state:
    st.session_state.running = True

st.sidebar.title("⚙️ Control Panel")
st.sidebar.success("Random Forest Model: Loaded")
st.sidebar.info("Mode: Synthetic Sensor Simulation")
st.sidebar.write("Drainage Zones: 6")
st.sidebar.write("Fog Gateways: 3")
st.sidebar.write("Cloud Servers: 1")

st.sidebar.markdown("---")
st.sidebar.subheader("Monitoring Controls")

interval = st.sidebar.selectbox(
    "Update interval",
    [10, 20, 30],
    index=0
)

if st.sidebar.button("⏸ Pause Monitoring", use_container_width=True):
    st.session_state.running = False

if st.sidebar.button("▶ Resume Monitoring", use_container_width=True):
    st.session_state.running = True

if st.sidebar.button("🔄 Generate Next Cycle", use_container_width=True):
    st.session_state.manual_cycle = True

if st.sidebar.button("🗑 Clear History", use_container_width=True):
    st.session_state.history = []
    st.session_state.cycle = 0
    st.session_state.previous_risks = {}

# Generate readings using learned ranges from synthetic dataset.
def generate_readings():
    rng = np.random.default_rng()
    rows = []

    for zone in range(1, 7):
        previous = None

        if st.session_state.history:
            old = st.session_state.history[-1]
            previous = old[old["zone"] == f"Zone-{zone}"]

        if previous is not None and not previous.empty:
            old = previous.iloc[0]
            water = old["water_level"] + rng.normal(0, 5)
            flow = old["flow_rate"] + rng.normal(0, 6)
            rain = old["rainfall"] + rng.normal(0, 8)
            pressure = old["pressure"] + rng.normal(0, 4)
        else:
            sample = training_data.sample(
                n=1, random_state=None
            ).iloc[0]
            water = sample["water_level"]
            flow = sample["flow_rate"]
            rain = sample["rainfall"]
            pressure = sample["pressure"]

        rows.append({
            "zone": f"Zone-{zone}",
            "water_level": float(np.clip(water, 5, 100)),
            "flow_rate": float(np.clip(flow, 5, 100)),
            "rainfall": float(np.clip(rain, 0, 150)),
            "pressure": float(np.clip(pressure, 5, 100))
        })

    return pd.DataFrame(rows)

def predict_zones(sensor_df):
    X = sensor_df[FEATURES]
    predictions = model.predict(X)

    probabilities = model.predict_proba(X)
    confidence = probabilities.max(axis=1) * 100

    result = sensor_df.copy()
    result["predicted_risk"] = predictions
    result["confidence"] = confidence.round(1)

    result["fog_node"] = [
        "fog-1", "fog-1", "fog-2",
        "fog-2", "fog-3", "fog-3"
    ]

    result["processing_location"] = result[
        "predicted_risk"
    ].apply(
        lambda risk: "FOG"
        if risk in ["High", "Critical"]
        else "CLOUD"
    )

    return result

# Create a new monitoring cycle.
if st.session_state.running:
    if "last_cycle_time" not in st.session_state:
        st.session_state.last_cycle_time = 0

    now = time.time()
    manual = st.session_state.pop("manual_cycle", False)

    if (
        now - st.session_state.last_cycle_time >= interval
        or manual
        or st.session_state.cycle == 0
    ):
        sensor_df = generate_readings()
        result = predict_zones(sensor_df)

        st.session_state.cycle += 1
        result["cycle"] = st.session_state.cycle
        result["timestamp"] = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        st.session_state.history.append(result.copy())
        st.session_state.history = st.session_state.history[-60:]
        st.session_state.last_cycle_time = now

# Always display the most recent available readings.
if not st.session_state.history:
    st.info("Start monitoring to generate readings.")
    st.stop()

df = st.session_state.history[-1]

total = len(df)
critical = int((df["predicted_risk"] == "Critical").sum())
high = int((df["predicted_risk"] == "High").sum())
moderate = int((df["predicted_risk"] == "Moderate").sum())
normal = int((df["predicted_risk"] == "Normal").sum())
fog_count = int((df["processing_location"] == "FOG").sum())
cloud_count = int((df["processing_location"] == "CLOUD").sum())

st.markdown(
    f"### 🟢 Monitoring Cycle: {st.session_state.cycle}"
)
st.caption(
    f"Last updated: {df['timestamp'].iloc[0]} | "
    f"Update interval: {interval} seconds"
)

if st.session_state.running:
    st.success("LIVE MONITORING ACTIVE")
else:
    st.warning("MONITORING PAUSED")

st.subheader("📊 System Overview")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Zones", total)
c2.metric("Critical", critical)
c3.metric("High Risk", high)
c4.metric("Moderate", moderate)
c5.metric("Normal", normal)

st.markdown("---")
st.subheader("🚨 Live Drainage Alerts")

alerts = df[
    df["predicted_risk"].isin(["Critical", "High"])
]

if alerts.empty:
    st.success("No high-risk zones detected.")
else:
    for _, row in alerts.iterrows():
        st.error(
            f"{row['zone']} | {row['predicted_risk']} | "
            f"Water: {row['water_level']:.1f}% | "
            f"Flow: {row['flow_rate']:.1f} | "
            f"Gateway: {row['fog_node']}"
        )

# --------------------------------------------------
# DRAINGUARD FOG RESPONSE AND CLOUD MONITORING
# --------------------------------------------------

# Initialize maintenance task storage
if "maintenance_tasks" not in st.session_state:
    st.session_state.maintenance_tasks = []

# Create a maintenance task for each new High/Critical prediction
for _, row in df.iterrows():

    if row["predicted_risk"] in ["High", "Critical"]:

        task_id = f"{int(row['cycle'])}-{row['zone']}"

        existing_ids = [
            task["task_id"]
            for task in st.session_state.maintenance_tasks
        ]

        if task_id not in existing_ids:

            action = (
                "Emergency drainage inspection"
                if row["predicted_risk"] == "Critical"
                else "Urgent drainage inspection"
            )

            st.session_state.maintenance_tasks.append({
                "task_id": task_id,
                "zone": row["zone"],
                "risk": row["predicted_risk"],
                "gateway": row["fog_node"],
                "action": action,
                "created": row["timestamp"],
                "status": "Pending"
            })

st.markdown("---")
st.subheader("🚨 Fog Emergency Response Centre")

fog_tasks = [
    task for task in st.session_state.maintenance_tasks
    if task["status"] != "Completed"
]

if fog_tasks:

    for task in reversed(fog_tasks[-12:]):

        color = (
            "🔴" if task["risk"] == "Critical"
            else "🟠"
        )

        st.warning(
            f"{color} {task['zone']} | {task['risk']} RISK | "
            f"Gateway: {task['gateway']} | "
            f"Action: {task['action']}"
        )

else:
    st.success("No pending emergency responses.")

st.markdown("---")
st.subheader("🛠️ Maintenance Task Management")

if not st.session_state.maintenance_tasks:

    st.info("No maintenance tasks generated yet.")

else:

    for task in reversed(st.session_state.maintenance_tasks[-12:]):

        with st.container(border=True):

            st.write(
                f"**{task['zone']} — {task['risk']} Risk**"
            )

            st.caption(
                f"Gateway: {task['gateway']} | "
                f"Action: {task['action']} | "
                f"Created: {task['created']}"
            )

            status = st.selectbox(
                "Task Status",
                ["Pending", "Assigned", "Completed"],
                index=[
                    "Pending", "Assigned", "Completed"
                ].index(task["status"]),
                key=f"status_{task['task_id']}"
            )

            task["status"] = status

            if status == "Completed":
                st.success("Inspection marked as completed.")
            elif status == "Assigned":
                st.info("Maintenance task assigned.")
            else:
                st.warning("Awaiting maintenance assignment.")

st.markdown("---")
st.subheader("☁️ Cloud Monitoring Centre")

history_df = pd.concat(
    st.session_state.history,
    ignore_index=True
)

cloud_history = history_df[
    history_df["processing_location"] == "CLOUD"
].copy()

fog_history = history_df[
    history_df["processing_location"] == "FOG"
].copy()

cloud_col1, cloud_col2, cloud_col3 = st.columns(3)

cloud_col1.metric(
    "Cloud Records",
    len(cloud_history)
)

cloud_col2.metric(
    "Fog Records",
    len(fog_history)
)

cloud_col3.metric(
    "Monitoring Cycles",
    st.session_state.cycle
)

st.write("**Recent Cloud-Processed Readings**")

if not cloud_history.empty:

    st.dataframe(
        cloud_history[
            [
                "timestamp",
                "zone",
                "water_level",
                "flow_rate",
                "predicted_risk",
                "fog_node"
            ]
        ].tail(15),
        use_container_width=True,
        hide_index=True
    )

else:
    st.info("No Cloud-processed records available yet.")

st.markdown("---")
st.subheader("📍 Live Zone Monitoring")

colors = {
    "Critical": "#ef4444",
    "High": "#f97316",
    "Moderate": "#eab308",
    "Normal": "#22c55e"
}

for start in range(0, len(df), 3):
    cols = st.columns(3)

    for col, (_, row) in zip(
        cols, df.iloc[start:start + 3].iterrows()
    ):
        with col:
            color = colors.get(
                row["predicted_risk"], "#94a3b8"
            )

            st.markdown(f"""
            <div class="zone-card">
                <h3>{row['zone']}</h3>
                <h2 style="color:{color}">
                    {row['predicted_risk']}
                </h2>
                <p>💧 Water Level: {row['water_level']:.1f}%</p>
                <p>🌊 Flow Rate: {row['flow_rate']:.1f}</p>
                <p>🌧️ Rainfall: {row['rainfall']:.1f} mm</p>
                <p>⚙️ Pressure: {row['pressure']:.1f}</p>
                <p>🧠 Confidence: {row['confidence']:.1f}%</p>
                <p>📡 Gateway: {row['fog_node']}</p>
                <p>🖥️ Processing: {row['processing_location']}</p>
            </div>
            """, unsafe_allow_html=True)

st.markdown("---")
st.subheader("📈 Historical Monitoring")

history_df = pd.concat(
    st.session_state.history,
    ignore_index=True
)

selected_zone = st.selectbox(
    "Select drainage zone",
    [f"Zone-{i}" for i in range(1, 7)]
)

zone_history = history_df[
    history_df["zone"] == selected_zone
].copy()

st.markdown("#### Water Level History")
st.line_chart(
    zone_history.set_index("cycle")["water_level"]
)

st.markdown("#### Flow Rate History")
st.line_chart(
    zone_history.set_index("cycle")["flow_rate"]
)

st.markdown("---")
st.subheader("☁️ Fog vs Cloud Processing")

a, b, c = st.columns(3)
a.metric("Fog Processed", fog_count)
b.metric("Cloud Processed", cloud_count)
c.metric("Average Simulated Latency", "4.0 units")

st.bar_chart(
    pd.DataFrame({
        "Zones": [fog_count, cloud_count]
    }, index=["Fog", "Cloud"])
)

st.markdown("---")
st.subheader("📋 Latest Sensor Readings")
st.dataframe(df, use_container_width=True, hide_index=True)

st.caption(
    "DrainGuard | Academic Software Prototype | "
    "All sensor readings are synthetically generated. "
    "Fog/cloud assignments and latency are simulated."
)

# Refresh the page automatically to create the next cycle.
if st.session_state.running:
    remaining = max(
        1,
        interval - (time.time() - st.session_state.last_cycle_time)
    )
    time.sleep(remaining)
    st.rerun()
