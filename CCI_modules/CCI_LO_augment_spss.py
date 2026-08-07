import pandas as pd
import numpy as np
import datetime as dt
import sys, os
from pathlib import Path
import pyreadstat

import tkinter
from tkinter.filedialog import askopenfilename, asksaveasfilename, askdirectory

from CCI_modules.CCI_utils import (PATH_DATA_MAANED,  CCI_DEFINISJON, KJOPSINDEKS_DEFINISJON, SPSS_VARIABLE_MAPPING, SCORE_LABELS, QUESTION_TITLES,
                       SCALE_SCORES, MONTHS_LO, QUARTERS_LO,select_and_apply_scale, EXPECTED_VARIABLES_RAW, YYMM_LABELS, YYQ_LABELS)

def check_raw_variables(df):
    missing_vars = [v for v in EXPECTED_VARIABLES_RAW if v not in df.columns]
    if len(missing_vars)>0:
        print('\nWARNING: Missing variables:')
        print('\n'.join(missing_vars))
        input('Press Enter to continue')
    else:
        pass


def ask_coerce_dates_to_last_month(date_dt):
    # Setter minimumsdato til 1. dag i siste måned i datasett, slik at alle data tilordnes samme måned
    # For eksempel, hvis datasettet inneholder 29/11-5/12, endres 29-30/11 til 1/12.
    print('Datoer i datasett: ')
    print(date_dt.dt.date.value_counts().sort_index())
    year = date_dt.dt.year.max()
    month = date_dt.dt.month.max()
    min_date = pd.Timestamp(f"{year}-{month}-01")
    date_dt = date_dt.clip(lower=min_date)
    inp = input('Sett minimumsdato til {}? [y/n]: '.format(min_date.strftime('%Y-%m-%d')))
    if inp.upper() == 'Y':
        print('Endret datoer til:')
        print(date_dt.dt.date.value_counts().sort_index())
    return date_dt


# TRACKERVARIABLER
def tracker_variables(date_column):
    tracker = pd.DataFrame()
    tracker['date_dt'] = pd.to_datetime(date_column)
    
    if tracker['date_dt'].dt.month.nunique()> 1:
        tracker['date_dt'] = ask_coerce_dates_to_last_month(tracker['date_dt'])   

    tracker['mnd_num'] = tracker['date_dt'].dt.month
    tracker['kvartal_num'] = tracker['date_dt'].dt.quarter
    #tracker['year'] = tracker['date_dt'].dt.year
    yy = tracker['date_dt'].dt.year -2000
    tracker['yymm'] = (yy)*100+tracker['mnd_num']
    tracker['yyq'] = (yy)*10+tracker['kvartal_num']

    # Måned og kvartal til LO: Start i 2021
    tracker['År'] = tracker['date_dt'].dt.year
    temp_year_LO = tracker['År']-2021
    tracker['Måned'] = 12*temp_year_LO + tracker['mnd_num']
    tracker['Kvartal'] = 4*temp_year_LO + tracker['date_dt'].dt.quarter
    
    # Id format yyyymmxxxx, f.eks 2024080001
    tracker['unik_id'] = (tracker['yymm']*1E5 + tracker.index).astype(int)
    tracker['date_dt'] = tracker['date_dt'].dt.date

    print('\nGenerated tracker variables:')
    print(tracker)
    input('Press Enter to continue')
    return tracker


# INDEXVERDIER -100 TIL 100
def calculate_respondent_CCI_scores(df):
    # Beregner score -100, -50, 0, 50 100 for CCI-spørsmål, per respondent
    # Beregner CCI og Kjøpsindeks (gjennomsnitt av underliggende spørsmål)
    cci_questions = SPSS_VARIABLE_MAPPING.keys()
    dfm = select_and_apply_scale(df)[cci_questions]
    scores = dfm.map(lambda x: SCALE_SCORES[x])
    #
    temp = scores.rename(columns=SPSS_VARIABLE_MAPPING)
    scores['cci'] = temp[CCI_DEFINISJON].mean(axis=1)
    scores['kjopsindeks'] = temp[KJOPSINDEKS_DEFINISJON].mean(axis=1)
    scores.columns = scores.columns+'_score'
    print('\nCalculated CCI scores:')
    print(scores)
    return scores

