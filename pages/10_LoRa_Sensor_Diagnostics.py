import time

import streamlit as st
from google.cloud import bigquery
import plotly.express as px

st.write('# LoRaWAN Sensor Diagnostics')

# create a BigQuery client
client = bigquery.Client()

@st.cache(ttl=3600)
def all_devices():
    # return a list of all unique device IDs
    sql = """
    SELECT DISTINCT device
    FROM `an-projects.things.gateway_reception`
    """
    df = client.query(sql).to_dataframe()
    devices = df.device.values
    devices.sort()
    return devices

def filter_devices():
    st.session_state.filtered_devices = [d for d in all_devices() if st.session_state.filter in d]
    if len(st.session_state.filtered_devices) > 1:
        # insert a blank item at the top so no real device is selected
        st.session_state.filtered_devices.insert(0, '')

st.sidebar.text_input('Text to Filter Devices', key='filter', on_change=filter_devices)

# deal with case where the filter_device() function has never run during the session
if 'filtered_devices' not in st.session_state:
    st.session_state.filtered_devices = []

device_id = st.sidebar.selectbox('Select a Device', st.session_state.filtered_devices)
if not device_id:
    st.write('No Device selected')
    st.stop()

data_days = 3
tz = 'US/Alaska'

st.write(f'**Device ID:** {device_id}')

sql = f"""SELECT 
  *, 
  DATETIME(ts, "{tz}") as ts_tz
FROM `things.gateway_reception`
WHERE 
  device = "{device_id}"
  AND ts >= TIMESTAMP_TRUNC(TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {data_days} DAY), HOUR)
ORDER BY ts"""
df3g = client.query(sql).to_dataframe()

sql = f"""SELECT 
  *,
  DATETIME(ts, "{tz}") as ts_tz
FROM `things.payload`
WHERE 
  device = "{device_id}"
  AND ts >= TIMESTAMP_TRUNC(TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {data_days} DAY), HOUR)
ORDER BY ts"""
df3p = client.query(sql).to_dataframe()

vbat = df3p.iloc[-1].vbat

st.write(f'**Battery Voltage:** {vbat:.2f} Volts')

last_ts = df3p.iloc[-1].ts
minutes_ago = (time.time() - last_ts.timestamp()) / 60

st.write(f'Last Reading was **{minutes_ago:.1f} minutes ago**')

df_rd = df3p.set_index('ts_tz')[['device']].resample('1H').count()
fig = px.line(df_rd, x=df_rd.index, y='device')
st.plotly_chart(fig)