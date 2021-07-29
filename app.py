import streamlit as st
import pce_dashboard
import phil_hp
import lora_sig

apps = {
    'lora-sig': 'LoRa Signal Strength',
    'pce': 'Power Cost Equalization (PCE) Data',
    'phil-hp': "Phil's Heat Pump Data",
}

def main():
    app = st.sidebar.radio('Select Application', list(apps.keys()), 0, apps.get)

    if app == 'pce':
        pce_dashboard.run()

    elif app == 'phil-hp':
        phil_hp.run()

    elif app == 'lora-sig':
        lora_sig.run()

if __name__ == '__main__':
    main()