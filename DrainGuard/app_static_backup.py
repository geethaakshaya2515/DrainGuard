
import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(
    page_title="DrainGuard | Smart Drainage Monitoring",
    page_icon="🌊",
    layout="wide"
)

# ---------- Styling ----------
st.markdown("""
<style>
.stApp {
    background: #0b1220;
    color: #f1f5f9;
}
[data-testid="stMetric"] {
    background: #172338;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #263852;
}
.zone-card {
    background: #172338;
    border: 1px solid #30445f;
    border-radius: 14px;
    padding: 18px;
    margin-bottom: 12px;
}
.small {
    color: #94a3b8;
    font-size: 13px;
}
</style>
""", unsafe_allow_html=True)

# ---------- Load ML predictions ----------
file_path = Path("ml_predictions.csv")

st.title("🌊 DrainGuard")
st.caption("ML-Driven Urban Drainage Blockage Prediction & Early Warning System")
st.markdown("---")

if not file_path.exists():
    st.error("ml_predictions.csv not found. Run predict_zones.py first.")
    st.stop()

df = pd.read_csv(file_path)

# ---------- Sidebar ----------
st.sidebar.title("⚙️ Control Panel")
st.sidebar.success("ML Model: Random Forest")
st.sidebar.info("Simulation: iFogSim2 / CloudSim")
st.sidebar.markdown("### System Configuration")
st.sidebar.write("Drainage Zones: 6")
st.sidebar.write("Fog Gateways: 3")
st.sidebar.write("Cloud Servers: 1")

if st.sidebar.button("🔄 Refresh Dashboard"):
    st.rerun()

# ---------- Summary ----------
total = len(df)
critical = int((df["predicted_risk"] == "Critical").sum())
high = int((df["predicted_risk"] == "High").sum())
normal = int((df["predicted_risk"] == "Normal").sum())
fog_count = int((df["processing_location"] == "FOG").sum())
cloud_count = int((df["processing_location"] == "CLOUD").sum())

st.subheader("System Overview")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Zones", total)
c2.metric("Critical Zones", critical)
c3.metric("High Risk Zones", high)
c4.metric("Normal Zones", normal)

st.markdown("---")

# ---------- Alerts ----------
st.subheader("🚨 Drainage Risk Alerts")

alerts = df[df["predicted_risk"].isin(["Critical", "High"])]

if alerts.empty:
    st.success("No elevated-risk zones detected.")
else:
    for _, row in alerts.iterrows():
        st.error(
            f"{row['zone']} — {row['predicted_risk']} risk | "
            f"Gateway: {row['fog_node']} | "
            f"Confidence: {row['confidence']}%"
        )

# ---------- Zone Cards ----------
st.markdown("---")
st.subheader("📍 Live Simulated Zone Monitoring")

for start in range(0, len(df), 3):
    cols = st.columns(3)

    for col, (_, row) in zip(cols, df.iloc[start:start+3].iterrows()):
        risk = row["predicted_risk"]

        color = {
            "Critical": "#ef4444",
            "High": "#f97316",
            "Moderate": "#eab308",
            "Normal": "#22c55e"
        }.get(risk, "#94a3b8")

        with col:
            st.markdown(f"""
            <div class="zone-card">
                <h3>{row['zone']}</h3>
                <h2 style="color:{color}">{risk}</h2>
                <p>💧 Water Level: {row['water_level']}%</p>
                <p>🌧️ Rainfall: {row['rainfall']} mm (simulated)</p>
                <p>🌊 Flow Rate: {row['flow_rate']}</p>
                <p>⚙️ Pressure: {row['pressure']}</p>
                <p>🧠 ML Confidence: {row['confidence']}%</p>
                <p>📡 Gateway: {row['fog_node']}</p>
                <p>🖥️ Processing: {row['processing_location']}</p>
            </div>
            """, unsafe_allow_html=True)

# ---------- Charts ----------
st.markdown("---")
st.subheader("📊 Analytics")

left, right = st.columns(2)

with left:
    st.markdown("#### Risk Distribution")
    risk_counts = (
        df["predicted_risk"]
        .value_counts()
        .rename_axis("Risk")
        .to_frame("Zones")
    )
    st.bar_chart(risk_counts)

with right:
    st.markdown("#### Fog vs Cloud Processing")
    processing = pd.DataFrame({
        "Processing": ["Fog", "Cloud"],
        "Zones": [fog_count, cloud_count]
    }).set_index("Processing")
    st.bar_chart(processing)

# ---------- Sensor data ----------
st.markdown("---")
st.subheader("📋 Detailed Sensor and ML Data")
st.dataframe(df, use_container_width=True, hide_index=True)

# ---------- Simulation metrics ----------
st.markdown("---")
st.subheader("☁️ Fog Computing Simulation Results")

m1, m2, m3 = st.columns(3)
m1.metric("Fog Processed", fog_count)
m2.metric("Cloud Processed", cloud_count)
m3.metric("Average Simulated Latency", "4.0 units")

st.caption(
    "Latency uses the configured simulation assumptions: "
    "2 time units for fog and 8 for cloud. "
    "These are simulated values, not real network measurements."
)

st.markdown("---")
st.caption(
    "DrainGuard | Academic IoT Prototype | "
    "Synthetic sensor data and simulated drainage scenarios"
)