# BAKGRUNNSVARIABLER
def get_recode_descriptions():
    """ Returnerer nøstet dict med 
            keys= rekodede variabler
            inner dict: {
                input: inputvariabel,
                d: mapping av verdier,
                labels: value labels for ny variabel
                }"""
    recode_descriptions = {
        'd7_ny': {
            # HUSHOLDNINGENS INNTEKT
            'input':'d7',
            'd' : ({k: 1 for k in [1,2,3,4]}    | # 1: Under 400 000
                   {k: 2 for k in [5,6,7]}      | # 2: 401 000 - 700 000
                   {k: 3 for k in [8,9,10]}     | # 3: 701 000 - 1 000 000
                   {k: 4 for k in [11]}         | # 4: Mer enn 1 000 000
                   {k: 4 for k in range(14,21)} | # 4: Mer enn 1 000 000
                   {k: 5 for k in[12,13]}         # 5: Ønsker ikke svare/vet ikke
                   ),
            'labels': {
                1: "Under 400 000 kr",
                2: "401–700 000 kr",
                3: "701–1 000 000 kr",
                4: "Mer enn 1 000 000 kr",
                5: "Vet ikke / ønsker ikke å svare"
            }
        },
        'd7b_ny': {
            # PERSONLIG INNTEKT
            'input':'d7b',
            'd' : {
                1: 1, 2: 1, 3: 1,           # 1,2,3     -> 1
                4: 2, 5: 2,                 # 4,5       -> 2
                6: 3, 7: 3,                 # 6,7       -> 3 
                8: 4, 9: 4, 10: 4, 11: 4,   # 8,9,10,11 -> 4
                12: 5                       # 12        -> 5 (ønsker ikke å svare)
            },
            'labels': {
                1: "Under 300 000 kr",
                2: "301–500 000 kr",
                3: "501–700 000 kr",
                4: "Mer enn 700 000 kr",
                5: "Ønsker ikke å svare"
            }
        },
        'd8_ny': {
            # HUSSTANDSLÅN
            'input':'d8',
            'd': {
                1: 1, 
                2: 2,
                3: 3,
                4: 4,
                5: 5, 6: 5, # 5,6 -> 5
                7: np.nan,  # Ikke sikker
                8: 6        # Har ikke lån
                },
            'labels': {
                1: "Under 0,5 mill. kroner", 
                2: "0,5–0,99 mill. kroner", 
                3: "1–1,49 mill. kroner", 
                4: "1,5–1,99 mill. kroner",
                5: "2 mill. kroner eller mer",
                6: "Har ikke lån"
            }
        },
        'D_ny1_ny': {
            # DAGLIG SITUASJON
            'input':'D_ny1',
            'd': {
                1: 1, 3: 1,         # 1,3 -> 1 (Heltid)
                2: 2,               # 2 -> 2 (Deltid)
                4: 3, 5: 3, 6: 3,   # 4,5,6 -> 3 (Permittert)
                7: 4,               # 7 -> 4 (Pensjonist)
                8: 5, 9: 5, 10: 5,  # 8,9,10 -> 5 (Arbeidssøkende/student/annet)
                11: 6               # Ønsker ikke å svare
            },
            'labels': {
                1: "Heltid",
                2: "Deltid",
                3: "Permittert",
                4: "Pensjonist",
                5: "Arbeidssøkende/student/annet",
                6: "Ønsker ikke svare"                
            }
        },
        'D_ny1_ny_II': {
            # DAGLIG SITUASJON (i jobb / ikke i jobb)
            'input': 'D_ny1',
            'd': {
                1: 1, 2: 1, 3: 1,  #  1 (I jobb)
                4: 2, 5: 2, 6: 2, 7: 2, 8: 2, 9: 2, 10: 2, 11: 2  #  2 (Ikke i jobb)
            },
            'labels': {
                1: "I jobb",  
                2: "Ikke i jobb"
            }
        },
        'd17_ny': {
            # TILSLUTNING
            'input':'d17',
            'd': {
                1: 1,
                2: 2, 3: 2, 4: 2, 5: 2,   #  2 (YS/Unio/Akademikerne/Frittstående)
                6: 3
            },
            'labels': {
                1: "LO",
                2: "YS/Unio/Akademikerne/Frittstående",
                3: "Ikke medlem"
            }
        },
        'Gxny7_ny':{
            # POLITISK AKSE
            'input': 'Gxny7',
            'd': {
                1: 1, 2: 1, 3: 1, 4: 1,  # 1,2,3,4  -> 1 (Venstre)
                5: 2, 6: 2,              # 5,6      -> 2 (Sentrum)
                7: 3, 8: 3, 9: 3, 10: 3, # 7,8,9,10 -> 3 (Høyre) 
                11: 4, 999: 4            # 11, 999  -> 4 (Vet ikke)
            },
            'labels': {
                1: 'Venstre',
                2: 'Sentrum',
                3: 'Høyre',
                4: 'Vet ikke'
            }
        }
    }
    return recode_descriptions


