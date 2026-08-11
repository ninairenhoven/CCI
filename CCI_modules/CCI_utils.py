from pathlib import Path
import pandas as pd
from tkinter.filedialog import askopenfilename, asksaveasfilename
import os


user_path = Path.home()
PATH_CCI = user_path.joinpath("Opinion AS/Opinion SharePoint - ForbrukerMeteret/")

PATH_DATA  = PATH_CCI.joinpath('01 Data')
PATH_GENERERTE_FILER = PATH_CCI.joinpath('02 Tabeller')
PATH_PLOTS = PATH_CCI.joinpath('03 Plots')

PATH_DATA_MAANED = PATH_DATA.joinpath('Månedlige SPSS-filer')
PATH_DATA_MASTER = PATH_DATA.joinpath('CCI Master')
PATH_EU = PATH_DATA.joinpath('EU-data')
PATH_HISTORISKE_DATA = PATH_DATA.joinpath('Historisk EU og Norge')

#PATH_LO = user_path.joinpath("Opinion AS/Opinion SharePoint - LO INRA/2024/01 Befolkningsundersøkelse 2024/")
PATH_LO = user_path.joinpath("Opinion AS/Opinion SharePoint - LO INRA/2025/01 Befolkningsundersøkelse 2025/")

PATH_MOBI = user_path.joinpath("Opinion AS/Opinion SharePoint - Mobilitetsbarometer/02 Perioder/Data/Datafiler")

CCI_DEFINISJON = ['EU01_Egen_oko_naa','EU02_Egen_oko_12mnd','EU04_Landets_oko_12mnd','EU09_Store_kjop_12mnd']
KJOPSINDEKS_DEFINISJON = ['EU09_Store_kjop_12mnd','EU13_Bilkjop_12mnd','EU14_Boligkjop_12mnd','EU15_Oppussing_12mnd']


# SPSS variabelnavn -> Kolonneheader i CCI_og_delindekser_Norge_akkumulert.csv
# Brukes:
#  - CCI_Norge.compute_scores()
#  - CCI_Norge.cci_norge_maanedlig() (Bruker kun keys!)
#
SPSS_VARIABLE_MAPPING = {
    'q1': 'EU03_Landets_oko_naa',
    'q2': 'EU04_Landets_oko_12mnd',
    'q3': 'EU01_Egen_oko_naa',
    'q4': 'EU02_Egen_oko_12mnd',
    'q6': 'EU09_Store_kjop_12mnd',
    'q7': 'EU12_Hushold_finanser',
    'q8': 'EU07_Arbeidsl_12mnd',
    'q10': 'NO10_Renter_12mnd',
    'q12': 'EU11_Sparing_12mnd',
    'q13': 'EU13_Bilkjop_12mnd',
    'q14': 'EU14_Boligkjop_12mnd',
    'q15': 'EU15_Oppussing_12mnd',
    'q17': 'NO17_Boligpriser_12mnd',
    }
 
# Kolonneheader i CCI_og_delindekser_Norge_akkumulert.csv -> kolonneheadere tilsvarende EU-data
# Brukes: 
#  -cci_europe_main() 
#
VARNAME_MAPPING_NO = {
    'CCI':  'NO.COF.B.M',
    'Kjopsindeksen':'NO.KI',
    'EU01_Egen_oko_naa': 'NO.1.B.M',
    'EU02_Egen_oko_12mnd': 'NO.2.B.M',
    'EU03_Landets_oko_naa': 'NO.3.B.M',
    'EU04_Landets_oko_12mnd': 'NO.4.B.M',
    'EU07_Arbeidsl_12mnd': 'NO.7.B.M',
    'EU09_Store_kjop_12mnd': 'NO.9.B.M',
    'EU11_Sparing_12mnd': 'NO.11.B.M',
    'EU12_Hushold_finanser': 'NO.12.B.M',
    'EU13_Bilkjop_12mnd': 'NO.13.B.M',
    'EU14_Boligkjop_12mnd': 'NO.14.B.M',
    'EU15_Oppussing_12mnd': 'NO.15.B.M',
    'NO10_Renter_12mnd': 'NO.10',
    'NO17_Boligpriser_12mnd': 'NO.17'
    }

