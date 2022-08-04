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

def filter_devices():
    st.session_state.filtered_devices = [d for d in all_devices() if st.session_state.filter in d]
    if len(st.session_state.filtered_devices) > 1:
        # insert a blank item at the top so no real device is selected
        st.session_state.filtered_devices.insert(0, '')

st.sidebar.text_input('Text to Filter Devices', key='filter', on_change=filter_devices)

# deal with case where the filter_device() function has never run during the session
if 'filtered_devices' not in st.session_state:
    st.session_state.filtered_devices = []

device = st.sidebar.selectbox('Select a Device', st.session_state.filtered_devices)
if not device:
    st.write('No Device selected')
    st.stop()

st.write(f'**Device ID:** {device}')
