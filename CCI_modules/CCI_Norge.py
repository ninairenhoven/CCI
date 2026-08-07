from re import S
import pandas as pd
import numpy as np
import datetime as dt
from pandas.tseries.offsets import MonthEnd
import sys, os
from pathlib import Path
import pyreadstat

import tkinter
from tkinter.filedialog import askopenfilename, asksaveasfilename

from CCI_modules.CCI_utils import (PATH_HISTORISKE_DATA, PATH_DATA_MAANED,
    CCI_DEFINISJON, KJOPSINDEKS_DEFINISJON, 
    SPSS_VARIABLE_MAPPING, 
    select_and_apply_scale,
    open_file_y_n)


#def apply_scale_mapping(df):
#    # Mapper tallsvar til Most positive/positive/negative/most negative i henhold til koding i spss
#    mapped = df.copy()
#    for scale, questions in SCALE_SELECTION.items():
#        mapped[questions] = df[questions].replace(SCALE_MAPPING[scale])
#    return mapped


def calculate_question_scores(df, var, weight_var):
    # Returns weighted scores (up, down, net) for a single variable
    weighted_counts = df.groupby(var)[weight_var].sum()
    pct = 100*weighted_counts/weighted_counts.sum()
    pct = pct.reindex(['PP','P','M','MM']).fillna(0)
    #
    pos = (pct['PP']+0.5*pct['P']).round(4)
    neg = (pct['MM']+0.5*pct['M']).round(4)
    net = (pos-neg).round(4)
    s = pd.Series({'up':pos,'down':neg,'net':net})
    return s 


def compute_scores(df):
    print('Computing scores.')
    scores = pd.DataFrame(dtype=float, columns=['up','down','net'])
    #
    # Beregner net score for aktuelle spørsmål
    for spss_var, param_name in SPSS_VARIABLE_MAPPING.items():
        #print('{} -> {}'.format(spss_var, param_name))
        s = calculate_question_scores(df, spss_var, 'weight')
        scores.loc[param_name] = s
    #
    scores.loc['CCI', 'net'] = scores.loc[CCI_DEFINISJON].mean()['net']
    scores.loc['Kjopsindeksen', 'net'] = scores.loc[KJOPSINDEKS_DEFINISJON].mean()['net']
    #
    return scores


def append_to_historical_data(scores, month, historikk_fil):
    #last_day_of_month = (month+MonthEnd(0)).strftime('%d/%m/%Y')
    #month_str = month.strftime('%Y/%m')
    last_day_of_month = (month+MonthEnd(0)).strftime('%d/%m/%Y')
    #
    # Get columns from historical data
    temp = pd.read_csv(historikk_fil, index_col=0, header=[0,1])
    csv_header = temp.columns
    prev_index = temp.index
    #
    if last_day_of_month in prev_index:
        print('\nADVARSEL: {} finnes allerede i historiske data.'.format(last_day_of_month))
        input('Press Enter to continue\n')
    #
    # Reindex new data to align with historical data
    s = scores.stack().reindex(index=csv_header).round(2)
    #s.name =  month_str
    s.name = last_day_of_month
    row = s.to_frame().T
    #
    try:
        row.to_csv(historikk_fil, mode='a',header=False)
        print('Saved to file: '+historikk_fil)
    except:
        print('Kan ikke skrive til fil '+historikk_fil)
    return


def cci_norge_maanedlig(spss_file=''):
    if spss_file == '':
        root = tkinter.Tk()
        root.withdraw()
        spss_file = askopenfilename(title="Åpne månedlig SPSS-fil", initialdir=PATH_DATA_MAANED, filetypes=[('SAV','*.sav')])
    # spss_file = CCI_path + 'spss-filer/ONJ93334_221018_weight_toPM_Kodet_1.sav'
    print(spss_file)
    questions =list(SPSS_VARIABLE_MAPPING.keys())
    usecols = ['record', 'date','weight'] + questions
    df, _ = pyreadstat.read_sav(spss_file, usecols=usecols)
    #dfm = apply_scale_mapping(df)
    dfm = select_and_apply_scale(df)

    scores = compute_scores(dfm)

    print('CCI resultater:')
    print(scores)

    # Leser ut aktuell måned fra datasettet
    months_in_data = pd.to_datetime(df['date']).dt.to_period('M').unique()
    if len(months_in_data)>1:
        print('\nADVARSEL: Mer enn én måned i datasett. Velger siste måned.')
        print(months_in_data)

    month = max(months_in_data)
    print('\nMÅNED: {}'.format(month))
    
    inp = input('\nSkriv (append) net scores til fil med historiske data? [y/n]: ')
    if inp.lower() == 'y':
        historikk_fil = askopenfilename(title='Velg fil med historiske data for Norge', initialdir=PATH_HISTORISKE_DATA, filetypes=(('csv','CCI_og_delindekser_Norge_akkumulert.csv'),))
        append_to_historical_data(scores, month, historikk_fil)      
        open_file_y_n(historikk_fil)
    
    return df, month, scores



#if __name__ == '__main__':
#    df, month, scores = cci_norge_maanedlig()

#######################################
# På akkumulert fil
"""
def scores_from_spss_master():
    spss_file = 'C:/Users/NinaIrenHoven/Opinion AS/Opinion SharePoint - ForbrukerMeteret/DATA AKKUMULERT/spss_akk_2021-dd/CCI_MASTER_Kodet_2021_til_dd.sav'

    questions =list(SPSS_VARIABLE_MAPPING.keys())
    usecols = ['record', 'date','weight','MND', 'year','mnd_num'] + questions
    df, meta = pyreadstat.read_sav(spss_file, usecols=usecols)
    mnd_labels = meta.variable_value_labels['MND']

    df['MND'].value_counts().sort_index().rename(mnd_labels)
    df.groupby('MND')['date'].agg(['min','max']).rename(mnd_labels)

    # Create month_dt column with the last day of the month
    temp_dates = df[['year', 'mnd_num']].assign(day=1).rename(columns={'mnd_num':'month'})
    df['month_dt'] = pd.to_datetime(temp_dates) + pd.offsets.MonthEnd(0)
    df.groupby('MND')['month_dt'].unique().rename(mnd_labels)

    #dfm = apply_scale_mapping(df)
    dfm = select_and_apply_scale(df)

    # Calculate score per month
    scores = dfm.groupby('month_dt').apply(compute_scores, include_groups=False)
    scores = scores.unstack(level=1)
    scores = scores.swaplevel(1,0, axis=1)

    historikk_fil = 'C:/Users/NinaIrenHoven/Opinion AS/Opinion SharePoint - ForbrukerMeteret/DATA AKKUMULERT/historiske data eu og norge/CCI_og_delindekser_Norge_akkumulert.csv'
    temp = pd.read_csv(historikk_fil, index_col=0, header=[0,1])        
    csv_header = temp.columns

    scores = scores.reindex(columns=csv_header).round(2)
    scores.to_csv(historikk_fil, mode='a',header=True)
    """