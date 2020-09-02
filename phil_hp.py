import streamlit
import pandas as pd
import plotly.express as px
import bmondata

dfr = None

def run():
    global dfr
    
    streamlit.markdown("# Phil's Heat Pump Data")

    refresh = streamlit.sidebar.button('Refresh Data')
    if dfr is None or refresh:
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

        df_bound = df_pwr.query('cycle_boundary == True')
        st = 0 if df_bound.on[0] == True else 1
        en = None if df_bound.on[-1] == False else -1
        cycles = df_bound.index.values[st:en].reshape((-1,2))

        recs = []
        for cycle_st, cycle_en in cycles:
            query_expr = '@cycle_st <= index < @cycle_en'
            
            rec = {'power': df_pwr.query(query_expr).power.mean()}

            df_cycle = df.query(query_expr).mean()
            for fld in ('heat', 'flow', 'entering_t', 'leaving_t', 'out_t'):
                rec[fld] = df_cycle[fld]
            rec['cop'] = rec['heat'] / rec['power'] / 3.413
            rec['heat_dt'] = rec['leaving_t'] - rec['entering_t']
            rec['entering_out_dt'] = rec['entering_t'] - rec['out_t']
            rec['date_time'] =  pd.to_datetime((cycle_en - cycle_st) / 2.0 + cycle_st)
            rec['date_time_str'] = rec['date_time'].strftime('%D %H:%M:%S')
            rec['cycle_minutes'] = (cycle_en - cycle_st) / 1e9 / 60.0
            recs.append(rec)

        dfr = pd.DataFrame(recs)

    streamlit.markdown("""## COP vs. Outdoor Temperature

Each point is one cycle.  The color of the point indicates the compressor power during
the cycle.
""")
    fig = px.scatter(dfr, x='out_t', y='cop', 
        color='power', 
        hover_data=['date_time_str', 'entering_t', 'flow', 'heat_dt', 'cycle_minutes'], 
        color_continuous_scale="Bluered_r")
    fig.update_layout(
        xaxis_title = 'Outdoor Temperature, deg F',
        yaxis_title = 'COP',
        coloraxis_colorbar_title_text = 'Compressor Power'
    )
    streamlit.write(fig)

    streamlit.markdown("""## COP vs. (Heat Pump Entering - Outdoor Temp)
""")
    fig = px.scatter(dfr, x='entering_out_dt', y='cop', 
        color='power', 
        hover_data=['date_time_str', 'entering_t', 'out_t', 'flow', 'heat_dt', 'cycle_minutes'], 
        color_continuous_scale="Bluered_r")
    fig.update_layout(
        xaxis_title = 'Heat Pump Entering - Outdoor Temperature, deg F',
        yaxis_title = 'COP',
        coloraxis_colorbar_title_text = 'Compressor Power'
    )
    streamlit.write(fig)
