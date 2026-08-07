
import pandas as pd
import datetime as dt
import tkinter
from tkinter.filedialog import askopenfilename

from CCI_modules.CCI_LO_augment_spss import augment_spss_CCI_LO
from CCI_modules.CCI_LO_split_save_spss import split_and_save_files
from CCI_modules.CCI_merge_with_master import merge_with_master_data_main

from CCI_modules.CCI_utils import PATH_DATA_MAANED, PATH_DATA_MASTER

root = tkinter.Tk()
root.withdraw()

    
inp = input('Les inn og berike rådata? y/n: ')
if inp.upper() == 'Y':
    print('\nVELG FIL MED RÅDATA:\n')
    raadata_file = askopenfilename(title="Åpne månedlig SPSS-fil", initialdir=PATH_DATA_MAANED, filetypes=[('SAV','*.sav')])
    print(raadata_file)

    # Les inn månedlig spss-fil, kode bakgrunnsvariabler for CCI, LO, Mobilitetsbarometeret, lagre til ny fil
    augmented_file, df = augment_spss_CCI_LO(raadata_file)

else:
    print('\nVELG FIL MED FERDIG BERIKET MÅNEDLIG DATA:\n')
    augmented_file = askopenfilename(title='Åpne prosessert månedlig fil', initialdir=PATH_DATA_MAANED, filetypes=[('SAV','*.sav')])


# Lagre til CCI, LO, Mobilitetsbarometeret
files = split_and_save_files(augmented_file)


inp = input('\nMerge CCI-data med masterfil? y/n: ')
if inp.upper()=='Y':
    cci_master_file = askopenfilename(title="Åpne CCI Masterfil", initialdir=PATH_DATA_MASTER, filetypes=[('SAV','*.sav')])
    merge_with_master_data_main(files['CCI'], cci_master_file)

