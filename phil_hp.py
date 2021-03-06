import streamlit
import pandas as pd
import numpy as np
import plotly.express as px
import bmondata
from dateutil.parser import parse
from datetime import datetime

# A list of date ranges to exclude from the cycle analysis.  If the midpoint of the cycle
# falls in any one of the following ranges, it is not included.
DATES_TO_REMOVE = (
    ('2020-09-18 16:00', '2020-09-18 17:00'),
    ('2020-09-20 07:00', '2020-09-20 23:59'),
    ('2020-09-22 07:30', '2020-09-22 08:00'),
    ('2020-09-22 11:00', '2020-09-22 11:30'),
    ('2020-09-28 20:00', '2020-09-28 21:00'),
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
        df_pwr['on'] = df_pwr.power > 130.0
        df_pwr['on_shift'] = df_pwr.on.shift()
        df_pwr['cycle_boundary'] = df_pwr.on != df_pwr.on_shift
        # set first value to false
        vals = df_pwr['cycle_boundary'].values
        vals[0] =  False
        df_pwr['cycle_boundary'] = vals
        # df_pwr.loc[df.index[0], 'cycle_boundary'] = False   # did not work due to duplicate index DST

        df_bound = df_pwr.query('cycle_boundary == True')
        st = 0 if df_bound.on[0] == True else 1
        en = None if df_bound.on[-1] == False else -1
        cycles = df_bound.index.values[st:en].reshape((-1,2))

        recs = []
        for cycle_st, cycle_en in cycles:
            # Create two query expressions, one that captures the cycle as defined by the
            # electrical power cycle, but another "extended" cycle that adds 5 minutes to the 
            # cycle to capture any residual heat that occurs at the end of the cycle.  Use
            # the extended cycle to calculate the COP.
            query_expr = '@cycle_st <= index < @cycle_en'
            cycle_en_ext = cycle_en + np.timedelta64(5, 'm')       # extended cycle has end time 3 minutes later
            query_expr_ext = '@cycle_st <= index < @cycle_en_ext'

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
            
            # get dataframes for both the regular cycle and the extended cycle
            df_pwr_cycle_ext = df_pwr.query(query_expr_ext)
            df_pwr_cycle = df_pwr_cycle_ext.query(query_expr)    # faster to do this query on the shortened data set
            df_cycle_ext = df.query(query_expr_ext)
            df_cycle = df_cycle_ext.query(query_expr)
            df_cycle_mean = df_cycle.mean()

            rec['power'] = df_pwr_cycle.power.mean()

            for fld in ('heat', 'flow', 'entering_t', 'leaving_t', 'out_t'):
                rec[fld] = df_cycle_mean[fld]
            rec['heat_dt'] = rec['leaving_t'] - rec['entering_t']
            rec['entering_out_dt'] = rec['entering_t'] - rec['out_t']
            # Use extended cycle for the COP calculation
            rec['cop'] = df_cycle_ext.heat.mean() / df_pwr_cycle_ext.power.mean() / 3.413
            rec['age'] = (datetime.now() - date_time).total_seconds()/(3600.*24.)   # age of cycle in days

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
    age = dfr.age.values

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
        age,                # 10
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
Cycle Length: %{customdata[7]:,.0f} minutes<br>
Age: %{customdata[10]:,.1f} days ago
"""

    # checkbox to determine if dot size is varied
    vary_size = streamlit.checkbox('Mark Recent Cycles with Large Dots?', True)
    # Show zero on Y-Axis
    show_zero = streamlit.checkbox('Show COP=0 on Vertical Axis?', True)

    # dropdown to select the variable to use for the color
    color_vars = dict(
        power='Compressor Power',
        cycle_minutes='Cycle Length',
        flow='Flow Rate',
        age='Cycle Age (days ago)'
    )
    color_var = streamlit.selectbox(
        'Select Variable to use for Dot Color',
        list(color_vars.keys()), 
        0, color_vars.get,
    )
    if vary_size:
        fig = px.scatter(dfr, x='out_t', y='cop', 
            color=color_var, size='size',
            color_continuous_scale="Bluered_r")
    else:
        fig = px.scatter(dfr, x='out_t', y='cop', 
            color=color_var,
            color_continuous_scale="Bluered_r")

    fig.update_layout(
        xaxis_title = 'Outdoor Temperature, deg F',
        yaxis_title = 'COP',
        coloraxis_colorbar_title_text = color_vars[color_var]
    )

    if show_zero:
        fig.update_yaxes(rangemode="tozero")

    fig.update_traces(
        customdata=customdata,
        hovertemplate=hover_tmpl,
    )
    streamlit.plotly_chart(fig, use_container_width=True)

    streamlit.markdown('''## COP vs. Temperature Lift
Heat Pump Entering Temperature - Outdoor Temperature
''')

    if vary_size:
        fig = px.scatter(dfr, x='entering_out_dt', y='cop', 
            color=color_var, size='size', 
            color_continuous_scale="Bluered_r")
    else:
        fig = px.scatter(dfr, x='entering_out_dt', y='cop', 
            color=color_var,
            color_continuous_scale="Bluered_r")

    fig.update_layout(
        xaxis_title = 'Heat Pump Entering - Outdoor Temperature, deg F',
        yaxis_title = 'COP',
        coloraxis_colorbar_title_text = color_vars[color_var]
    )

    if show_zero:
        fig.update_yaxes(rangemode="tozero")

    fig.update_traces(
        customdata=customdata,
        hovertemplate=hover_tmpl,
    )
    streamlit.plotly_chart(fig, use_container_width=True)

    if streamlit.checkbox('Show Raw Data?'):
        streamlit.write(dfr)

if __name__ == '__main__':
    run()
