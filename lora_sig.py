import time
import json
import datetime
from pathlib import Path
import subprocess
from dateutil.parser import parse
from dateutil import tz
import streamlit as st
import pandas as pd
import plotly.express as px

lora_data_file = '../an-api/lora-data/lora.txt'
reading_count_to_read = 500

gtw_lbls = {
    'eui-00800000a00034ed': 'Kasilof',
    'eui-3235313227006100': 'Abbot/Elmore',
    'eui-323531322b004500': 'Intl/C St',
    'eui-58a0cbfffe800baf': 'SEED Lab',
    'eui-58a0cbfffe8015fd': 'Tyler Indoor',
    'eui-a840411d91b44150': 'Dragino LPS8',
    'eui-c0ee40ffff293d87': 'Laird',
    'kl4qh-mtcdt3': 'ANMC',
    'eui-24e124fffef06f56': 'Old Swd/Tudor',
    'eui-000080029c2b2b77': 'Bear Valley',
    'eui-a84041ffff1ee2b4': 'Dragino Outdoor',
}

dev_lbls = dict(
    A81758FFFE0523DB = 'ELT #1 23DB',
)

def gtw_map(x):
    if x in gtw_lbls:
        return gtw_lbls[x]
    else:
        return x if len(x) <= 10 else x[:4] + '..' + x[-4:]

def dev_map(x):
    return dev_lbls.get(x, x)

tz_display = tz.gettz('US/Alaska')
def decode_post(post_data):
    d = json.loads(post_data)
    ts_utc = parse(d['metadata']['time'])
    ts = ts_utc.astimezone(tz_display).replace(tzinfo=None)
    gateways = [
        dict(
            gateway = gtw_map(gtw['gtw_id']),
            snr = gtw['snr'],
            rssi = gtw['rssi']
        ) for gtw in d['metadata']['gateways']
    ]
    return dict(
        sensor = dev_map(d['hardware_serial']),
        data_rate = d['metadata']['data_rate'],
        ts = ts,
        ts_utc = ts_utc,
        gateways = gateways
    )

def get_readings(reading_ct=reading_count_to_read, data_file=lora_data_file):
    """Returns a DataFrame of the last 'reading_ct' readings received.
    Readings are read from the file with a full path of 'data_file'.
    """
    cmd = f'/usr/bin/tail -n {reading_ct} ' + data_file
    output = subprocess.check_output(cmd, shell=True)
    results = []
    for lin in output.splitlines():
        data = decode_post(lin)
        results.append(data)
    return pd.DataFrame(results)

def run():

    st.markdown("# LoRa Signal Strength Data")

    sensor = st.sidebar.selectbox('Select Sensor to View', list(dev_lbls.values()))
    rcv_time = st.sidebar.slider('Minutes to Receive Data', min_value=0.1, max_value=15.0, value=1.0, step=0.1)
    reading_history_n = st.sidebar.slider('Number of Readings to Plot in History Chart', 10, 100, 40)
    start_button = st.sidebar.button('Start Receiving')
    txt_seconds_ago = st.empty()
    cht = st.empty()
    cht_history = st.empty()
    start = time.time()
    if start_button:
        file_mod_time = None
        last_ts = None
        last_datarate = None
        while (time.time() - start)/60.0 < rcv_time:
            if last_ts:
                seconds_ago = time.time() - last_ts
                txt_seconds_ago.markdown(f'### {seconds_ago:,.0f} secs ago, {last_datarate}')
            cur_file_mod_time = Path(lora_data_file).stat().st_mtime
            if file_mod_time != cur_file_mod_time:
                file_mod_time = cur_file_mod_time
                df = get_readings()
                df_sensor = df.query('sensor == @sensor')
                info = df_sensor.iloc[-1].to_dict()     # get last reading
                last_ts = info['ts_utc'].timestamp()
                last_datarate = info['data_rate']
                seconds_ago = time.time() - last_ts
                txt_seconds_ago.markdown(f'### {seconds_ago:,.0f} secs ago, {last_datarate}')
                gtws = [g['gateway'] for g in info['gateways']]
                snrs = [g['snr'] for g in info['gateways']]
                df_gtw = pd.DataFrame(data = {'Gateway': gtws, 'SNR': snrs})
                df_gtw['SNR above -10 dB'] = df_gtw.SNR + 10
                df_gtw.sort_values('Gateway', inplace=True) 
                fig = px.bar(df_gtw, x='Gateway', y='SNR above -10 dB')  
                fig.update_yaxes(range=[0, 20])
                fig.update_xaxes(
                    tickangle = 30,
                    title_font = {'size': 15},
                    tickfont = {'size': 15},
                )
                cht.plotly_chart(fig, use_container_width=True)

                # make a history data frame with a row for each gateway reception.
                # Plot a scatter plot of the results.
                recs = []
                for _, r in df_sensor.tail(reading_history_n).iterrows():
                    ts = r.ts
                    for gtw in r.gateways:
                        rec = dict(
                            Time = ts,
                            Gateway = gtw['gateway'],
                            SNR = gtw['snr']
                        )
                        recs.append(rec)
                df_history = pd.DataFrame(recs)
                fig = px.scatter(df_history, x='Time', y='SNR', color='Gateway')
                fig.update_yaxes(range=[-14, 14])
                cht_history.plotly_chart(fig, use_container_width=True)

            time.sleep(1)

        txt_seconds_ago.empty()
        cht.empty()
        cht_history.empty()
