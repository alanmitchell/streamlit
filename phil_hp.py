# %%
import streamlit as st
import pandas as pd
import plotly.express as px
import bmondata

# %%
server = bmondata.Server('https://bmon.analysisnorth.com')
start_ts = '2020-09-01'
df_pwr = server.sensor_readings([
        ('phil_hp_pwr_16_pulse', 'pwr'),
    ], start_ts=start_ts)
df_pwr['on'] = df_pwr.pwr > 120.0
df_pwr['on_shift'] = df_pwr.on.shift()
df_pwr['cycle_boundary'] = df_pwr.on != df_pwr.on_shift
df_pwr.loc[df_pwr.index[0], 'cycle_boundary'] = False

#heat = server.sensor_readings([
#        ('phil_hp_out_13_btu_heat', 'heat'),
#    ], start_ts=start_ts).heat




# %%
df_pwr.query('cycle_boundary == True')

# %%

def run():

    st.markdown("""
    # Phil's Heat Pump Data

    Interesting and insightful data about Phil's heat pumps will eventually be here!
    """)


# %%