def get_col_labels_recoded_vars():
    # Column labels (Variable labels) for rekodede variabler
    labels = {
        'Alder':'Alder',
        'd7_ny':'Husstandsinntekt',
        'd7b_ny':'Personlig inntekt',
        'd8_ny':'Husstandslån',
        'D_ny1_ny': 'Daglig situasjon',
        'D_ny1_ny_II':'Daglig situasjon II',
        'd17_ny':'Tilslutning',
        'd17_ny_jobb':'Tilslutning II',
        'Gxny7_ny':'Politisk akse'
    }
    return pd.Series(labels)


def get_col_labels_update():
    # Column labels (Variable labels) for andre variabler
    labels = {
        'landsdel2020': 'Landsdeler 2020',
        'landsdel2024': 'Landsdel',
        'd6': 'Utdanning',
        'c15': 'Urbanitet',
        'd16': 'Partivalg',
        'd17': 'Tilslutning',
        'År': 'År',
        'Kvartal': 'Kvartal',
        'Måned': 'Måned',
        'mnd_num': 'Månedsnummer',
        'kvartal_num': 'Kvartalsnummer',
        'year': 'Year',
        'yymm': 'År_måned',
        'yyq': 'År_kvartal',
        'gender':'Kjønn',
    }
    return pd.Series(labels)


def recode_variables(df):
    # Henter mapping og nye labels for variabler som skal rekodes
    recode_description = get_recode_descriptions()
    recoded = pd.DataFrame(index=df.index)
    value_labels = pd.Series()
    for newvar, description in recode_description.items():
        input_var = description['input']
        if input_var in df.columns:
            # Mapping dictionary
            d = description['d']
            # Sjekker om input inneholder verdier som ikke er definert i mapping
            test = set(df[input_var])-set(d.keys())
            if len(test)>0:
                print('\nADVARSEL: Rekoding av variabler')
                print('\n{} inkluderer verdier som ikke er definert i mapping for {}. Beholder verdi fra input.'.format(input_var, newvar))
                print(test)
                input('Press Enter for å fortsette eller Ctrl-C for å avbryte.')
            recoded[newvar] = df[input_var].replace(d)
        else:
            print('\nADVARSEL: Variabel {} finnes ikke i input-data'.format(input_var))
            input('Press Enter for å fortsette eller Ctrl-C for å avbryte.')
            recoded[newvar] = np.nan
        # Labels for ny variabel
        value_labels[newvar] = description['labels']
    return recoded, value_labels



