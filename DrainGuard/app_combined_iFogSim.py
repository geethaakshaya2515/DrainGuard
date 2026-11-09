import streamlit as st
import pandas as pd
import time
from pathlib import Path

st.set_page_config(page_title='DrainGuard | Smart Drainage Monitoring', page_icon='🌊', layout='wide')
BASE_DIR = Path(__file__).resolve().parent
SENSOR_PATH = BASE_DIR / 'sensor_inputs.csv'
PREDICTIONS_PATH = BASE_DIR / 'ml_predictions.csv'

st.markdown('''<style>.stApp{background:#0b1220;color:#f1f5f9}[data-testid="stMetric"]{background:#172338;padding:16px;border-radius:12px;border:1px solid #30445f}.zone-card{background:#172338;border:1px solid #30445f;border-radius:14px;padding:16px;margin-bottom:12px}div[data-testid="stSidebar"]{background:#101b2d}</style>''', unsafe_allow_html=True)

st.title('🌊 DrainGuard')
st.caption('ML-DRIVEN URBAN DRAINAGE BLOCKAGE RISK & EARLY WARNING SYSTEM')
st.sidebar.title('🌊 DrainGuard')
st.sidebar.caption('Navigation')
page = st.sidebar.radio('Go to', ['Overview & Analytics','Live Monitoring','Alerts & Maintenance','Fog & Cloud'])
st.sidebar.markdown('---')
st.sidebar.subheader('System Configuration')
st.sidebar.write('**IoT drainage zones:** 6')
st.sidebar.write('**Fog gateways:** 3')
st.sidebar.write('**Cloud servers:** 1')
st.sidebar.info('Data source: iFogSim simulated IoT sensors')

@st.cache_data(ttl=1)
def sensors():
    return pd.read_csv(SENSOR_PATH) if SENSOR_PATH.exists() else pd.DataFrame()

@st.cache_data(ttl=1)
def predictions():
    return pd.read_csv(PREDICTIONS_PATH) if PREDICTIONS_PATH.exists() else pd.DataFrame()

def risk_color(r):
    return {'Critical':'#ef4444','High':'#f97316','Moderate':'#eab308','Normal':'#22c55e'}.get(r,'#94a3b8')

def latest():
    s, p = sensors(), predictions()
    if s.empty: return pd.DataFrame()
    t = min(s.simulation_time.max(), p.simulation_time.max()) if not p.empty else s.simulation_time.max()
    s = s[s.simulation_time == t].copy()
    if p.empty: return s
    p = p[p.simulation_time == t].copy()
    return s.merge(p[['zone','predicted_risk','confidence','fog_node','processing_location']], on='zone', how='left')

def history():
    s, p = sensors(), predictions()
    if s.empty: return pd.DataFrame()
    if p.empty: return s
    return s.merge(p[['simulation_time','zone','predicted_risk','confidence','fog_node','processing_location']], on=['simulation_time','zone'], how='left')

def show_zones(df):
    for start in range(0,len(df),3):
        cols=st.columns(3)
        for col,(_,r) in zip(cols,df.iloc[start:start+3].iterrows()):
            with col:
                c=risk_color(r.get('predicted_risk'))
                st.markdown(f'''<div class="zone-card"><h3>{r.zone}</h3><h2 style="color:{c}">{r.get('predicted_risk','Waiting')}</h2><p>💧 Water Level: {r.water_level:.2f}%</p><p>🌊 Flow Rate: {r.flow_rate:.2f}</p><p>🌧️ Rainfall: {r.rainfall:.2f} mm</p><p>⚙️ Pressure: {r.pressure:.2f}</p><p>🧠 Confidence: {r.get('confidence','—')}%</p><p>📡 Gateway: {r.get('fog_node','—')}</p><p>🖥️ Processing: {r.get('processing_location','—')}</p></div>''',unsafe_allow_html=True)

