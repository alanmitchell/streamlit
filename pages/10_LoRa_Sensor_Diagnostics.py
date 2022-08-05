import time
import math
from datetime import datetime, timedelta

from pytz import timezone
import streamlit as st
from google.cloud import bigquery
import plotly.express as px
import pandas as pd

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

st.sidebar.text_input('Enter Text to Filter Device List:', key='filter', on_change=filter_devices)

# deal with case where the filter_device() function has never run during the session
if 'filtered_devices' not in st.session_state:
    st.session_state.filtered_devices = []

device_id = st.sidebar.selectbox('Select a Device:', st.session_state.filtered_devices)
if not device_id:
    st.write('No Device selected yet.')
    st.stop()

data_days = 3
tz = 'US/Alaska'
tz_info = timezone(tz)

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

# ************ FIX ME: Do Tests for not enough Data for each element.

# -------- Battery Voltage ------------
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

if math.isnan(vbat):
    st.write('Battery Voltage is not Avaialble.')
else:
    st.write(f'**Battery Voltage:** {vbat:.2f} Volts')

# ----------- Reporting Interval and Last Reading -------------

df_diff = df3g.groupby('counter').last().reset_index().iloc[-2:][['ts', 'counter']].diff()
interval = round(df_diff.iloc[-1].ts.total_seconds() / df_diff.iloc[-1].counter / 60.0, 1)
st.write(f'**Reporting Interval:** {interval:.1f} minutes')

df_diff = df3g.iloc[-2:][['ts', 'counter']].diff()
interval = round(df_diff.iloc[-1].ts.total_seconds() / df_diff.iloc[-1].counter / 60.0, 1)
print(interval, 'minutes')

last_rec = df3g.iloc[-1]
minutes_ago = (time.time() - last_rec.ts.timestamp()) / 60

st.write(f'Last Reading was **{minutes_ago:.1f} minutes ago**')

# ------ Data Rate

st.write(f'**Current Data Rate:** {last_rec.data_rate}')

# ----------------- Readings / hour in Last 3 Days

df_rd = df3p.set_index('ts_tz')[['device']].resample('1H').count().iloc[:-1]
# reindex to include every hour in the last 3 days
ts_end = datetime.now(tz_info) - timedelta(hours=1)
ts_end = ts_end.replace(tzinfo=None, minute=0, second=0, microsecond=0)
new_ix = pd.date_range(ts_end - timedelta(hours=71), ts_end, freq='1H')
df3_full = df_rd.reindex(new_ix, fill_value=0.0)

st.write('#### Readings Received in each Hour for Last 3 Days')
fig = px.scatter(
    df3_full, x=df3_full.index, y='device',
    labels={
        'ts_tz': 'Date/Time',
        'device': 'Readings per Hour'
    }
)
st.plotly_chart(fig)

# ------------- Readings per hour Last 3 Months 

sql = f"""SELECT 
  count(device) as rec_count,
  DATETIME_TRUNC(DATETIME(ts, "{tz}"), DAY) as ts_day
FROM `things.payload`
WHERE 
  device = "{device_id}"
  AND ts >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 91 DAY)
GROUP BY ts_day
ORDER BY ts_day
"""
# don't include first and last partial days
# FIX ME:  Need to reindex with every day and put in Zeros!!
df3mo = client.query(sql).to_dataframe().iloc[1:-1]
df3mo.set_index('ts_day', inplace=True)
df3mo['rec_count'] = df3mo.rec_count / 24.0

# reindex to include every day in the last 90
dt_end = datetime.now(tz_info) - timedelta(days=1)
dt_end = dt_end.replace(tzinfo=None).date()
new_ix = pd.date_range(dt_end - timedelta(days=89), dt_end)
df3mo_full = df3mo.reindex(new_ix, fill_value=0.0)

st.write('#### Readings per Hour Received for Last 3 Months, daily averages')
fig = px.line(
    df3mo_full, x=df3mo_full.index, y='rec_count',
    labels={
        'ts_day': 'Day',
        'rec_count': 'Readings per Hour, daily average'
    }
)
st.plotly_chart(fig)

# ***** FIX ME: there is a problem at the start of the hour.  Get 0 readings per hour.

# ------------- Counts by Gateway in last 3 days
st.write('#### Gateways receiving Readings from Device')
dfg = df3g.groupby('gateway').count()[['device']].reset_index()
dfg.sort_values('device', inplace=True, ascending=False)
dfg.rename(columns={'device': 'Reading Count'}, inplace=True)
st.write(dfg)
 
# ---------- SNR by Gateway by Hour
df3g['ts_tz_hr'] = df3g['ts_tz'].dt.floor('h')
df3gh = df3g.groupby(['gateway', 'ts_tz_hr']).mean()[['snr']].reset_index()
fig = px.line(df3gh, x='ts_tz_hr', y='snr', color='gateway')
st.write('#### SNR Signal Strength by Gateway for last 3 Days')
st.plotly_chart(fig)