# 
# Kolonneheader i CCI_og_delindekser_Norge_akkumulert.csv -> Spørsmålstittel på norsk
# # Brukes:
# - CCI_excelrapporter.kvartalstabeller() 
# - CCI_plotting.bar_and_line_with_dateindex()
#
QUESTION_TITLES = {
    'EU03_Landets_oko_naa': 'Landets økonomi i dag',
    'EU04_Landets_oko_12mnd': 'Landets økonomi om 12 mnd',
    'EU01_Egen_oko_naa': 'Egen økonomi i dag',
    'EU02_Egen_oko_12mnd': 'Egen økonomi om 12 mnd',
    'EU07_Arbeidsl_12mnd': 'Arbeidsløsheten om 12 mnd',
    'zzRenter_naa': 'Rentene i dag',
    'NO10_Renter_12mnd': 'Rentene om 12 mnd',
    'EU12_Hushold_finanser': 'Husholdningenes finanser (lån vs sparing)',
    'EU11_Sparing_12mnd': 'Sparing neste 12 mnd',
    'zzStore_kjop_naa': 'Forbruksgoder i dag',
    'EU09_Store_kjop_12mnd': 'Forbruksgoder neste 12 mnd',
    'EU13_Bilkjop_12mnd': 'Bilkjøp neste 12 mnd',
    'EU14_Boligkjop_12mnd': 'Boligkjøp neste 12 mnd',
    'EU15_Oppussing_12mnd': 'Oppussing neste 12 mnd',
    'zzBoligpriser_naa': 'Boligpriser i dag',
    'NO17_Boligpriser_12mnd': 'Boligpriser om 12 mnd',
    'CCI': 'CCI',
    'Kjopsindeksen': 'Kjøpsindeksen (forbruksgoder, bil, bolig, oppussing)'
    }


#titles = pd.Series(SPSS_VARIABLE_MAPPING).map(QUESTION_TITLES)
#pd.Series(SPSS_VARIABLE_MAPPING).str.extract("(^..\d{2})").squeeze()+" "+pd.Series(SPSS_VARIABLE_MAPPING).map(QUESTION_TITLES)


# Variable labels for respondentscore i kodet spss-fil
# Brukes: 
# - augment_spss_CCI_LO()
#
SCORE_LABELS = {
    'q1_score': 'NO.3 Landets økonomi i dag',
    'q2_score': 'NO.4 Landets økonomi om 12 mnd',
    'q3_score': 'NO.1 Egen økonomi i dag',
    'q4_score': 'NO.2 Egen økonomi om 12 mnd',
    'q6_score': 'NO.9 Forbruksgoder neste 12 mnd',
    'q7_score': 'NO.12 Husholdningens finanser',
    'q8_score': 'NO.7 Arbeidsledigheten om 12 mnd',
    'q10_score': 'NO.10 Boliglånsrenter om 12 mnd',
    'q12_score': 'NO.11 Sparing neste 12 mnd',
    'q13_score': 'NO.13 Bilkjøp neste 12 mnd',
    'q14_score': 'NO.14 Boligkjøp neste 12 mnd',
    'q15_score': 'NO.15 Oppussing neste 12 mnd',
    'q17_score': 'NO.17 Boligpriser om 12 mnd',
    'cci_score': 'NO.CCI',
    'kjopsindeks_score' :'NO.Kjøpsindeksen'

    }


SCALE_SELECTION = {
        'pos_5_points': ['q1','q2','q3','q4','q6','q8','q10','q17'],
        'pos_4_points': ['q12','q13','q14','q15'],
        'neg_5_points': ['q7'],
    }


