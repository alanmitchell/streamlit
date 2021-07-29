import time
import json
import io
import datetime
from pathlib import Path
import subprocess
from dateutil.parser import parse
import pytz
import streamlit as st
import pandas as pd
import plotly.express as px

from label_map import dev_lbls, gtw_lbls

lora_data_file = '../an-api/lora-data/gateways.tsv'
lines_to_read = 10000

def gtw_map(x):
    if x in gtw_lbls:
        return gtw_lbls[x]
    else:
        return x if len(x) <= 10 else x[:4] + '..' + x[-4:]

def dev_map(x):
    return dev_lbls.get(x, x)

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

# timezone of the 'ts' column in the data is Alaska
tz_data = pytz.timezone('US/Alaska')

def get_readings(dev_id, line_ct=lines_to_read, data_file=lora_data_file):
    """Returns a DataFrame of the readings for the "dev_id" sensor in the last 'line_ct' 
    lines in the LoRa gateway file. Readings are read from the file with a full path 
    of 'data_file'.  Only the Gateway, SNR, data_rate, counter and the ts (timestamp) columns are retained, 
    and the timestamp column is converted to a DateTime column.  Gateway labels are used
    if available for a particular Gateway ID.
    """
    # get the header row
    cmd = f'/usr/bin/head -n 1 ' + data_file
    hdr =  subprocess.check_output(cmd, shell=True)
    
    # get the data rows requested
    cmd = f'/usr/bin/tail -n {line_ct} ' + data_file
    output = subprocess.check_output(cmd, shell=True)
    
    df = pd.read_csv(io.BytesIO(hdr + output), sep='\t')
    # Filter to desired sensor and desired columns
    df = df.query('dev_id == @dev_id')[['ts', 'gateway', 'snr', 'data_rate', 'counter']]

    # rename columns for better graph labels
    df.rename(columns={'gateway': 'Gateway', 'snr': 'SNR'}, inplace=True)

    # convert timestamp column to datetime
    df['ts'] = pd.to_datetime(df.ts, format='%Y-%m-%d %H:%M:%S')

    # convert datatypes of other columns, as they end up object
    df = df.astype(
        {'SNR': float, 'counter': int}
    )

    # Convert to Gateway labels
    df['Gateway'] = df.Gateway.apply(gtw_map)
    
    return df

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
                df = get_readings(sensor)
                df_rdg = df.groupby('counter')
                df_last = list(df_rdg)[-1][1]             # DataFrame for last reading

                # get the first gateway in order to extract timestamp and data rate.
                first_gtw = df_last.iloc[0].to_dict()

                # convert the date/time into UTC and get a Unix timestamp from it
                last_ts = tz_data.localize(first_gtw['ts']).astimezone(pytz.UTC).timestamp()
                last_datarate = first_gtw['data_rate']
                seconds_ago = time.time() - last_ts
                txt_seconds_ago.markdown(f'### {seconds_ago:,.0f} secs ago, {last_datarate}')

                # Use the Dataframe of the last reading to make the top plot
                df_last['SNR above -10 dB'] = df_last.SNR + 10
                df_last.sort_values('Gateway', inplace=True) 
                fig = px.bar(df_last, x='Gateway', y='SNR above -10 dB')  
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
                fig.update_yaxes(range=[-15, 15])
                cht_history.plotly_chart(fig, use_container_width=True)

            time.sleep(1)

        txt_seconds_ago.empty()
        cht.empty()
        cht_history.empty()
