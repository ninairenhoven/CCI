from tkinter.filedialog import askopenfilename, asksaveasfilename
from CCI_europe import PATH_HISTORISKE_DATA
import pandas as pd
import datetime as dt
import streamlit as st

year_month  =  dt.date.today().strftime('%Y_%m')

norge_historisk = askopenfilename(title='Åpne historisk fil Norge', initialdir=PATH_HISTORISKE_DATA, filetypes=(('csv','CCI_Norge*.csv'),))
data = pd.read_csv(norge_historisk, index_col=0)
dropcols = ['Boligpriser_naa', 'Boligpriser_12mnd', 'Renter_naa', 'Store_kjop_naa']
data = data.drop(columns=dropcols)
data = data.reset_index().rename(columns={'index':'date'})

s = ', '.join(data.columns)

st.write(s)


