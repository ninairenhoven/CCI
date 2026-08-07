
import pandas as pd
import datetime as dt
import tkinter
from tkinter.filedialog import askopenfilename, asksaveasfilename

#from CCI_modules.CCI_LO_augment_spss import augment_spss_CCI_LO
#from CCI_modules.CCI_LO_split_save_spss import split_and_save_files

from CCI_modules.CCI_utils import read_norway_historical_data, read_combined_historical_data
from CCI_modules.CCI_utils import PATH_DATA_MAANED, PATH_DATA_MASTER

from CCI_modules.CCI_Norge import cci_norge_maanedlig
#from CCI_modules.CCI_merge_with_master import merge_with_master_data_main
from CCI_modules.CCI_europe import cci_europe_main
from CCI_modules.CCI_excelrapporter import write_cci_reports
from CCI_modules.CCI_plotting import generate_plots


root = tkinter.Tk()
root.withdraw()

"""
spss_file = 'C:/Users/NinaIrenHoven/Opinion AS/Opinion SharePoint - ForbrukerMeteret/Resultater/2024/2024 - 09/ONI127298_240917_weight_September_Kodet.sav'
spss_file_coded = PATH_RESULTATER.joinpath('2024/2024 - 09/ONI127298_240917_weight_September_Kodet_kodet_240918.sav')
master_file = PATH_AKK_DATA.joinpath('spss_master/CCI_MASTER_Kodet_2021_til_dd.sav')

data_samlet = read_combined_historical_data()

"""


"""
raadata_file = askopenfilename(title="Åpne månedlig SPSS-fil", initialdir=PATH_DATA_MAANED, filetypes=[('SAV','*.sav')])
augmented_file, _ = augment_spss_CCI_LO(raadata_file)
files = split_and_save_files(augmented_file)
cci_file = files['CCI']

"""
    
print('\nVELG FIL MED MÅNEDLIG DATA:\n')
cci_file = askopenfilename(title="Åpne månedlig CCI SPSS-fil", initialdir=PATH_DATA_MAANED, filetypes=[('SAV','*.sav')])
print(cci_file)


"""# Åpne masterfil
print('\nMASTER DATA:')
cci_master_file = askopenfilename(title="Åpne CCI Masterfil", initialdir=PATH_DATA_MASTER, filetypes=[('SAV','*.sav')])
print(cci_master_file)


# Merge med Master, lagre ny  masterfil
print('Merger nye data med master')
merge_with_master_data_main(cci_file, cci_master_file)
"""

# Månedlig prosess Norge
print('Behandler månedlig data norge')
df, month, scores = cci_norge_maanedlig(cci_file)


# Les inn og behandle EU-data
print('\nCCI EU-DATA\n')
akk_data_eu_og_norge = cci_europe_main()


print('\nSKRIVER RAPPORTER\n')
data_norge_detalj = read_norway_historical_data()
write_cci_reports(akk_data_eu_og_norge, data_norge_detalj)


print('\nLAGER PLOTS\n')
data_norge_net = read_norway_historical_data(detailed=False)
generate_plots(data_norge_net, akk_data_eu_og_norge)