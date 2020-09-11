import streamlit
import pandas as pd
import numpy as np
import plotly.express as px
import bmondata
from dateutil.parser import parse

# A list of date ranges to exclude from the cycle analysis.  If the midpoint of the cycle
# falls in any one of the following ranges, it is not included.
DATES_TO_REMOVE = (
    ('2020-09-07 11:00', '2020-09-07 16:30'),
)

dfr = None

def run():

    global dfr
    
    streamlit.markdown("# Phil's Heat Pump Data")

    refresh = streamlit.sidebar.button('Refresh Data')
    if dfr is None or refresh:
        server = bmondata.Server('https://bmon.analysisnorth.com')
        start_ts = '2020-09-07 16:30'
        df = server.sensor_readings([
                ('phil_hp_out_13_btu_heat', 'heat'),
                ('phil_hp_out_13_btu_thot', 'leaving_t'),
                ('phil_hp_out_13_btu_tcold', 'entering_t'),
                ('phil_hp_out_13_btu_pulse', 'flow'),
                ('phil_hp_pwr_10187_temp', 'out_t'),
            ], start_ts=start_ts)
        # found that sometimes outdoor temperature misses readings, so interpolate it.
        # But, should keep an eye on it to ensure not too much interpolation is going on.
        df['out_t'] = df.out_t.interpolate(method='time')
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

            date_time = pd.to_datetime((cycle_en - cycle_st) / 2.0 + cycle_st)
            # check to see if this cycle falls in one of the intervals that should be excluded
            exclude_cycle = False
            for excl_st, excl_en in DATES_TO_REMOVE:
                if date_time >= parse(excl_st) and date_time <= parse(excl_en):
                    exclude_cycle = True
            if exclude_cycle:
                continue

            rec = {'date_time': date_time}
            rec['date_time_str'] = rec['date_time'].strftime('%-m/%-d/%y %-I:%M %p')
            rec['cycle_minutes'] = float((cycle_en - cycle_st)) / 1e9 / 60.0
            
            rec['power'] = df_pwr.query(query_expr).power.mean()

            df_cycle = df.query(query_expr).mean()
            for fld in ('heat', 'flow', 'entering_t', 'leaving_t', 'out_t'):
                rec[fld] = df_cycle[fld]
            rec['cop'] = rec['heat'] / rec['power'] / 3.413
            rec['heat_dt'] = rec['leaving_t'] - rec['entering_t']
            rec['entering_out_dt'] = rec['entering_t'] - rec['out_t']
            recs.append(rec)

        dfr = pd.DataFrame(recs)

    streamlit.markdown("""## COP vs. Outdoor Temperature

Each point is one cycle, and the COP shown only includes energy flows during the cycle.
The color of the point indicates the compressor power during
the cycle.  Larger dots are more recent cycles.
""")

    # make a size column that allows for enlarging recent points
    size = np.ones(len(dfr))
    sz = 0.5
    for i in range(len(size)):
        size[-1-i] = sz
        sz -= 0.1
        if sz < 0.05:
            sz = 0.05
    dfr['size'] = size

    # Make arrays to be used for creating custom hover text
    out_t = dfr.out_t.values
    entering_out_dt = dfr.entering_out_dt.values
    heat = dfr.heat.values
    flow = dfr.flow.values
    entering_t = dfr.entering_t.values
    heat_dt = dfr.heat_dt.values
    date_time_str = dfr.date_time_str.values
    cycle_minutes = dfr.cycle_minutes.values
    cop = dfr.cop.values
    power = dfr.power.values

    customdata = np.dstack((
        date_time_str,      # 0
        heat,               # 1     
        out_t,              # 2
        entering_out_dt,    # 3
        flow,               # 4
        entering_t,         # 5
        heat_dt,            # 6
        cycle_minutes,      # 7
        cop,                # 8
        power,              # 9
    ))[0]

    # Template for the hover text:
    hover_tmpl = """%{customdata[0]} <br>
Outdoor Temperature: %{customdata[2]:.1f} F <br>
COP: %{customdata[8]:.2f} <br>
Power: %{customdata[9]:,.0f} W <br>
Heat Output: %{customdata[1]:,.0f} BTU/hour <br>
Entering - Outside Temp: %{customdata[3]:.1f} F <br>
Flow: %{customdata[4]:.1f} gpm <br>
HP Entering Temp: %{customdata[5]:.1f} F <br>
HP Delta Temp: %{customdata[6]:.1f} F <br>
Cycle Length: %{customdata[7]:,.0f} minutes
"""
    fig = px.scatter(dfr, x='out_t', y='cop', 
        color='power', size='size',
        color_continuous_scale="Bluered_r")
    fig.update_layout(
        xaxis_title = 'Outdoor Temperature, deg F',
        yaxis_title = 'COP',
        coloraxis_colorbar_title_text = 'Compressor Power'
    )
    fig.update_traces(
        customdata=customdata,
        hovertemplate=hover_tmpl,
    )
    streamlit.plotly_chart(fig, use_container_width=True)

    streamlit.markdown('## COP vs. (Heat Pump Entering - Outdoor Temp)')

    fig = px.scatter(dfr, x='entering_out_dt', y='cop', 
        color='power', size='size', 
        color_continuous_scale="Bluered_r")
    fig.update_layout(
        xaxis_title = 'Heat Pump Entering - Outdoor Temperature, deg F',
        yaxis_title = 'COP',
        coloraxis_colorbar_title_text = 'Compressor Power'
    )
    fig.update_traces(
        customdata=customdata,
        hovertemplate=hover_tmpl,
    )
    streamlit.plotly_chart(fig, use_container_width=True)

    streamlit.markdown('## Raw Data')
    streamlit.write(dfr)
