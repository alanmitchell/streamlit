"""LoRa Sensor Transmission Success App.
"""
from tempfile import TemporaryDirectory
from datetime import datetime, timedelta
from pytz import timezone
from pathlib import Path

import streamlit as st
import pandas as pd

from trim_files import trim_file

lora_data_file = '../an-api/lora-data/gateways.tsv'

def run():

    st.markdown('''
# LoRa Sensor Performance

This table summarizes transmission characteristics and performance for sensor reporting
to the LoRa Debug database. The *Last Data Rate* column shows the LoRa Data Rate for the 
last sensor transmission.  The *Success %* column shows the percentage of the sensor's total
transmissions during the last 24 hours that were received by the network.  Success rates less
than 90% are colored red.

Note that if the Sensor reboots, the value in the *Success %* column will be distorted.
    ''')

    if st.button('Run Again with Current Data'):
        pass

    with TemporaryDirectory() as tempdirname:

        extract_file = Path(tempdirname) / 'gtw.tsv'
        try:
            trim_file(lora_data_file, extract_file, 1)
        except:
            # were no records, just the header row
            pass

        df = pd.read_csv(extract_file, sep='\t', parse_dates=['ts'])
        tz_ak = timezone('US/Alaska')
        ts_now = datetime.now(tz_ak)
        ts_start = (ts_now - timedelta(days=1)).replace(tzinfo=None)
        df1d = df.query('ts >= @ts_start')

        dfs = df1d.groupby('dev_id').agg(
            {
                'data_rate': 'last',
                'counter': ['first', 'last']
            }
        )
        dfs.columns = ['data_rate', 'counter_first', 'counter_last']
        dfs['total_rdg'] = dfs.counter_last - dfs.counter_first + 1

        df_rcvd = df1d[['dev_id', 'counter']].drop_duplicates()
        df_rcvd = df_rcvd.groupby('dev_id').count()
        df_rcvd.columns = ['rcvd']

        df_final = dfs.join(df_rcvd)
        df_final['success_pct'] = df_final.rcvd / df_final.total_rdg * 100.0
        df_final = df_final.round({'success_pct': 1})

        df_display = df_final[['data_rate', 'success_pct']].copy()
        df_display['data_rate'] = df_display.data_rate.str.replace('.0', '', regex=False)
        df_display.columns = ['Last Data Rate', 'Success %']
        df_display.index.name = 'Sensor Dev ID'
        df_display.reset_index(inplace=True)
        s2 = df_display.style.applymap(lambda v: 'color:red;' if v < 90 else None, subset=['Success %']).format('{:.1f}%', subset=['Success %'])
        
        st.markdown(f"Summary of data for the 24 hours prior to: **{ts_start.strftime('%Y-%m-%d %H:%M')}**")
        st.dataframe(s2, height=50000)
