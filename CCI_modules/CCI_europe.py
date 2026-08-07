import pandas as pd
import numpy as np
import datetime as dt
import os
from pathlib import Path
from urllib.request import urlretrieve
from tkinter.filedialog import askopenfilename, asksaveasfilename

from CCI_modules.CCI_utils import PATH_HISTORISKE_DATA, PATH_EU, VARNAME_MAPPING_NO, read_norway_historical_data, open_file_y_n


import webbrowser
"""
- Leser inn CCI-data fra EU-fil, månedlige og kvartalsvise spm
    https://economy-finance.ec.europa.eu/economic-forecast-and-surveys/business-and-consumer-surveys/download-business-and-consumer-survey-data/time-series_en
    Consumers - ‘Non-Seasonally Adjusted Data (total sector)’ 
- Leser inn CCI-data for Norge (egengenerert csv-fil)
- Kombinerer 3 datasett til ett
- Beregner gjennomsnitt for Norden
- skriver totalfil til CSV

"""




EU_FILE = PATH_EU.joinpath('consumer_total_nsa_nace2/consumer_total_nsa_nace2.xlsx')
#NORGE_FILE = PATH_HISTORISKE_DATA.joinpath('CCI_og_delindekser_Norge_akkumulert.csv')


def get_timestamp(filename):
    return dt.datetime.fromtimestamp(os.path.getmtime(filename)).strftime('%Y-%m-%d %H:%M:%S')


def generate_eu_url():
    timestamp = dt.date.today()-dt.timedelta(days=30)
    yy = timestamp.year-2000
    mm = timestamp.month
    url_template = "https://ec.europa.eu/economy_finance/db_indicators/surveys/documents/series/nace2_ecfin_{:02d}{:02d}/consumer_total_nsa_nace2.zip"
    return url_template.format(yy,mm)


def download_eu_data():
    eu_url = generate_eu_url()
    download_to = PATH_EU.joinpath("consumer_total_nsa_nace2.zip")
    print('URL EU-data: '+str(eu_url))
    inp = input('Last ned data fra {}? y/n: '.format(eu_url))
    if inp.upper() == 'Y':
        try:
            urlretrieve(eu_url, download_to)
            print('\nOppdatert fil consumer_total_nsa_nace2.zip lastet ned til {}'.format(PATH_EU))
        except:
            print('\nAutomatisk nedlasting feilet. \nLast ned Consumer - non seasonally adjusted data,  til {}'.format(PATH_EU))
            webbrowser.open("https://economy-finance.ec.europa.eu/economic-forecast-and-surveys/business-and-consumer-surveys/download-business-and-consumer-survey-data/time-series_en")
            os.startfile(PATH_EU)
        input('Unzip og trykk Enter for å fortsette.')
    return


def read_eu_data(filename):
    eu_monthly = pd.read_excel(filename, sheet_name="CONSUMER MONTHLY", index_col=0)
    eu_quarterly = pd.read_excel(filename, sheet_name="CONSUMER QUARTERLY", index_col=0)
    #
    # Lager date index for kvartalsdata fra "yyyy-Qx"
    pattern = '(?P<year>[0-9]{4})\-Q(?P<quarter>[0-9])'
    dates = eu_quarterly.index.str.extract(pattern).astype(int)
    dates['month'] = dates['quarter'].map({1:1, 2:4, 3:7, 4:10})
    dates['day'] = dates['month'].map({1:31,4:30,7:31,10:31})
    eu_quarterly.index = pd.to_datetime(dates[['year','month','day']])
    #
    eu_data = pd.concat([eu_monthly, eu_quarterly], axis=1)
    eu_data = eu_data.dropna(how='all', axis=1)
    print('\nEU:\nLest data fra fil: {}'.format(filename))
    print('Sist endret: {}\n'.format(get_timestamp(filename)))
    print('Siste rad: {}\n'.format(eu_data.index[eu_data.index.size-1].date()))
    return eu_data


def split_cols_to_multiindex(cols):
    # Finn country og spm.nr fra colonneheader. Eks: CONS.SE.TOT.COF.B.M, CONS.SE.TOT.1.B.M
    cols = cols.str.replace('CONS.','').str.replace('TOT.','')
    pattern = "(?P<country>[A-Z]{2})\.(?P<question>[\w]{1,3})"
    col_info = cols.str.extract(pattern)
    col_info['id'] = cols 
    return pd.MultiIndex.from_frame(col_info)


def calculate_COF_nordic(df):
    norden_vekt = {
        'NO': 0.23,
        'SE': 0.35,
        'DK': 0.23,
        'FI': 0.19
    }
    temp = df.xs('COF',level='question', axis=1)[norden_vekt.keys()]
    temp.columns = temp.columns.droplevel([1])
    COF_nordic = temp.mul(norden_vekt).sum(axis=1, skipna=False)
    df[('Nordic','COF','Nordic.COF')] = COF_nordic.round(4)
    return


def cci_europe_main():
    download_eu_data()
    norge_data = read_norway_historical_data(detailed=False)
    norge_data = norge_data[VARNAME_MAPPING_NO.keys()].rename(columns=VARNAME_MAPPING_NO)
    eu_data = read_eu_data(EU_FILE)
    data = pd.concat([eu_data, norge_data], axis=1)

    data.columns = split_cols_to_multiindex(data.columns)
    calculate_COF_nordic(data)
    keep_countries = ['EA','Nordic','NO','DK','FI','SE','PT','IT','EL','ES','DE','FR']
    data = data[keep_countries]

    # Flytte COF-kolonner til starten
    cof_mask = data.columns.get_level_values(1) =='COF'
    data = pd.concat([data.loc[:,cof_mask], data.loc[:,~cof_mask]], axis=1)

    print(data)
    data_summary = data.columns.to_frame().reset_index(drop=True).groupby('country')['question'].unique()
    print('\nCountries and questions/indices:')
    print(data_summary)
    
    # Prepare to save
    data.columns = data.columns.droplevel([0,1])
    #data.index = data.index.strftime('%m/%d/%Y')

    inp = input('\nSkriv samlet fil til csv? [y/n]:')
    if inp.lower() == 'y':
        output_data = data.copy()
        output_data.index = output_data.index.strftime('%m/%d/%Y')

        today = dt.datetime.now().strftime('%y%m%d')
        output_file = PATH_HISTORISKE_DATA.joinpath('cci_eu_og_norge_historisk_{}.csv'.format(today))
        try:
            output_data.to_csv(output_file, index_label='date')
            print('Saved to file: {}\n'.format(output_file))
        except PermissionError:
            print('Could not write to file: {}'.format(+output_file))
        open_file_y_n(output_file)
        
    return data


if __name__ == '__main__':
    data = cci_europe_main()

######################################
