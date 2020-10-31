import time
import json
import datetime
from pathlib import Path
from dateutil.parser import parse
import streamlit
import pandas as pd
import plotly.express as px

last_post_path = '../an-api/lora-data/lora-last.txt'

gtw_lbls = {
    'eui-00800000a00034ed': 'Kasilof',
    'eui-3235313227006100': 'Abbot/Elmore',
    'eui-323531322b004500': 'Intl/C St',
    'eui-58a0cbfffe800baf': 'SEED Lab',
    'eui-58a0cbfffe8015fd': 'Tyler',
    'eui-a840411d91b44150': 'Dragino LPS8',
    'eui-c0ee40ffff293d87': 'Laird',
    'kl4qh-mtcdt3': 'ANMC',
    'eui-24e124fffef06f56': 'Old Swd/Tudor',
    'eui-000080029c2b2b77': 'Bear Valley',
    'eui-a84041ffff1ee2b4': 'Dragino Outdoor',
}

def gtw_map(x):
    if x in gtw_lbls:
        return gtw_lbls[x]
    else:
        return x if len(x) <= 10 else x[:4] + '..' + x[-4:]

dev_lbls = dict(
    A81758FFFE046262 = 'SEED Alcove',
    A81758FFFE048DA1 = 'Tyler',
    A81758FFFE0526D2 = '2nd Flr East',
    A81758FFFE0526D3 = '1st Flr Risk',
    A81758FFFE0526D4 =  '1st Flr Training',
    A81758FFFE0526D5 = '4th Flr West',
    A81758FFFE0526D6 = '3rd Flr Office',
    A81758FFFE0526D7 = 'R2D2',
    A84041000181C74E = 'Alan Freezer',
    A84041000181C772 = 'Alan Outdoor Temp',
    A84041C991822CA8 = 'Alan Greenhouse'
)
def dev_map(x):
    return dev_lbls.get(x, x)

def decode_post(post_data):
    d = json.loads(post_data)
    ts = parse(d['metadata']['time'])
    seconds_ago = (datetime.datetime.now(datetime.timezone.utc) - ts).total_seconds()
    gateways = [
        dict(
            gateway = gtw_map(gtw['gtw_id']),
            snr = gtw['snr'],
            rssi = gtw['rssi']
        ) for gtw in d['metadata']['gateways']
    ]
    return dict(
        sensor = dev_map(d['hardware_serial']),
        seconds_ago = seconds_ago,
        gateways = gateways
    )

def run():

    streamlit.markdown("# LoRa Signal Strength Data")

    rcv_time = streamlit.slider('Minutes to Receive Data', min_value=0.1, max_value=15.0, value=1.0, step=0.1)
    st = time.time()
    start_button = streamlit.button('Start Receiving')
    txt_seconds_ago = streamlit.empty()
    cht = streamlit.empty()
    if start_button:
        while (time.time() - st)/60.0 < rcv_time:
            if Path(last_post_path).exists():
                last_post = open(last_post_path).read()
                info = decode_post(last_post)
                txt_seconds_ago.markdown(f'### {info["seconds_ago"]:,.0f} secs ago, {info["sensor"]}')
                gtws = [g['gateway'] for g in info['gateways']]
                snrs = [g['snr'] for g in info['gateways']]
                df = pd.DataFrame(data = {'Gateway': gtws, 'SNR': snrs})
                df['SNR above -10 dB'] = df.SNR + 10
                df.sort_values('Gateway', inplace=True) 
                fig = px.bar(df, x='Gateway', y='SNR above -10 dB')  
                fig.update_yaxes(range=[0, 20])
                fig.update_xaxes(
                    tickangle = 30,
                    title_font = {'size': 15},
                    tickfont = {'size': 15},
                )
                fig.update_layout(

                )
                cht.plotly_chart(fig, use_container_width=True)

            else:
                txt_seconds_ago.markdown('## No Data')
            time.sleep(2)
        txt_seconds_ago.empty()
        cht.empty()
