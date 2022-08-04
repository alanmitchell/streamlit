import streamlit as st
from google.cloud import bigquery

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

st.sidebar.selectbox('Select a Device', all_devices())