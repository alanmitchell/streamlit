"""Streamlit app to visualize PCE Data by Community.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# Force app into a wider mode
st.markdown(
    f"""
    <style>
    .reportview-container .main .block-container{{
        max-width: 95%;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

@st.cache
def get_pce_data():
    """Reads PCE data into dataframe and returns it.
    """
    return pd.read_pickle(Path(__file__).parent / 'pce.pkl')

df = get_pce_data()

min_year, max_year = st.sidebar.slider(
    'Pick range of Years to Include',
    min_value=int(df.year.min()),
    max_value=int(df.year.max()),
    value=(2002, 2018)
)
st.sidebar.markdown(
    '*Note:* 2019 Data has not been scrubbed and contains errors.'
)

cities_all = list(df.city.unique())
cities_all.sort()
cities_nw = ('Ambler', 'Buckland', 'Deering', 'Kiana', 'Kivalina',
    'Kobuk', 'Kotzebue', 'Noatak', 'Noorvik', 'Selawik', 'Shungnak')

city_group = st.sidebar.selectbox('Select Community Group', ('All', 'NW Arctic'), 1)
cities = cities_all
if city_group == 'NW Arctic':
    cities = cities_nw

city = st.sidebar.selectbox(
    'Select Community to View',
    cities,
    )

st.sidebar.markdown('Data provided by the [Alaska Energy Authority](http://www.akenergyauthority.org/).')

st.markdown(f'# {city} Utility Data from PCE Reporting')

# Generation by Source

gen_cols = ['diesel_kwh', 'hydro_kwh', 'other1_kwh', 'other2_kwh']
df_selected = df.query('city==@city and year>=@min_year and year<=@max_year')[
        ['year', 'month', 'fuel_price', 'date','average_gen_kw', 'peak_consumption_kw'] + gen_cols
    ].copy()

df_melt = pd.melt(df_selected, id_vars=['year', 'month', 'date'], value_vars=gen_cols,
    var_name='generation', value_name='kWh')
df_annual = df_melt.groupby(['year', 'generation']).sum()
df_annual.reset_index(inplace=True)

st.markdown('## Annual Generation by Type')
st.write(
    px.line(df_annual, x='year', y='kWh', color='generation', width=900, height=500)
)

st.write(
    px.bar(df_annual, x='year', y='kWh', color='generation', width=900, height=500)
)

# Diesel Fuel Price

st.markdown('## Diesel Fuel Price, $/gallon')
st.write(
    px.line(df_selected, x='date', y='fuel_price',
                width=900, height=500)
)

# Monthly analysis of Other Generation Sources, often Wind
st.markdown('## Other Generation by Month')
st.write(
    px.line(df_melt.query('generation in ("other1_kwh", "other2_kwh")'),
        x='date', y='kWh', color='generation', width=900, height=500)
)
st.write(
    px.scatter(df_melt.query('generation in ("other1_kwh", "other2_kwh")'),
        x='month', y='kWh', color='generation', width=900, height=500)
)

# Peak and Average Generation
df_melt = pd.melt(df_selected, id_vars=['date'], value_vars=['peak_consumption_kw', 'average_gen_kw'],
    var_name='measure_type', value_name='kW')
st.markdown('## Peak and Average Generation')
st.write(
    px.line(df_melt, x='date', y='kW', color='measure_type', width=900, height=500)
)

st.markdown('# Compare Multiple Communities')

cities_to_graph = st.multiselect('Select Communities to Compare', cities, cities[:11])
fields = [fld for fld in df.columns if fld not in ('city', 'year', 'month', 'day', 'date')]
field_to_graph = st.selectbox('Select Variable to Graph', fields, fields.index('fuel_price'))
df_to_graph = df.query('city in @cities_to_graph and year>=@min_year and year<=@max_year')
if len(cities_to_graph) > 0:
    st.plotly_chart(
        px.line(df_to_graph, x='date', y=field_to_graph, color='city', height=600),
        use_container_width=True,
    )
else:
    st.error('You must choose at least one Community to graph.')
