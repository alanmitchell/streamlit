import streamlit as st
import pce_dashboard
import phil_hp
import lora_sig
import lora_success
import hp_rebate_econ


apps = {
    'lora-sig': 'LoRa Signal Strength',
    'lora-success': 'LoRa Sensor Performance',
    'heat-pump-econ': 'Heat Pump Utility Rebate Economics',
    'pce': 'Power Cost Equalization (PCE) Data',
    # 'phil-hp': "Phil's Heat Pump Data",
}

def main():

    st.set_page_config(layout='wide')

    app = st.sidebar.radio('Select Application', list(apps.keys()), 0, apps.get)

    if app == 'pce':
        pce_dashboard.run()

    elif app == 'lora-success':
        lora_success.run()

    elif app == 'lora-sig':
        lora_sig.run()

    elif app == 'heat-pump-econ':
        hp_rebate_econ.run()

if __name__ == '__main__':
    main()