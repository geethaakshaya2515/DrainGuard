import streamlit as st
import pandas as pd
import numpy as np
import joblib
import time
from pathlib import Path
from datetime import datetime

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------
st.set_page_config(
    page_title="DrainGuard | Smart Drainage Monitoring",
    page_icon="🌊",
    layout="wide"
)

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "drain_model.pkl"
DATA_PATH = BASE_DIR / "drainage_data.csv"
PREDICTIONS_PATH = BASE_DIR / "ml_predictions.csv"

FEATURES = ["water_level", "flow_rate", "rainfall", "pressure"]

# --------------------------------------------------
# SHARED STYLING
# --------------------------------------------------
st.markdown("""
<style>
.stApp {
    background: #0b1220;
    color: #f1f5f9;
}
[data-testid="stMetric"] {
    background: #172338;
    padding: 16px;
    border-radius: 12px;
    border: 1px solid #30445f;
}
.zone-card {
    background: #172338;
    border: 1px solid #30445f;
    border-radius: 14px;
    padding: 16px;
    margin-bottom: 12px;
}
div[data-testid="stSidebar"] {
    background: #101b2d;
}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# SHARED HEADER AND NAVIGATION
# --------------------------------------------------
st.title("🌊 DrainGuard")
st.caption("ML-DRIVEN URBAN DRAINAGE BLOCKAGE PREDICTION & EARLY WARNING SYSTEM")

st.sidebar.title("🌊 DrainGuard")
st.sidebar.caption("Navigation")
page = st.sidebar.radio(
    "Go to",
    ["Overview & Analytics", "Live Monitoring", "Alerts & Maintenance", "Fog & Cloud"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.subheader("System Configuration")
st.sidebar.write("**Drainage zones:** 6")
st.sidebar.write("**Fog gateways:** 3")
st.sidebar.write("**Cloud servers:** 1")
st.sidebar.info("Academic software prototype • Synthetic sensor data")

# --------------------------------------------------
# SHARED DATA / MODEL LOADERS
# --------------------------------------------------
@st.cache_resource
def load_model():
    return joblib.load(MODEL_PATH)

@st.cache_data
def load_training_data():
    return pd.read_csv(DATA_PATH)

@st.cache_data
def load_static_predictions():
    return pd.read_csv(PREDICTIONS_PATH)

def risk_color(risk):
    return {
        "Critical": "#ef4444",
        "High": "#f97316",
        "Moderate": "#eab308",
        "Normal": "#22c55e"
    }.get(risk, "#94a3b8")

# ==================================================
# PAGE 1: OVERVIEW & ANALYTICS (ORIGINAL app.py)
# ==================================================
if page == "Overview & Analytics":
    st.header("System Overview")
    st.caption("Prepared ML predictions from the latest prediction file.")

    if not PREDICTIONS_PATH.exists():
        st.error("ml_predictions.csv not found. Run predict_zones.py first.")
        st.stop()

    df = load_static_predictions()

    required = {
        "zone", "water_level", "flow_rate", "rainfall", "pressure",
        "predicted_risk", "confidence", "fog_node", "processing_location"
    }
    missing = required.difference(df.columns)
    if missing:
        st.error("The prediction file is missing required columns: " + ", ".join(sorted(missing)))
        st.stop()

    total = len(df)
    counts = df["predicted_risk"].value_counts()
    critical = int(counts.get("Critical", 0))
    high = int(counts.get("High", 0))
    moderate = int(counts.get("Moderate", 0))
    normal = int(counts.get("Normal", 0))
    fog_count = int((df["processing_location"] == "FOG").sum())
    cloud_count = int((df["processing_location"] == "CLOUD").sum())

    if st.button("🔄 Refresh prepared predictions"):
        load_static_predictions.clear()
        st.rerun()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Zones", total)
    c2.metric("Critical", critical)
    c3.metric("High Risk", high)
    c4.metric("Moderate", moderate)
    c5.metric("Normal", normal)

    st.markdown("---")
    st.subheader("🚨 Drainage Risk Alerts")
    alerts = df[df["predicted_risk"].isin(["Critical", "High"])]

    if alerts.empty:
        st.success("No elevated-risk zones detected in the prepared predictions.")
    else:
        for _, row in alerts.iterrows():
            st.error(
                f"{row['zone']} — {row['predicted_risk']} risk | "
                f"Gateway: {row['fog_node']} | Confidence: {row['confidence']}%"
            )

    st.markdown("---")
    st.subheader("📍 Zone Status")
    for start in range(0, len(df), 3):
        cols = st.columns(3)
        for col, (_, row) in zip(cols, df.iloc[start:start + 3].iterrows()):
            with col:
                color = risk_color(row["predicted_risk"])
                st.markdown(f"""
                <div class="zone-card">
                    <h3>{row['zone']}</h3>
                    <h2 style="color:{color}">{row['predicted_risk']}</h2>
                    <p>💧 Water Level: {row['water_level']}%</p>
                    <p>🌧️ Rainfall: {row['rainfall']} mm (synthetic)</p>
                    <p>🌊 Flow Rate: {row['flow_rate']}</p>
                    <p>⚙️ Pressure: {row['pressure']}</p>
                    <p>🧠 ML Confidence: {row['confidence']}%</p>
                    <p>📡 Gateway: {row['fog_node']}</p>
                    <p>🖥️ Processing: {row['processing_location']}</p>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("📊 Analytics")
    left, right = st.columns(2)
    with left:
        st.markdown("#### Risk Distribution")
        risk_order = ["Critical", "High", "Moderate", "Normal"]
        risk_counts = pd.Series(
            {risk: int((df["predicted_risk"] == risk).sum()) for risk in risk_order},
            name="Zones"
        ).to_frame()
        st.bar_chart(risk_counts)
    with right:
        st.markdown("#### Fog vs Cloud Processing")
        processing = pd.DataFrame(
            {"Zones": [fog_count, cloud_count]},
            index=["Fog", "Cloud"]
        )
        st.bar_chart(processing)

    st.markdown("---")
    st.subheader("📋 Prepared Sensor and ML Data")
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.caption(
        "This page displays prepared predictions from ml_predictions.csv. "
        "Readings are synthetic and processing allocation is simulated."
    )

# ==================================================
# PAGE 2: LIVE MONITORING (app_live.py)
# ==================================================
elif page == "Live Monitoring":
    if not MODEL_PATH.exists() or not DATA_PATH.exists():
        st.error("drain_model.pkl or drainage_data.csv not found in the application folder.")
        st.stop()

    model = load_model()
    training_data = load_training_data()

    if "dg_history" not in st.session_state:
        st.session_state.dg_history = []
    if "dg_cycle" not in st.session_state:
        st.session_state.dg_cycle = 0
    if "dg_running" not in st.session_state:
        st.session_state.dg_running = True
    if "dg_maintenance_tasks" not in st.session_state:
        st.session_state.dg_maintenance_tasks = []
    if "dg_last_cycle_time" not in st.session_state:
        st.session_state.dg_last_cycle_time = 0.0

    st.sidebar.markdown("---")
    st.sidebar.subheader("Live Monitoring Controls")
    interval = st.sidebar.selectbox(
        "Update interval (seconds)", [10, 20, 30], index=0, key="dg_interval"
    )

    control1, control2 = st.sidebar.columns(2)
    if control1.button("⏸ Pause", use_container_width=True, key="dg_pause"):
        st.session_state.dg_running = False
    if control2.button("▶ Resume", use_container_width=True, key="dg_resume"):
        st.session_state.dg_running = True
    if st.sidebar.button("🔄 Generate Next Cycle", use_container_width=True, key="dg_manual"):
        st.session_state.dg_manual_cycle = True
    if st.sidebar.button("🗑 Clear Live History", use_container_width=True, key="dg_clear"):
        st.session_state.dg_history = []
        st.session_state.dg_cycle = 0
        st.session_state.dg_maintenance_tasks = []
        st.session_state.dg_last_cycle_time = 0.0
        st.rerun()

    def generate_readings():
        rng = np.random.default_rng()
        rows = []
        for zone in range(1, 7):
            previous = None
            if st.session_state.dg_history:
                old_df = st.session_state.dg_history[-1]
                previous = old_df[old_df["zone"] == f"Zone-{zone}"]

            if previous is not None and not previous.empty:
                old = previous.iloc[0]
                water = old["water_level"] + rng.normal(0, 5)
                flow = old["flow_rate"] + rng.normal(0, 6)
                rain = old["rainfall"] + rng.normal(0, 8)
                pressure = old["pressure"] + rng.normal(0, 4)
            else:
                sample = training_data.sample(n=1).iloc[0]
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

    def predict_live_zones(sensor_df):
        predictions = model.predict(sensor_df[FEATURES])
        probabilities = model.predict_proba(sensor_df[FEATURES])
        result = sensor_df.copy()
        result["predicted_risk"] = predictions
        result["confidence"] = (probabilities.max(axis=1) * 100).round(1)
        result["fog_node"] = [
            "fog-1", "fog-1", "fog-2", "fog-2", "fog-3", "fog-3"
        ]
        result["processing_location"] = result["predicted_risk"].apply(
            lambda risk: "FOG" if risk in ["High", "Critical"] else "CLOUD"
        )
        return result

    manual = st.session_state.pop("dg_manual_cycle", False)
    now = time.time()
    should_generate = (
        st.session_state.dg_running
        and (
            now - st.session_state.dg_last_cycle_time >= interval
            or manual
            or st.session_state.dg_cycle == 0
        )
    )

    if should_generate:
        result = predict_live_zones(generate_readings())
        st.session_state.dg_cycle += 1
        result["cycle"] = st.session_state.dg_cycle
        result["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.dg_history.append(result.copy())
        st.session_state.dg_history = st.session_state.dg_history[-60:]
        st.session_state.dg_last_cycle_time = now

        for _, row in result.iterrows():
            if row["predicted_risk"] in ["High", "Critical"]:
                task_id = f"{int(row['cycle'])}-{row['zone']}"
                known_ids = {task["task_id"] for task in st.session_state.dg_maintenance_tasks}
                if task_id not in known_ids:
                    action = (
                        "Emergency drainage inspection"
                        if row["predicted_risk"] == "Critical"
                        else "Urgent drainage inspection"
                    )
                    st.session_state.dg_maintenance_tasks.append({
                        "task_id": task_id,
                        "zone": row["zone"],
                        "risk": row["predicted_risk"],
                        "gateway": row["fog_node"],
                        "action": action,
                        "created": row["timestamp"],
                        "status": "Pending"
                    })

    if not st.session_state.dg_history:
        st.info("Monitoring is ready. Resume monitoring or generate the next cycle.")
        st.stop()

    df = st.session_state.dg_history[-1]
    counts = df["predicted_risk"].value_counts()
    critical = int(counts.get("Critical", 0))
    high = int(counts.get("High", 0))
    moderate = int(counts.get("Moderate", 0))
    normal = int(counts.get("Normal", 0))
    fog_count = int((df["processing_location"] == "FOG").sum())
    cloud_count = int((df["processing_location"] == "CLOUD").sum())

    st.header("Live Simulated Monitoring")
    st.caption(
        f"Cycle {st.session_state.dg_cycle} • Last updated: {df['timestamp'].iloc[0]} "
        f"• Refresh interval: {interval} seconds"
    )
    if st.session_state.dg_running:
        st.success("🟢 LIVE SIMULATION ACTIVE")
    else:
        st.warning("⏸ MONITORING PAUSED")

    metric_cols = st.columns(5)
    metric_cols[0].metric("Total Zones", len(df))
    metric_cols[1].metric("Critical", critical)
    metric_cols[2].metric("High Risk", high)
    metric_cols[3].metric("Moderate", moderate)
    metric_cols[4].metric("Normal", normal)

    st.markdown("---")
    st.subheader("📍 Live Zone Monitoring")
    for start in range(0, len(df), 3):
        cols = st.columns(3)
        for col, (_, row) in zip(cols, df.iloc[start:start + 3].iterrows()):
            with col:
                color = risk_color(row["predicted_risk"])
                st.markdown(f"""
                <div class="zone-card">
                    <h3>{row['zone']}</h3>
                    <h2 style="color:{color}">{row['predicted_risk']}</h2>
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
    st.subheader("🚨 Current Live Alerts")
    alerts = df[df["predicted_risk"].isin(["Critical", "High"])]
    if alerts.empty:
        st.success("No High or Critical zones detected in this cycle.")
    else:
        for _, row in alerts.iterrows():
            st.error(
                f"{row['zone']} | {row['predicted_risk']} risk | "
                f"Water: {row['water_level']:.1f}% | "
                f"Flow: {row['flow_rate']:.1f} | Gateway: {row['fog_node']}"
            )

    st.markdown("---")
    st.subheader("📈 Live History")
    history_df = pd.concat(st.session_state.dg_history, ignore_index=True)
    selected_zone = st.selectbox(
        "Select drainage zone",
        [f"Zone-{i}" for i in range(1, 7)],
        key="dg_selected_zone"
    )
    zone_history = history_df[history_df["zone"] == selected_zone]
    chart1, chart2 = st.columns(2)
    with chart1:
        st.markdown("#### Water Level")
        st.line_chart(zone_history.set_index("cycle")["water_level"])
    with chart2:
        st.markdown("#### Flow Rate")
        st.line_chart(zone_history.set_index("cycle")["flow_rate"])

    st.markdown("---")
    st.subheader("📋 Latest Simulated Sensor Readings")
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.caption(
        "All live readings are synthetically generated. The trained Random Forest "
        "model classifies these simulated readings. Fog/cloud allocation and alerts "
        "are software demonstrations, not physical sensor or actuator operations."
    )

    if st.session_state.dg_running:
        remaining = max(
            1.0, interval - (time.time() - st.session_state.dg_last_cycle_time)
        )
        time.sleep(remaining)
        st.rerun()

# ==================================================
# PAGE 3: ALERTS & MAINTENANCE
# ==================================================
elif page == "Alerts & Maintenance":
    st.header("🚨 Alerts & Maintenance Management")
    st.caption("Maintenance tasks are generated by the live simulation.")

    tasks = st.session_state.get("dg_maintenance_tasks", [])
    if not tasks:
        st.info("No live maintenance tasks are available yet. Open Live Monitoring and generate a cycle.")
    else:
        pending = sum(task["status"] == "Pending" for task in tasks)
        assigned = sum(task["status"] == "Assigned" for task in tasks)
        completed = sum(task["status"] == "Completed" for task in tasks)
        c1, c2, c3 = st.columns(3)
        c1.metric("Pending", pending)
        c2.metric("Assigned", assigned)
        c3.metric("Completed", completed)

        st.markdown("---")
        for task in reversed(tasks[-30:]):
            with st.container(border=True):
                st.markdown(f"**{task['zone']} — {task['risk']} Risk**")
                st.write(
                    f"Gateway: {task['gateway']} | Action: {task['action']} | "
                    f"Created: {task['created']}"
                )
                status_options = ["Pending", "Assigned", "Completed"]
                current_index = status_options.index(task["status"])
                new_status = st.selectbox(
                    "Task status",
                    status_options,
                    index=current_index,
                    key=f"dg_task_status_{task['task_id']}"
                )
                task["status"] = new_status

# ==================================================
# PAGE 4: FOG & CLOUD
# ==================================================
elif page == "Fog & Cloud":
    st.header("☁️ Fog & Cloud Processing")
    st.caption("Logical processing allocation used by the DrainGuard software prototype.")

    live_history = st.session_state.get("dg_history", [])
    if live_history:
        history_df = pd.concat(live_history, ignore_index=True)
        cloud_history = history_df[history_df["processing_location"] == "CLOUD"]
        fog_history = history_df[history_df["processing_location"] == "FOG"]
        latest = live_history[-1]
        fog_now = int((latest["processing_location"] == "FOG").sum())
        cloud_now = int((latest["processing_location"] == "CLOUD").sum())

        c1, c2, c3 = st.columns(3)
        c1.metric("Fog Records (history)", len(fog_history))
        c2.metric("Cloud Records (history)", len(cloud_history))
        c3.metric("Live Cycles", len(live_history))

        st.markdown("---")
        st.subheader("Latest Cycle Allocation")
        a, b = st.columns(2)
        a.metric("Fog-processed zones", fog_now)
        b.metric("Cloud-processed zones", cloud_now)

        st.subheader("Recent Cloud-Processed Readings")
        if not cloud_history.empty:
            st.dataframe(
                cloud_history[
                    ["timestamp", "zone", "water_level", "flow_rate",
                     "predicted_risk", "fog_node"]
                ].tail(20),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No Cloud-processed records yet.")
    else:
        st.info("No live monitoring history yet. Open Live Monitoring and generate a cycle.")

    st.markdown("---")
    st.subheader("Prepared iFogSim2 / CloudSim Results")
    st.write(
        "The Java simulation is executed separately in the iFogSim2 environment. "
        "This dashboard does not run the Java simulation automatically."
    )
    st.write("Use the final metrics recorded from your completed Java simulation in your project report.")
    st.caption(
        "Fog/cloud assignments shown in this dashboard are logical software-simulation "
        "policies. They are not live measurements of a deployed network."
    )

# --------------------------------------------------
# FOOTER
# --------------------------------------------------
st.markdown("---")
st.caption(
    "DrainGuard | Academic Software Prototype | "
    "Synthetic sensor readings • ML-based risk classification • Simulated fog/cloud response"
)