if page == 'Overview & Analytics':
    st.header('System Overview')
    st.caption('Latest synchronized readings from iFogSim and Random Forest output.')
    if st.button('🔄 Refresh iFogSim Data'):
        sensors.clear(); predictions.clear(); st.rerun()
    if not SENSOR_PATH.exists(): st.error('sensor_inputs.csv not found. Run the iFogSim simulation first.'); st.stop()
    if not PREDICTIONS_PATH.exists(): st.warning('ml_predictions.csv not found yet. Run the ML cycle first.'); st.stop()
    df=latest()
    if df.empty: st.warning('Waiting for iFogSim data.'); st.stop()
    st.success(f"Latest synchronized iFogSim cycle: {df.simulation_time.iloc[0]} simulation seconds")
    counts=df.predicted_risk.value_counts(); critical=int(counts.get('Critical',0)); high=int(counts.get('High',0)); moderate=int(counts.get('Moderate',0)); normal=int(counts.get('Normal',0))
    c1,c2,c3,c4,c5=st.columns(5); c1.metric('IoT Zones',len(df)); c2.metric('Critical',critical); c3.metric('High Risk',high); c4.metric('Moderate',moderate); c5.metric('Normal',normal)
    st.markdown('---'); st.subheader('🚨 Current Risk Alerts'); alerts=df[df.predicted_risk.isin(['Critical','High'])]
    if alerts.empty: st.success('No High or Critical zones detected.')
    else:
        for _,r in alerts.iterrows(): st.error(f"{r.zone} — {r.predicted_risk} risk | Gateway: {r.fog_node} | Confidence: {r.confidence}%")
    st.markdown('---'); st.subheader('📡 IoT Zone Status'); show_zones(df)
    st.markdown('---'); left,right=st.columns(2)
    with left: st.markdown('#### Risk Distribution'); st.bar_chart(pd.Series({x:int((df.predicted_risk==x).sum()) for x in ['Critical','High','Moderate','Normal']},name='Zones'))
    with right: st.markdown('#### Fog vs Cloud Processing'); st.bar_chart(pd.Series({'Fog':int((df.processing_location=='FOG').sum()),'Cloud':int((df.processing_location=='CLOUD').sum())},name='Zones'))
    st.markdown('---'); st.subheader('📋 Latest iFogSim Sensor + ML Data'); st.dataframe(df,use_container_width=True,hide_index=True)

elif page == 'Live Monitoring':
    st.header('Live iFogSim Monitoring')
    st.caption('No independent/random sensor values are generated by Streamlit. The dashboard reads the iFogSim CSV files.')
    interval=st.sidebar.selectbox('Dashboard refresh interval (seconds)',[5,10,20,30],index=1)
    auto=st.sidebar.checkbox('Auto refresh',value=True)
    if st.sidebar.button('🔄 Refresh Now',use_container_width=True): sensors.clear(); predictions.clear(); st.rerun()
    df=latest()
    if df.empty: st.warning('Waiting for iFogSim data. Start the Java simulation and wait for the first ML cycle.'); st.stop()
    latest_time = float(df.simulation_time.iloc[0])
    cycle_number = int(df.cycle.iloc[0])
    st.success(
        f"🟢 CONNECTED TO iFogSim DATA | "
        f"Cycle {cycle_number} | "
        f"Simulation time: {latest_time:.0f} seconds"
    )
    counts=df.predicted_risk.value_counts(); c1,c2,c3,c4,c5,c6=st.columns(6)
    for c,label,val in zip([c1,c2,c3,c4,c5,c6],['IoT Zones','Critical','High','Moderate','Normal','Fog / Cloud'],[len(df),int(counts.get('Critical',0)),int(counts.get('High',0)),int(counts.get('Moderate',0)),int(counts.get('Normal',0)),f"{int((df.processing_location=='FOG').sum())} / {int((df.processing_location=='CLOUD').sum())}"]): c.metric(label,val)
    st.markdown('---'); st.subheader('📡 Live Zone Monitoring'); show_zones(df)
    st.markdown('---'); st.subheader('🚨 Current Live Alerts'); alerts=df[df.predicted_risk.isin(['Critical','High'])]
    if alerts.empty: st.success('No High or Critical zones detected in this cycle.')
    else:
        for _,r in alerts.iterrows(): st.error(f"{r.zone} | {r.predicted_risk} risk | Water: {r.water_level:.1f}% | Flow: {r.flow_rate:.1f} | Gateway: {r.fog_node}")
    h=history(); st.markdown('---'); st.subheader('📈 iFogSim Sensor History')
    if not h.empty:
        z=st.selectbox('Select drainage zone',[f'Zone-{i}' for i in range(1,7)])
        zh=h[h.zone==z].sort_values('simulation_time'); a,b=st.columns(2)
        with a: st.markdown('#### Water Level'); st.line_chart(zh.set_index('simulation_time').water_level)
        with b: st.markdown('#### Flow Rate'); st.line_chart(zh.set_index('simulation_time').flow_rate)
    st.markdown('---'); st.subheader('📋 Latest iFogSim Sensor Readings'); st.dataframe(df,use_container_width=True,hide_index=True)
    st.caption('Data flow: iFogSim IoT sensors → sensor_inputs.csv → Random Forest → ml_predictions.csv → Streamlit.')
    if auto:
        time.sleep(interval); sensors.clear(); predictions.clear(); st.rerun()

