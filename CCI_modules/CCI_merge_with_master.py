import pandas as pd
import numpy as np
import datetime as dt
import sys, os
from pathlib import Path
import pyreadstat

import tkinter
from tkinter.filedialog import askopenfilename, asksaveasfilename

from CCI_modules.CCI_utils import PATH_DATA_MAANED, PATH_DATA_MASTER

def keep_variables(df, keep_vars):
    keep = [v for v in df.columns if v in keep_vars]
    return df[keep]


def stack_value_labels(value_labels_dict):
    return pd.Series(value_labels_dict).apply(pd.Series).stack()
    
    
def compare_value_labels(labels, master_labels, ignore_empty=True, ignore_vars=[]):
    # ignore_empty -> sammenligner kun variabler som har labels i begge datasett
    # ignore_vars -> ignorerer spesifikke variabler
    labels = stack_value_labels(labels)
    master_labels = stack_value_labels(master_labels)
    if ignore_empty:
        keep_vars = [v for v in labels.index.levels[0] if v in master_labels.index.levels[0]]
        master_labels = master_labels.loc[keep_vars]
    labels = labels.reindex_like(master_labels)
    comparison = labels.compare(master_labels).drop(ignore_vars, errors='ignore')
    print("self: nye data\nother: master")
    print(comparison)
    input('Press Enter to continue')
    return comparison


def compare_column_labels(labels, master_labels, ignore_case=True, ignore_vars=[]):
    labels = pd.Series(labels)
    master_labels = pd.Series(master_labels).drop(ignore_vars, errors='ignore')
    if ignore_case:
        labels = labels.str.lower()
        master_labels = master_labels.str.lower()
    labels = labels.reindex_like(master_labels)
    comparison = labels.compare(master_labels)
    print(comparison)
    input('Press Enter to continue')
    return comparison


def check_months(df, master, month_labels={}):
    new_data_months = df['yymm'].value_counts().rename(month_labels)
    master_months = master['yymm'].value_counts().sort_index().rename(month_labels)
    print('\nMaster data:')
    print(master_months)
    print('\nNye data:')
    print(new_data_months)
    if new_data_months.index.size > 1:
        print('\nNB! Mer enn én måned i nye data')
        input('Press Enter to continue')
    if new_data_months.index in list(master_months.index):
        print('\nNB! Måned finnes allerede i master data')
        input('Press Enter to continue')
    return


def merge_with_master_data_main(new_file='', master_file=''):
    if new_file=='':
        new_file = askopenfilename(initialdir=PATH_DATA_MAANED, title='Velg kodet månedlig spss-fil' ,filetypes=[('SAV','*.sav')])
    new_file = Path(new_file)
    print(new_file)

    if master_file=='':
        master_file = askopenfilename(initialdir=PATH_DATA_MASTER, title='Velg masterfil', filetypes=[('SAV','*.sav')])
    master_file = Path(master_file)
    print(master_file)

    new_data, new_meta = pyreadstat.read_sav(new_file)
    print(new_data)

    master_data, master_meta = pyreadstat.read_sav(master_file)
    print(master_data)

    missing_columns = [c for c in master_data.columns if c not in new_data.columns]
    if len(missing_columns)>0:
        print('\n\nADVARSEL Mangler variabler i nye data:')
        print(missing_columns)
        input('Press Enter to continue')

    new_value_labels = new_meta.variable_value_labels
    master_value_labels = master_meta.variable_value_labels
    print('\nCOMPARE VALUE LABELS')
    c = compare_value_labels(new_value_labels, master_value_labels, ignore_vars=missing_columns)

    new_column_labels = new_meta.column_names_to_labels
    master_column_labels = master_meta.column_names_to_labels
    print('\nCOMPARE VARIABLE LABELS')
    c = compare_column_labels(new_column_labels, master_column_labels, ignore_vars=missing_columns)

    for c in ['yymm','yyq']:
        add_labels = {k:v for k,v in new_value_labels[c].items() if k not in master_value_labels[c]}
        if len(add_labels)>0:
            print('\n'+c+ ': Legger til labels i master')
            print(add_labels)
        master_value_labels[c] = master_value_labels[c]|add_labels
        input('Press Enter to continue')

    mnd_labels = master_value_labels['yymm']
    check_months(new_data, master_data, mnd_labels)
       
    new_data = new_data.reindex(columns=master_data.columns)
    accumulated_data = pd.concat([master_data, new_data], axis=0)
    print(accumulated_data)

    today = dt.datetime.now().strftime('%y%m%d')
    output_file = 'CCI_MASTER_{}.sav'.format(today)
    output_file = asksaveasfilename(initialdir=master_file.parent, initialfile=output_file)

    #try:
    pyreadstat.write_sav(
        accumulated_data, 
        output_file, 
        column_labels=master_column_labels, 
        variable_value_labels=master_value_labels,
        )
    print('Lagret til {}'.format(output_file))
    #except:
    #    print('Kan ikke lagre til {}'.format(output_file))
    
    inp = input('Lagre siste måneds data for Crunch-append? y/n: ')
    if inp.upper() =='Y':
        wave_rows = new_data['unik_id']
        wave_data = accumulated_data.set_index('unik_id').loc[wave_rows]
        wave_data = wave_data.reset_index()
        wave_file = new_file.stem + '_CRUNCH_APPEND.sav'
        wave_file = asksaveasfilename(initialdir=new_file.parent, initialfile=wave_file)

        try:
            pyreadstat.write_sav(
                wave_data, 
                wave_file, 
                column_labels=master_column_labels, 
                variable_value_labels=master_value_labels,
                )
            print('Lagret til {}'.format(wave_file))
        except:
            print('Kan ikke lagre til {}'.format(wave_file))




###################################################################
"""

def normalize_weights(master_data):
    data = master_data.set_index('unik_id')[['yymm','weight']].copy()
    summed_weights = data.groupby('yymm')['weight'].sum()
    #vc = data['yymm'].value_counts().sort_index()
    data['summed_weight'] = data['yymm'].map(summed_weights)
    data['weight_normalized'] = data['weight']/data['summed_weight']*1000
    print(data.groupby('yymm')['weight_normalized'].sum())
    return data
"""

"""
output_file = Path(master_file).parent.joinpath('CCI_MASTER_norm_weight.sav')
pyreadstat.write_sav(
    w['weight_normalized'].reset_index(), 
    output_file
    )

master_file = 
new_file = 'C:/Users/NinaIrenHoven/Opinion AS/Opinion SharePoint - LO INRA/2024/01 Befolkningsundersøkelse 2024/09 September/SPSS-filer/ONI127298_240917_weight_toPM_kodet_240930.sav'
    


dir = 'C:/Users/NinaIrenHoven/Opinion AS/Opinion SharePoint - ForbrukerMeteret/DATA AKKUMULERT/spss_master/for merge/2020/kodet'
files = os.listdir(dir)
print(files)
master_file = 'C:/Users/NinaIrenHoven/Opinion AS/Opinion SharePoint - ForbrukerMeteret/DATA AKKUMULERT/spss_master/CCI_MASTER_240930.sav'

for file in files:
    file = Path(dir).joinpath(file)
    print(file)
    print()
    merge_spss_data_main(file, master_file)



"""


