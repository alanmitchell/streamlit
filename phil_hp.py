# %%
import streamlit as st
import pandas as pd
import plotly.express as px
import bmondata

# %%
server = bmondata.Server('https://bmon.analysisnorth.com')
start_ts = '2020-09-01'
df = server.sensor_readings([
        ('phil_hp_out_13_btu_heat', 'heat'),
        ('phil_hp_out_13_btu_thot', 'leaving_t'),
        ('phil_hp_out_13_btu_tcold', 'entering_t'),
        ('phil_hp_out_13_btu_pulse', 'flow'),
        ('phil_hp_pwr_10187_temp', 'out_t'),
    ], start_ts=start_ts)
df_pwr = server.sensor_readings([
        ('phil_hp_pwr_16_pulse', 'power'),
    ], start_ts=start_ts)
df_pwr['on'] = df_pwr.power > 120.0
df_pwr['on_shift'] = df_pwr.on.shift()
df_pwr['cycle_boundary'] = df_pwr.on != df_pwr.on_shift
df_pwr.loc[df.index[0], 'cycle_boundary'] = False



# %%
df_bound = df_pwr.query('cycle_boundary == True')
st = 0 if df_bound.on[0] == True else 1
en = None if df_bound.on[-1] == False else -1
cycles = df_bound.index.values[st:en].reshape((-1,2))

for cycle_st, cycle_en in cycles:
    query_expr = '@cycle_st <= index < @cycle_en'
    
    rec = {'power': df_pwr.query(query_expr).power.mean()}

    df_cycle = df.query(query_expr).mean()
    for fld in ('heat', 'flow', 'entering_t', 'leaving_t', 'out_t'):
        rec[fld] = df_cycle[fld]
    rec['cop'] = rec['heat'] / rec['power'] / 3.413
    rec['delta_t'] = rec['leaving_t'] - rec['entering_t']
    print(rec)

# %%

def run():

    st.markdown("""
    # Phil's Heat Pump Data

    Interesting and insightful data about Phil's heat pumps will eventually be here!
    """)


# %%