elif page == 'Alerts & Maintenance':
    st.header('🚨 Alerts & Maintenance Management')
    df=latest()
    if df.empty: st.info('No iFogSim prediction data available yet.'); st.stop()
    alerts=df[df.predicted_risk.isin(['High','Critical'])]
    if alerts.empty: st.success('No High or Critical zones in the latest cycle.')
    else:
        c1,c2,c3=st.columns(3); c1.metric('Active Alerts',len(alerts)); c2.metric('High Risk',int((alerts.predicted_risk=='High').sum())); c3.metric('Critical',int((alerts.predicted_risk=='Critical').sum()))
        for _,r in alerts.iterrows():
            action='Emergency drainage inspection' if r.predicted_risk=='Critical' else 'Urgent drainage inspection'
            with st.container(border=True):
                st.markdown(f"### {r.zone} — {r.predicted_risk} Risk"); st.write(f"Gateway: {r.fog_node} | Processing: {r.processing_location}"); st.write(f"Water: {r.water_level:.2f}% | Flow: {r.flow_rate:.2f} | Rainfall: {r.rainfall:.2f} mm | Pressure: {r.pressure:.2f}"); st.warning(f'Recommended action: {action}')
    st.markdown('---'); st.subheader('Actuator / Warning Event'); st.info('High and Critical conditions generate a simulated warning/actuator event. No physical actuator is connected.')

else:
    st.header('☁️ Fog & Cloud Processing')
    st.caption('Processing allocation produced by the DrainGuard decision layer.')
    h=history(); latest_df=latest()
    if h.empty or latest_df.empty: st.info('No iFogSim history available yet.'); st.stop()
    h=h.dropna(subset=['processing_location']); fog=h[h.processing_location=='FOG']; cloud=h[h.processing_location=='CLOUD']
    c1,c2,c3=st.columns(3); c1.metric('Fog Records',len(fog)); c2.metric('Cloud Records',len(cloud)); c3.metric('Latest Cycle',latest_df.simulation_time.iloc[0])
    st.markdown('---'); st.subheader('Zone → Fog Gateway Mapping'); st.dataframe(pd.DataFrame({'Zone':[f'Zone-{i}' for i in range(1,7)],'Fog Gateway':['fog-1','fog-1','fog-2','fog-2','fog-3','fog-3']}),use_container_width=True,hide_index=True)
    st.subheader('Latest Fog / Cloud Decisions'); st.dataframe(latest_df[['simulation_time','zone','predicted_risk','confidence','fog_node','processing_location']],use_container_width=True,hide_index=True)
    st.subheader('Recent Cloud-Processed Readings')
    if cloud.empty: st.info('No Cloud-processed records yet.')
    else: st.dataframe(cloud[['simulation_time','zone','water_level','flow_rate','predicted_risk','fog_node']].tail(20),use_container_width=True,hide_index=True)

st.markdown('---')
st.caption('DrainGuard | Academic Software Prototype | iFogSim IoT sensor readings → Random Forest risk classification → Fog/Cloud allocation → Simulated warning event')