SCALE_DEFINITION = {
    'pos_5_points': {1:'PP', 2:'P', 3:'.', 4:'M', 5:'MM', 6:'.'},
    'pos_4_points': {1:'PP', 2:'P', 3:'M', 4:'MM', 5:'.'},
    'neg_5_points': {5:'PP', 4:'P', 3:'.', 2:'M', 1:'MM', 6:'.'}
}


SCALE_SCORES = {
    'PP': 100,
    'P': 50,
    '.': 0,
    'M': -50,
    'MM':-100
}


QUARTERS_LO = {
    1: 'Q1 2021', 2: 'Q2 2021', 3: 'Q3 2021', 4: 'Q4 2021',
    5: 'Q1 2022', 6: 'Q2 2022', 7: 'Q3 2022', 8: 'Q4 2022',
    9: 'Q1 2023', 10: 'Q2 2023', 11: 'Q3 2023', 12: 'Q4 2023',
    13: 'Q1 2024', 14: 'Q2 2024', 15: 'Q3 2024', 16: 'Q4 2024',
    17: 'Q1 2025', 18: 'Q2 2025', 19: 'Q3 2025', 20: 'Q4 2025',
    21: 'Q1 2026', 22: 'Q2 2026', 23: 'Q3 2026', 24: 'Q4 2026',
    25: 'Q1 2027', 26: 'Q2 2027', 27: 'Q3 2027', 28: 'Q4 2027',
    29: 'Q1 2028', 30: 'Q2 2028', 31: 'Q3 2028', 32: 'Q4 2028'
}

