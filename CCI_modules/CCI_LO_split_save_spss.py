import pandas as pd
import numpy as np
import datetime as dt
import sys, os
from pathlib import Path
import pyreadstat

import tkinter
from tkinter.filedialog import askopenfilename, asksaveasfilename

from CCI_modules.CCI_utils import (PATH_DATA_MAANED, PATH_LO, PATH_MOBI, LO_BAKGRUNN, MOBI_BAKGRUNN, CCI_VARIABLES)

def keep_cols(df, cols):
    cols_in_df = [c for c in cols if c in df.columns]
    cols_not_in_df = [c for c in cols if c not in df.columns]
    print('NB: noen variabler mangler i datasett:')
    print(cols_not_in_df)
    return cols_in_df

def save_file_CCI(df, output_file, column_labels, value_labels):
    vars = keep_cols(df, CCI_VARIABLES)
    df_out = df[vars]
    print(df_out)
    pyreadstat.write_sav(df_out, output_file, column_labels=column_labels, variable_value_labels=value_labels)
    print('Lagret til {}'.format(output_file))
    return df_out


def save_file_LO(df, output_file, column_labels, value_labels):
    #LO_questions = list(df.filter(regex='^G|^noanswerG').columns)
    LO_questions = list(df.filter(regex=r'^(G|QG|noanswerG|noanswerQG)').columns)
    LO_cols = LO_BAKGRUNN['foran'] + LO_questions + LO_BAKGRUNN['bak']
    LO_cols = keep_cols(df, LO_cols)
    df_out = df[LO_cols]
    print(df_out)
    pyreadstat.write_sav(df_out, output_file, column_labels=column_labels,  variable_value_labels=value_labels)
    print('Lagret til {}'.format(output_file))
    return df_out


def save_file_Mobi(df, output_file, column_labels, value_labels):
    mobi_questions = list(df.filter(regex='^H|^hid_H|^T').columns)
    mobi_cols = MOBI_BAKGRUNN['foran'] + mobi_questions + MOBI_BAKGRUNN['bak']
    mobi_cols = keep_cols(df, mobi_cols)
    df_out = df[mobi_cols]
    print(df_out)
    pyreadstat.write_sav(df_out, output_file, column_labels=column_labels, variable_value_labels=value_labels)
    print('Lagret til {}'.format(output_file))
    return df_out


def split_and_save_files(file = ''):
    #
    if file == '':
        file = askopenfilename(initialdir=PATH_DATA_MAANED, title='Velg kodet månedlig spss-fil' ,filetypes=[('SAV','*.sav')])
    #
    df_komplett, meta = pyreadstat.read_sav(file)    
    column_labels = meta.column_names_to_labels
    value_labels = meta.variable_value_labels
    #
    print('Lest data fra fil: {}\n'.format(file))
    print(df_komplett)
    #
    #file_stem = Path(file).stem.replace('KOMPLETT_','')
    file_stem = Path(file).stem.replace('KOMPLETT','*')
    files = {}
    #
    inp = input('\nLagre fil til CCI? [y/n]: ')
    if inp.upper() =='Y':
        #output_file = '{}_CCI.sav'.format(file_stem)
        output_file = file_stem.replace('*','CCI')+'.sav'
        output_file = asksaveasfilename(initialdir=PATH_DATA_MAANED, initialfile=output_file)
        if output_file!='':
            save_file_CCI(df_komplett, output_file, column_labels, value_labels)
            files['CCI'] = output_file
    #
    inp = input('\nLagre fil til LO? [y/n]: ')
    if inp.upper() =='Y':
        #output_file = '{}_LO.sav'.format(file_stem)
        output_file = file_stem.replace('*','LO')+'.sav'
        output_file = asksaveasfilename(initialdir=PATH_LO, initialfile=output_file)
        if output_file!='':
            save_file_LO(df_komplett, output_file, column_labels, value_labels)
            files['LO'] = output_file
    #
    inp = input('\nLagre fil til Mobilitetsbarometeret? [y/n]: ')
    if inp.upper() =='Y':
        #output_file = '{}_MOBI.sav'.format(file_stem)
        output_file = file_stem.replace('*','MOBI')+'.sav'
        output_file = asksaveasfilename(initialdir=PATH_MOBI, initialfile=output_file)
        if output_file!='':
            save_file_Mobi(df_komplett, output_file, column_labels, value_labels)
            files['Mobi'] = output_file
    #
    print('Filer:')
    print(files)
    return files