def get_age_groups(age_col):
    # Grupper numerisk alder i aldersgrupper. 
    # Inkluderer VENSTRE og ikke høyre endepunkt
    age_bins = [18, 30, 40, 50, 60, 111]
    age_groups = pd.cut(age_col, bins=age_bins, labels=np.arange(5)+1, right=False)
    labels = {
        1: 'Under 30 år', 
        2: '30–39 år', 
        3: '40–49 år', 
        4: '50–59 år', 
        5: '60 år +'
        }
    if (min(age_col)<min(age_bins))|(max(age_col)>=max(age_bins)):
        print('\nADVARSEL: Aldersgrupper\nInputdata inkluderer verdier utenfor definerte alderskategorier')
        print(age_col.apply([min,max]))
        input('Press Enter for å fortsette ellr Ctrl-C for å avbryte.')
    return age_groups, labels



def code_background_variables(df):
    # Rekoder variabler i henhold til recode_descriptions
    recoded, recoded_labels = recode_variables(df)

    # Aldersgrupper
    age_groups, age_labels = get_age_groups(df['age'])
    recoded['Alder'] = age_groups
    recoded_labels['Alder'] = age_labels

    # Organisasjonstilslutning kombinert med jobb
    # Hvis vi har data på spm om jobb: temp = 2,3,4 ut fra organisasjonstilknytning 
    # LO -> 2, Annen org -> 3, ikke organisert -> 4
    temp = pd.Series(index=recoded.index)
    mask = ~recoded['D_ny1_ny_II'].isna()
    temp[mask] = recoded.loc[mask, 'd17_ny']+1
    # Respondenter som er LO-medlem i jobb settes til 1
    LO_ijobb_mask = (recoded['d17_ny']==1) & (recoded['D_ny1_ny_II'] ==1)
    temp[LO_ijobb_mask] = 1
    recoded['d17_ny_jobb'] = temp

    recoded_labels['d17_ny_jobb'] = {
            1: 'LO-medlemmer, i jobb',
            2: 'LO-medlemmer, ikke i jobb',
            3: 'YS/Unio/Akademikerne/Frittstående',
            4: 'Ikke medlem'
        }

    print('\nRecoded variables')
    print(recoded)   
    input('Press Enter to continue')
    return recoded, recoded_labels


def get_variable_rename(df):
    # Endre til 2 siffer etter underscore i variabelsett Gxny2
    # Gxny2_d -> Gxny2_dd
    # Endre til liten q i variabelsett Q14b
    gx = df.filter(regex='^Gxny2_\d{1,2}$').columns.to_series()
    q14b = df.filter(regex='Q14b').columns.to_series()
    q14b = q14b.str.lower()
    if len(gx)>0:
        gx = gx.str.split('_', expand=True)
        gx[1] = gx[1].str.zfill(2)
        gx = gx.apply('_'.join, axis=1)
    var_rename = pd.concat([gx,q14b])
    if len(var_rename)>0:
        print('Renaming variables:')
        print(var_rename)
    var_rename['C15'] = 'c15'
    var_rename['C16'] = 'c16'
    var_rename['D16'] = 'd16'
    var_rename['Region'] = 'region'
    return var_rename




"""
def clean_column_labels(current_column_labels):
    labels = pd.Series(current_column_labels)
    # I variabelsett G2 og Gxny2: fjern tekst etter " - "
    split_labels = labels.filter(regex='^G2r|^Gxny2_').index
    labels[split_labels] = labels[split_labels].str.split(' - ', expand=True)[0]

    # Fjern ' …' fra labels
    labels = labels.str.replace(' …','')

    labels = labels.str.strip()
    return labels.to_dict()
"""
"""
def remove_columns(df):
    patterns = [
        '^H\d{1,2}', # Mobilitetsbarometeret
        'H_Ny\d_',  # Mobilitetsbarometeret
        'hid_H'   # Mobilitetsbarometeret
    ]
    dropcols = df.filter(regex='|'.join(patterns)).columns
    df = df.drop(columns=dropcols)
    return df
"""



