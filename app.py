import streamlit as st
import pce_dashboard
import phil_hp

apps = {
    'pce': 'Power Cost Equalization (PCE) Data',
    'phil-hp': "Phil's Heat Pump Data",
}

def main():
    app = st.sidebar.radio('Select Application', list(apps.keys()), 0, apps.get)

    if app == 'pce':
        pce_dashboard.run()

    elif app == 'phil-hp':
        phil_hp.run()

if __name__ == '__main__':
    main()