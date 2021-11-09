"""Heat Pump Utility Rebate Economics Calculator.
"""

import streamlit as st

import locale
import numpy as np
import numpy_financial as npf

from ipywidgets import interact, FloatSlider
import ipywidgets as widgets

# import matplotlib pyplot commands
from matplotlib.ticker import FuncFormatter
from matplotlib.ticker import MultipleLocator, FormatStrFormatter
import matplotlib.pyplot as plt 

plt.rcParams['figure.figsize']= (10, 8)   # set Chart Size
plt.rcParams['font.size'] = 14            # set Font size in Chart

# 'style' the plot like fivethirtyeight.com website
plt.style.use('bmh')

def make_pattern(esc, life):
    pat = np.ones(life - 1) * (1 + esc)
    return np.insert(pat.cumprod(), 0, [0.0, 1.0])

def as_currency(amount, pos=None):
    if amount >= 0:
        return '${:,.0f}'.format(amount)
    else:
        return '(${:,.0f})'.format(-amount)

plt.rc('ytick',labelsize=16)
shared_ax = None
def cash_graph(cash_flow, plot_num, title, discount_rate):
    global shared_ax
    
    y_formatter = FuncFormatter(as_currency)

    width = 0.35
    if plot_num==1:
        shared_ax = plt.subplot(310 + plot_num)
        shared_ax.get_xaxis().set_ticks([])
        shared_ax.yaxis.set_major_formatter(y_formatter)
    else:
        ax = plt.subplot(310 + plot_num, sharey=shared_ax)
        ax.yaxis.set_major_formatter(y_formatter)
        if plot_num != 3:
            ax.get_xaxis().set_ticks([])
    if plot_num == 3:
        plt.xlabel('Year')
    plt.bar(np.arange(len(cash_flow)) - width*0.5, cash_flow, width)
    plt.xlim(-0.3, 14.5)
    plt.title(title, fontsize=26)
    
    # determine IRR
    try:
        irr = '{:.1%}'.format(npf.irr(cash_flow))   # in %
    except:
        irr = ''
    # Net Present Value
    npv = as_currency(npf.npv(discount_rate, cash_flow))
    plt.annotate(
        'Net Present Value: %s\nInternal Rate of Return: %s' % (npv, irr),
         xy=(0.4, 0.25),
        xycoords='axes fraction',
        fontsize=24,
        color='green'
    )

def model(
    hp_cost, 
    gal_saved, 
    hp_cop, 
    oil_price, 
    oil_esc, 
    elec_price, 
    util_rebate, 
    util_admin_cost,
    life,
    oil_effic,
    elec_esc, 
    elec_prod_hp,
    elec_prod_esc,
    t_d_losses,
    discount_rate,
    sales_tax
    ):

    # Oil heating system kWh per MMBtu of heat delivered.  Boiler is about 2, 
    # Toyotove 4, furnace 5 - 9 kWh/MMBtu.
    # This will be used to calculated kWh avoided due to reduced oil heating 
    # system use.
    kwh_per_mmbtu = 4.0   

    elec_pat = make_pattern(elec_esc, life)
    elec_prod_pat = make_pattern(elec_prod_esc, life)
    oil_pat = make_pattern(oil_esc, life)

    # Heat Pump Impacts
    cash = np.zeros(life + 1)
    cash += oil_pat * gal_saved * oil_price * (1 + sales_tax)
    hp_kwh = gal_saved * 135000 * oil_effic / 3412. / hp_cop
    avoided_kwh = gal_saved * 135000 * oil_effic / 1e6 * kwh_per_mmbtu
    net_kwh = hp_kwh - avoided_kwh
    print(hp_kwh, avoided_kwh, net_kwh, 'kWh')
    cash += -elec_pat * elec_price * net_kwh * (1 + sales_tax)
    cash[0] += -hp_cost * (1 + sales_tax) + util_rebate

    # Utility Cash Flow
    cash_util = np.zeros(life + 1)
    cash_util += net_kwh * elec_price * elec_pat
    cash_util += -net_kwh / (1.0 - t_d_losses) * elec_prod_hp * elec_prod_pat
    cash_util[0] += -util_rebate - util_admin_cost

    #print(cash)
    #print(cash_util)

    plt.figure(figsize=(12,12))
    cash_graph(cash,  1, 'Heat Pump Customer Cash Flow', discount_rate)
    cash_graph(cash_util, 2, 'Utility Cash Flow', discount_rate)
    cash_graph(cash + cash_util, 3, 'Heat Pump Customer + Utility Cash Flow', discount_rate)

    plt.tight_layout()
    return plt.gcf()

def run():
    st.markdown('''
# Heat Pump Utility Rebate Economics Calculator
    ''')

    col1, col2, col3 = st.columns([3, 1, 3])

    with col1:
        install_cost = st.slider('Heat Pump Total Installed Cost', 1500, 6000, 3600, 200, format='$%.0f')
        oil_gal_saved = st.slider('Oil Gallons saved per year', 100, 800, 400, 50)
        oil_price = st.slider('Fuel Oil Price, $/gallon', 2., 5., 3., 0.1, format='$%.2f')
        elec_price = st.slider('Retail Electric Price', 0.13, 0.25, 0.18, .005, format='$%.3f')

    with col3:
        rebate = st.slider('Utility Rebate for Heat Pump', 0.0, 5000.0, 1700.0, 100.0, format='$%.0f')
        rebate_admin_cost = st.slider('Utility Admin Cost per Rebate', 100.0, 300.0, 200.0, 10.0, format='$%.0f')
        oil_price_esc = st.slider('Fuel Oil Price Escalation, % per year', -1.0, 5.0, 3.0, 0.05, format='%.2f%%')
        with st.expander('Advanced Inputs'):
            hp_cop = st.slider('Heat Pump COP', 2.0, 3.5, 2.5, 0.05)
            hp_life = st.slider('Heat Pump Life, years', 10, 20, 14, 1)
            oil_effic = st.slider('Oil Heater Efficiency', 70.0, 90.0, 80.0, 1.0, format='%.0f%%')
            elec_retail_esc = st.slider('Retail Electric Price Escalation, %/year', 0.0, 5.0, 2.3, 0.1, format='%.1f%%')
            elec_prod_cost = st.slider('Marginal Electricity Production Cost, $/kWh', 0.06, 0.15, 0.10, 0.005, format='$%.3f')
            elec_prod_esc = st.slider('Production Cost Escalation, %/year', 0.0, 5.0, 2.5, 0.1, format='%.1f%%')
            t_d_losses = st.slider('Transmission and Distribution Losses, %', 3.0, 8.0, 6.0, 0.1, format='%.1f%%')
            disc_rate = st.slider('Discount Rate, nominal, %', 3.0, 10.0, 5.0, 0.1, format='%.1f%%')
            sales_tax = st.slider('Sales Tax, %', 0.0, 10.0, 7.0, 0.1, format='%.1f%%')

    graph = model(
        install_cost, 
        oil_gal_saved, 
        hp_cop, 
        oil_price, 
        oil_price_esc/100.0, 
        elec_price, 
        rebate, 
        rebate_admin_cost,
        hp_life,
        oil_effic/100.0,
        elec_retail_esc/100.0,
        elec_prod_cost,
        elec_prod_esc/100.0,
        t_d_losses/100.0,
        disc_rate/100.0,
        sales_tax/100.0,
        )
    st.pyplot(graph)