def save_augmented_to_file(df, column_labels, value_labels, filename_stem):
    data_month =  df['date_dt'].max().strftime("%b%Y").upper()
    yymmdd = dt.datetime.now().strftime('%y%m%d')
    output_file = '{}_KODET_KOMPLETT_{}_{}.sav'.format(filename_stem, data_month, yymmdd)
    output_file = asksaveasfilename(initialdir=PATH_DATA_MAANED, initialfile=output_file)
    if output_file!='':
        pyreadstat.write_sav(df, output_file, column_labels=column_labels, variable_value_labels=value_labels)
        print('Lagret til {}'.format(output_file))
    return output_file


def augment_spss_CCI_LO(spss_file=''):
    if spss_file=='':
        spss_file = askopenfilename(initialdir=PATH_DATA_MAANED, filetypes=[('SAV','*.sav')])
    print(spss_file)
    spss_file = Path(spss_file)
    
    # Read data and get value labels and column labels
    df0, meta = pyreadstat.read_sav(spss_file)
    check_raw_variables(df0)

    df0 = df0.set_index('record')
    value_labels = pd.Series(meta.variable_value_labels)
    column_labels = pd.Series(meta.column_names_to_labels)
    print('\nRead data from file')
    print(df0)

    tracker = tracker_variables(df0['date'])
    cci_scores = calculate_respondent_CCI_scores(df0)
    recoded, value_labels_recoded_vars = code_background_variables(df0)

    # Create normalized weight (sums to 1000)
    df0['weight_normalized'] = df0['weight']*1000/df0['weight'].sum()
    print('\nBeregnet normalisert vekt (Sum 1000 per måned):')
    print(df0[['weight','weight_normalized']].apply([pd.Series.count, pd.Series.mean, pd.Series.sum]).T)
    input('Press Enter to continue')

    # Add tracker, recoded vars and CCI scores to data
    df1 = pd.concat([tracker, df0, recoded, cci_scores], axis=1)

    # Add value labels and column labels for recoded variables and scores
    value_labels = pd.concat([value_labels, value_labels_recoded_vars])
    value_labels['yymm'] = YYMM_LABELS
    value_labels['yyq'] = YYQ_LABELS
    column_labels = pd.concat([column_labels, get_col_labels_recoded_vars(), pd.Series(SCORE_LABELS)])

    # Fix Value Labels

    # Update column labels
    update_col_labels = get_col_labels_update()
    column_labels = update_col_labels.combine_first(column_labels)

    # Rename variables (in data and metadata)
    d = get_variable_rename(df1)
    df1 = df1.rename(columns=d)
    value_labels = value_labels.rename(d)
    column_labels = column_labels.rename(d)

    value_labels['Kvartal'] = QUARTERS_LO
    value_labels['Måned'] = MONTHS_LO

    # Prepare data and metadata to save
    df1 = df1.reset_index()
    value_labels = value_labels.to_dict()
    column_labels = column_labels.to_dict()
    
    print('\nEndelig datasett')
    print(df1)

    # Sjekk for dupliserte labels
    duplicated = df1.columns.str.lower().duplicated(keep=False)
    if duplicated.sum() > 0:
        print('\n\nADVARSEL: Dupliserte variabelnavn')
        print(df1.loc[:,duplicated])

    print('\nLAGRE TIL FIL\n')
    inp = input('\nLagre komplett datasett til fil? [y/n]: ')
    if inp.upper() !='N':
        output_file = save_augmented_to_file(df1,column_labels, value_labels, spss_file.stem)
    else:
        output_file=''
 
    return output_file, df1