months_no = ['Januar', 'Februar', 'Mars', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Desember']
months = [f"{month} {year}" for year in range(2021, 2027) for month in months_no]
MONTHS_LO = {i: months[i-1] for i in range(1, len(months) + 1)}

YYMM_LABELS = {(year-2000)*100 + m: f"{months_no[m-1]} {year}" for year in range(2020, 2027) for m in range(1,13)}
YYQ_LABELS = {(year-2000)*10 + q: f"Q{q} {year}" for year in range(2020, 2027) for q in range(1,5)}


def select_and_apply_scale(df):
    mapped = df.copy()
    for scale_id, questions in SCALE_SELECTION.items():
        value_mapping = SCALE_DEFINITION[scale_id]
        mapped[questions] = df[questions].replace(value_mapping)
    return mapped


def read_norway_historical_data(detailed=True):
    norge_fil = PATH_HISTORISKE_DATA.joinpath('CCI_og_delindekser_Norge_akkumulert.csv')
    data = pd.read_csv(norge_fil, header=[0,1], index_col=0)
    data.index = pd.to_datetime(data.index, dayfirst=True)
    if data.index.size != data.index.unique().size:
        print('\nAdvarsel: Dupliserte datoverdier i {}\n'.format(norge_fil))
    if detailed==False:
        data = data.xs('net', level=1, axis=1)
    print(data)
    return data


def read_combined_historical_data():
    fil = askopenfilename(title='Velg fil: samlet historisk', initialdir=PATH_HISTORISKE_DATA, filetypes=(('csv','*.csv'),))
    data = pd.read_csv(fil, index_col=0)
    data.index = pd.to_datetime(data.index, dayfirst=False)
    print(data)
    return data


def open_file_y_n(file):
    inp = input('\nÅpne fil? [y/n]: ')
    if inp.lower()=='y':
        try:
            print('Åpner fil...')
            os.startfile(file)
        except:
            print('Kan ikke åpne fil {}'.format(file))
            pass


EXPECTED_VARIABLES_RAW = [
    "record", "start_date", "date", "status", "age", "gender", "zipcode", 
    "fylke2020", "kommune2020", "fylke2024", "kommune2024", "landsdel2020", "landsdel2024", "Region", 
    "age_group", "weeks", "months", "quarters", "year",
    "d16", "d16r11_other", "D_16B", "D_16Br11_other", "q0", "q0r11_other", 
    "q1", "q2", "q3", "q4", "q6", "q7", "q8", "q10", "q12", "q13", "q14", "Q14b_1", "Q14b_2", "Q14b_3", "Q14b_4", "Q14b_5", "Q14b_6", "Q14br5_other", 
    "q15", "q17", "C16", "SPM_C","d6", "d7b", "d7", "d8", "C15", "D_ny1", "D_ny2", "D_ny3", "D_ny4", "d17",
    "qtime", "weight"
]

#"fylke", "kommune","landsdel",
# "SPM_C2",
CCI_VARIABLES = ["fylke", "kommune","landsdel", "region",
    "unik_id", "record", "date", "date_dt", "year", "mnd_num", "kvartal_num", "yymm", "yyq", 
    "status", "age", "Alder", "gender", "zipcode",  "fylke2020", "kommune2020", 
     "landsdel2020", "fylke2024", "kommune2024", "landsdel2024",  "q1", "q2", "q3", "q4", "q6", "q7", "q8", "q10", "q12", "q13", "q14", "q15", "q17", 
    "q14b_1", "q14b_2", "q14b_3", "q14b_4", "q14b_5", "q14b_6", "c16", "d6", "d7b", "d7", "d8", 
    "c15", "D_ny1", "D_ny2", "D_ny3", "D_ny4", "d16", "d16r11_other", "d17", "SPM_C", "q1_score", 
    "q2_score", "q3_score", "q4_score", "q6_score", "q7_score", "q8_score", "q10_score", 
    "q12_score", "q13_score", "q14_score", "q15_score", "q17_score", "cci_score", 
    "kjopsindeks_score", "d7_ny", "d7b_ny", "d8_ny", "D_ny1_ny", "D_ny1_ny_II", "d17_ny", 
    "d17_ny_jobb", "weight", "weight_normalized"
]

#['ageXgender', 'region', 'q14b_1', 'q14b_2', 'q14b_3', 'q14b_4', 'q14b_5', 'q14b_6', 'c16', 'c15', 'SPMC'] 


#"fylke", "kommune","landsdel",
LO_BAKGRUNN = {
    'foran': ["fylke", "kommune","landsdel",
        "record", "unik_id", "start_date", "date", "År", "Kvartal", "yyq", "Måned","yymm", "status", "age", "Alder", "gender", 
        "zipcode",  "fylke2020", "kommune2020", "fylke2024", "kommune2024",  
        "landsdel2020", "landsdel2024", "age_group"],
    'bak': [
        "d6", "d7b", "d7b_ny", "d7", "d7_ny", "d8", "d8_ny", "c15", 
        "D_ny1", "D_ny1_ny", "D_ny1_ny_II", "D_ny2", "D_ny3", "D_ny4", "d16", 
        "d16r11_other", "D_16B", "D_16Br11_other", "d17", "d17_ny", "d17_ny_jobb", 
        "q0", "q0r11_other",
        "qtime",  "weight", "weight_normalized"]
}

MOBI_BAKGRUNN = {
    'foran': ["fylke", "kommune","landsdel",
        "record", "start_date", "date", "status", "age", "Alder", "gender", "zipcode", "fylke2020", 
        "kommune2020",  "fylke2024", "kommune2024", "landsdel2020", "landsdel2024"
        ],
    'bak': [
        "d6", "d7b","d7b_ny", "d7","d7_ny", "d8","d8_ny", "c15", "D_ny1", "D_ny1_ny_II", "D_ny2", "D_ny3", "D_ny4", 
        "d17","d17_ny", "weight", "weight_normalized"]
}




"""
LO_VARIABLES = [
    "record", "unik_id", "start_date", "date", "År", "Kvartal", "yyq", "Måned","yymm", "status", "age", "Alder", "gender", 
    "zipcode", "fylke", "kommune", "fylke2020", "kommune2020", "fylke2024", "kommune2024", "landsdel", 
    "landsdel2020", "landsdel2024", "age_group", "ageXgender", "region", 
    # Vil du si at samfunnsutviklingen i Norge går i riktig eller i feil retning under den sittende regjeringen?
    "G1", 
    # Vil du si at den sittende regjeringens politikk styrker eller svekker tilliten din til …
    "G2r1", "G2r2", "G2r3", 
    # Hvilket politisk parti mener du fører den beste politikken når det gjelder …
    "Gxny1r1", "Gxny1r2", "Gxny1r3", "Gxny1r4", "Gxny1r5", "Gxny1r6", "Gxny1r7", "Gxny1r8", 
    "Gxny1r9", "Gxny1r10", "Gxny1r11", 
    # Av følgende områder, hvilke er de tre viktigste politikkområdene for deg ved valg av parti?
    "Gxny2_01", "Gxny2_02", "Gxny2_03", "Gxny2_04", "Gxny2_05", "Gxny2_06", "Gxny2_07", "Gxny2_08", 
    "Gxny2_09", "Gxny2_10", "Gxny2_11", "Gxny2_12", "Gxny2_13", "Gxny2_14", "Gxny2_15", "Gxny2_16", 
    "Gxny2_17", "Gxny2_18", "Gxny2_19", "Gxny2_20", "Gxny2_21", "Gxny2_22", "Gxny2r22_other", 
    # Vil du bytte ut dagens regjering med en annen regjering eller beholde dagens regjering?
    "Gxny3", 
    # Nå vil vi gjerne vite hva du oppfatter er hvert enkelt partis politiske hovedsak. Hva oppfatter du er hovedsaken til: 
    "Gxny4_1r1", "Gxny4_2r1", "Gxny4_3r1", "Gxny4_4r1", "Gxny4_5r1", "Gxny4_6r1", "Gxny4_7r1", 
    "Gxny4_8r1", "Gxny4_9r1", 
    "noanswerGxny4_1_r2_1", "noanswerGxny4_2_r2_1", "noanswerGxny4_3_r2_1", "noanswerGxny4_4_r2_1", 
    "noanswerGxny4_5_r2_1", "noanswerGxny4_6_r2_1", "noanswerGxny4_7_r2_1", "noanswerGxny4_8_r2_1", 
    "noanswerGxny4_9_r2_1", 
    # Hva er ditt inntrykk av følgende politikere?
    "Gxny5r1", "Gxny5r2", "Gxny5r5", "Gxny5r8", "Gxny5r10", "Gxny5r11", "Gxny5r13", "Gxny5r14", "Gxny5r15", 
    # For hvert av de følgende politiske partiene, hvor godt eller dårlig liker du dem?
    "Gxny6r1", "Gxny6r2", "Gxny6r3", "Gxny6r4", "Gxny6r5", "Gxny6r6", "Gxny6r7", "Gxny6r8", "Gxny6r9", "Gxny6r11", 
    # Man snakker ofte om politikken som en akse fra venstre til høyre.Hvor vil du plassere deg på aksen, hvis 1 er ytterst til venstre og 10 er ytterst til høyre?
    "Gxny7", "Gxny7_ny", 
    # Kan du nevne inntil tre politiske saker eller områder som har vært diskutert i pauser eller ellers på arbeidsplassen din de siste månedene?
    "Gxny8r1", "Gxny8r2", "Gxny8r3", "noanswerGxny8_r4_1", 
    # Bakgrunn
    "d6", "d7b", "d7b_ny", "d7", "d7_ny", "d8", "d8_ny", "c15", 
    "D_ny1", "D_ny1_ny", "D_ny1_ny_II", "D_ny2", "D_ny3", "D_ny4", "qtime", "d16", 
    "d16r11_other", "D_16B", "D_16Br11_other", "d17", "d17_ny", "d17_ny_jobb", 
    "q0", "q0r11_other", "weight", "weight_normalized", 
]
"""