def batch_augment_spss():
    dir = PATH_DATA_MAANED
    dir = askdirectory(initialdir=PATH_DATA_MAANED)
    files = os.listdir(dir)
    files = [f for f in files if f.endswith('.sav')]
    print(dir)
    print('\n'.join(files))
    input('Press Enter to process files')

    for file in files:
        file = Path(dir).joinpath(file)
        print(file)
        input('Press Enter to process file')

        d = augment_spss_CCI_LO(file)
        input('Press Enter to continue')



"""
file = askopenfilename(initialdir=PATH_RESULTATER, filetypes=[('SAV','*.sav')])
file = PATH_RESULTATER.joinpath('2024/2024 - 09/ONI127298_240917_weight_toPM.sav')
file = PATH_RESULTATER.joinpath('2024/2024 - 09/ONI127298_240917_weight_September_Kodet.sav')

# Ukodet septemberfil
file = 'C:/Users/NinaIrenHoven/Opinion AS/Opinion SharePoint - LO INRA/2024/01 Befolkningsundersøkelse 2024/09 September/SPSS-filer/ONI127298_240917_weight_toPM.sav'
file = 'C:/Users/NinaIrenHoven/Opinion AS/Opinion SharePoint - ForbrukerMeteret/Resultater/2024/2024 - 09/ONI127298_240917_weight_toPM.sav'

# CCI Master
file = 'C:/Users/NinaIrenHoven/Opinion AS/Opinion SharePoint - ForbrukerMeteret/DATA AKKUMULERT/spss_master/CCI_MASTER_240930.sav'

# Ukodet desember 2023
file = 'C:/Users/NinaIrenHoven/Opinion AS/Opinion SharePoint - ForbrukerMeteret/Resultater/2023/2023-12/ONL109506_231205_weight_toPM.sav'




df0, meta = pyreadstat.read_sav(file)
df0 = df0.set_index('record')
value_labels = meta.variable_value_labels
column_labels = meta.column_names_to_labels

data, c, v = code_background_variables(df0, value_labels)


today = dt.datetime.now().strftime('%y%m%d')
output_file = spss_file.parent.joinpath('{}_kodet_{}.sav'.format(spss_file.stem, today))
pyreadstat.write_sav(
    df0.reset_index(), 
    output_file, 
    column_labels=meta.column_names_to_labels,  
    variable_value_labels=meta.variable_value_labels
    )


file = 'C:/Users/NinaIrenHoven/Opinion AS/Opinion SharePoint - ForbrukerMeteret/DATA AKKUMULERT/spss_master/CCI_MASTER_240918.sav'

df0, meta = pyreadstat.read_sav(file)
df0 = df0.set_index('unik_id')

recoded, new_value_labels, new_column_labels = code_background_variables(df0)

output_file = Path(file).parent.joinpath('{}_bakgrunnn.sav'.format(Path(file).stem, 'bakgrunn'))
pyreadstat.write_sav(
recoded.reset_index(), 
output_file, 
column_labels=new_column_labels,  
variable_value_labels=new_value_labels,
)
    


dir = tkinter.filedialog.askdirectory()
dir = 'C:/Users/NinaIrenHoven/Opinion AS/Opinion SharePoint - ForbrukerMeteret/DATA AKKUMULERT/spss_master/for merge/2020'
dir = 'C:/Users/NinaIrenHoven/Opinion AS/Opinion SharePoint - ForbrukerMeteret/DATA AKKUMULERT/spss_master/for merge/2019'
files = os.listdir(dir)
print(files)
for file in files:
    file = Path(dir).joinpath(file)
    print(file)
    d = code_spss_main(file)
    input('Press Enter')

    """


#file = 'C:/Users/NinaIrenHoven/Opinion AS/Opinion SharePoint - ForbrukerMeteret/DATA AKKUMULERT/spss_master/for merge/2020/OND74219_200406_weight_ToPM.sav'