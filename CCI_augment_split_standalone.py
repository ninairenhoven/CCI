"""
Standalone versjon av CCI_LO_augment_split_merge.py (uten merge-steg).

Gjør augment- og split-delen av originalen (les inn/berik månedlig SPSS-fil,
split til CCI/LO/Mobilitetsbarometeret), men uten avhengighet til de tre
augment/split/merge-modulene i CCI_modules. Gjenbruker paths og konstanter
fra CCI_modules.CCI_utils fremfor å duplisere dem. Forenklet: færre
"Press Enter"-pauser og mindre detaljert diagnostikk enn originalen.
"""

import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat
import tkinter
from tkinter.filedialog import askopenfilename, asksaveasfilename

from CCI_modules.CCI_utils import (
    PATH_DATA_MAANED, PATH_LO, PATH_MOBI,
    CCI_DEFINISJON, KJOPSINDEKS_DEFINISJON, SPSS_VARIABLE_MAPPING, SCORE_LABELS,
    SCALE_SCORES, MONTHS_LO, QUARTERS_LO, YYMM_LABELS, YYQ_LABELS,
    CCI_VARIABLES, LO_BAKGRUNN, MOBI_BAKGRUNN, select_and_apply_scale,
)

# --------------------------------------------------------------------------
# KONSTANTER SPESIFIKKE FOR BERIKING (ikke i CCI_utils)
# --------------------------------------------------------------------------

# Definerer hvordan hver bakgrunnsvariabel skal rekodes:
#   input:  navn på rå SPSS-variabel
#   d:      mapping fra rå verdi -> ny (grovere) kategori
#   labels: value labels for den nye variabelen
RECODE_DESCRIPTIONS = {
    "d7_ny": {  # HUSHOLDNINGENS INNTEKT
        "input": "d7",
        "d": ({k: 1 for k in [1, 2, 3, 4]} | {k: 2 for k in [5, 6, 7]} | {k: 3 for k in [8, 9, 10]}
              | {k: 4 for k in [11]} | {k: 4 for k in range(14, 21)} | {k: 5 for k in [12, 13]}),
        "labels": {1: "Under 400 000 kr", 2: "401–700 000 kr", 3: "701–1 000 000 kr",
                   4: "Mer enn 1 000 000 kr", 5: "Vet ikke / ønsker ikke å svare"},
    },
    "d7b_ny": {  # PERSONLIG INNTEKT
        "input": "d7b",
        "d": {1: 1, 2: 1, 3: 1, 4: 2, 5: 2, 6: 3, 7: 3, 8: 4, 9: 4, 10: 4, 11: 4, 12: 5},
        "labels": {1: "Under 300 000 kr", 2: "301–500 000 kr", 3: "501–700 000 kr",
                   4: "Mer enn 700 000 kr", 5: "Ønsker ikke å svare"},
    },
    "d8_ny": {  # HUSSTANDSLÅN
        "input": "d8",
        "d": {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 5, 7: np.nan, 8: 6},
        "labels": {1: "Under 0,5 mill. kroner", 2: "0,5–0,99 mill. kroner", 3: "1–1,49 mill. kroner",
                   4: "1,5–1,99 mill. kroner", 5: "2 mill. kroner eller mer", 6: "Har ikke lån"},
    },
    "D_ny1_ny": {  # DAGLIG SITUASJON
        "input": "D_ny1",
        "d": {1: 1, 3: 1, 2: 2, 4: 3, 5: 3, 6: 3, 7: 4, 8: 5, 9: 5, 10: 5, 11: 6},
        "labels": {1: "Heltid", 2: "Deltid", 3: "Permittert", 4: "Pensjonist",
                   5: "Arbeidssøkende/student/annet", 6: "Ønsker ikke svare"},
    },
    "D_ny1_ny_II": {  # DAGLIG SITUASJON (i jobb / ikke i jobb)
        "input": "D_ny1",
        "d": {1: 1, 2: 1, 3: 1, 4: 2, 5: 2, 6: 2, 7: 2, 8: 2, 9: 2, 10: 2, 11: 2},
        "labels": {1: "I jobb", 2: "Ikke i jobb"},
    },
    "d17_ny": {  # TILSLUTNING
        "input": "d17",
        "d": {1: 1, 2: 2, 3: 2, 4: 2, 5: 2, 6: 3},
        "labels": {1: "LO", 2: "YS/Unio/Akademikerne/Frittstående", 3: "Ikke medlem"},
    },
    "Gxny7_ny": {  # POLITISK AKSE
        "input": "Gxny7",
        "d": {1: 1, 2: 1, 3: 1, 4: 1, 5: 2, 6: 2, 7: 3, 8: 3, 9: 3, 10: 3, 11: 4, 999: 4},
        "labels": {1: "Venstre", 2: "Sentrum", 3: "Høyre", 4: "Vet ikke"},
    },
}

# Column labels (variabelnavn -> beskrivelse) for de nye rekodede variablene
COL_LABELS_RECODED_VARS = {
    "Alder": "Alder", "d7_ny": "Husstandsinntekt", "d7b_ny": "Personlig inntekt", "d8_ny": "Husstandslån",
    "D_ny1_ny": "Daglig situasjon", "D_ny1_ny_II": "Daglig situasjon II", "d17_ny": "Tilslutning",
    "d17_ny_jobb": "Tilslutning II", "Gxny7_ny": "Politisk akse",
}

# Overstyrer/supplerer column labels for enkelte variabler som beholdes fra rådata
# eller som opprettes i tracker_variables()
COL_LABELS_UPDATE = {
    "landsdel2020": "Landsdeler 2020", "landsdel2024": "Landsdel", "d6": "Utdanning", "c15": "Urbanitet",
    "d16": "Partivalg", "d17": "Tilslutning", "År": "År", "Kvartal": "Kvartal", "Måned": "Måned",
    "mnd_num": "Månedsnummer", "kvartal_num": "Kvartalsnummer", "year": "Year", "yymm": "År_måned",
    "yyq": "År_kvartal", "gender": "Kjønn",
}

# Aldersgrupper: bins er venstre-inkluderende (18-29, 30-39, ..., 60+)
AGE_BINS = [18, 30, 40, 50, 60, 111]
AGE_LABELS = {1: "Under 30 år", 2: "30–39 år", 3: "40–49 år", 4: "50–59 år", 5: "60 år +"}

D17_NY_JOBB_LABELS = {
    1: "LO-medlemmer, i jobb", 2: "LO-medlemmer, ikke i jobb",
    3: "YS/Unio/Akademikerne/Frittstående", 4: "Ikke medlem",
}


# --------------------------------------------------------------------------
# STEG 1: BERIKE RÅDATA (augment)
# --------------------------------------------------------------------------

def tracker_variables(date_column):
    tracker = pd.DataFrame()
    tracker["date_dt"] = pd.to_datetime(date_column)

    # En innsamlingsrunde kan strekke seg over månedsskiftet (f.eks. siste dager i
    # forrige måned). Alle datoer samles da til samme (siste) måned i datasettet,
    # slik at hele runden telles som én måling.
    if tracker["date_dt"].dt.month.nunique() > 1:
        print("\nDatoer i datasett:")
        print(tracker["date_dt"].dt.date.value_counts().sort_index())
        year = tracker["date_dt"].dt.year.max()
        month = tracker["date_dt"].dt.month.max()
        min_date = pd.Timestamp(f"{year}-{month}-01")
        print(f"\nFlere måneder i datasettet. Setter alle datoer >= {min_date.date()} til denne måneden.")
        input("Press Enter for å fortsette...")
        tracker["date_dt"] = tracker["date_dt"].clip(lower=min_date)
        print("\nEndret datoer til:")
        print(tracker["date_dt"].dt.date.value_counts().sort_index())

    tracker["mnd_num"] = tracker["date_dt"].dt.month
    tracker["kvartal_num"] = tracker["date_dt"].dt.quarter
    # yymm/yyq: kompakte sorterbare tidsnøkler, f.eks. august 2024 -> 2408, Q3 2024 -> 243
    yy = tracker["date_dt"].dt.year - 2000
    tracker["yymm"] = yy * 100 + tracker["mnd_num"]
    tracker["yyq"] = yy * 10 + tracker["kvartal_num"]

    # Måned/Kvartal: LO-spesifikke løpenumre som teller fra første måling i 2021
    # (Måned 1 = januar 2021), brukt som tidsakse i LO-rapportering
    tracker["År"] = tracker["date_dt"].dt.year
    temp_year_LO = tracker["År"] - 2021
    tracker["Måned"] = 12 * temp_year_LO + tracker["mnd_num"]
    tracker["Kvartal"] = 4 * temp_year_LO + tracker["date_dt"].dt.quarter

    # unik_id: yymm som "prefiks" + radnummer, f.eks. 2024080001 for rad 1 i august 2024.
    # Forutsetter færre enn 100 000 respondenter per måned.
    tracker["unik_id"] = (tracker["yymm"] * 1e5 + tracker.index).astype(int)
    tracker["date_dt"] = tracker["date_dt"].dt.date

    print(f"Måned: {tracker['mnd_num'].iloc[0]}, Kvartal: {tracker['kvartal_num'].iloc[0]}")
    print(f"Dato: {tracker['date_dt'].min()} - {tracker['date_dt'].max()}")

    return tracker


def calculate_respondent_CCI_scores(df):
    # select_and_apply_scale (fra CCI_utils) oversetter rå svarkoder (1-5/1-4) til
    # PP/P/./M/MM ("sterkt positiv" ... "sterkt negativ"), som her regnes om til
    # score -100..100 (SCALE_SCORES). CCI og Kjøpsindeksen er gjennomsnitt av
    # score for et fast utvalg spørsmål (CCI_DEFINISJON/KJOPSINDEKS_DEFINISJON i CCI_utils).
    cci_questions = list(SPSS_VARIABLE_MAPPING.keys())
    dfm = select_and_apply_scale(df)[cci_questions]
    scores = dfm.map(lambda x: SCALE_SCORES[x])
    temp = scores.rename(columns=SPSS_VARIABLE_MAPPING)
    scores["cci"] = temp[CCI_DEFINISJON].mean(axis=1)
    scores["kjopsindeks"] = temp[KJOPSINDEKS_DEFINISJON].mean(axis=1)
    scores.columns = scores.columns + "_score"
    return scores


def print_recode_mapping(raw_series, mapping, new_labels, old_labels=None):
    # Viser faktisk mapping i dataene, gruppert per ny kategori:
    # [ny label]
    #   - [gammel label] (antall)
    #   - [gammel label] (antall)
    # Bruker input-variabelens egne value labels (old_labels) for gammel label,
    # ikke den rå tallkoden - faller kun tilbake til rå verdi der label mangler.
    # Viser kun rå verdier som faktisk forekommer i dataene.
    old_labels = old_labels or {}
    counts = raw_series.value_counts(dropna=False).sort_index()
    groups = {}
    for old_value, count in counts.items():
        old_label = old_labels.get(old_value, old_value)
        new_value = mapping.get(old_value, np.nan)
        groups.setdefault(new_value, []).append((old_label, count))

    def sort_key(new_value):
        return (pd.isna(new_value), new_value if not pd.isna(new_value) else 0)

    for new_value in sorted(groups, key=sort_key):
        new_label = "NaN" if pd.isna(new_value) else new_labels.get(new_value, new_value)
        print(f"  {new_label}")
        for old_label, count in groups[new_value]:
            print(f"    - {old_label} ({count})")


def recode_variables(df, raw_value_labels=None):
    raw_value_labels = raw_value_labels or {}
    recoded = pd.DataFrame(index=df.index)
    value_labels = {}
    for newvar, description in RECODE_DESCRIPTIONS.items():
        input_var = description["input"]
        print(f"\nRekoder {input_var} -> {newvar}")
        if input_var in df.columns:
            unmapped = set(df[input_var]) - set(description["d"].keys())
            if unmapped:
                print(f"ADVARSEL: {input_var} har verdier uten mapping for {newvar}: {unmapped} (beholder original verdi)")
                input("Press Enter for å fortsette...")
            recoded[newvar] = df[input_var].replace(description["d"])
            print_recode_mapping(df[input_var], description["d"], description["labels"], raw_value_labels.get(input_var))
        else:
            print(f"ADVARSEL: Variabel {input_var} finnes ikke i input-data, {newvar} settes til NaN")
            input("Press Enter for å fortsette...")
            recoded[newvar] = np.nan
        value_labels[newvar] = description["labels"]
    return recoded, value_labels


def get_age_groups(age_col):
    age_groups = pd.cut(age_col, bins=AGE_BINS, labels=np.arange(5) + 1, right=False)
    if (age_col.min() < min(AGE_BINS)) or (age_col.max() >= max(AGE_BINS)):
        print("ADVARSEL: Inputdata inkluderer alder utenfor definerte aldersgrupper")
        input("Press Enter for å fortsette...")
    # pd.cut gir en Categorical, som pyreadstat ville lagret som tekst; gjør den
    # numerisk igjen (float pga. mulige NaN for aldre utenfor AGE_BINS) slik at
    # SPSS-filen får Alder som tallkolonne med value labels, ikke strengkolonne.
    return age_groups.astype("float64")


def code_background_variables(df, raw_value_labels=None):
    recoded, value_labels = recode_variables(df, raw_value_labels)

    recoded["Alder"] = get_age_groups(df["age"])
    value_labels["Alder"] = AGE_LABELS

    # Organisasjonstilslutning kombinert med jobbstatus (d17_ny_jobb):
    # d17_ny er 1=LO, 2=YS/Unio/Akademikerne/Frittstående, 3=Ikke medlem.
    # Skyver disse til 2/3/4 for å gjøre plass til en egen kategori 1 for
    # "LO-medlem som er i jobb" (se D17_NY_JOBB_LABELS).
    temp = pd.Series(index=recoded.index, dtype="float64")
    mask = ~recoded["D_ny1_ny_II"].isna()
    temp[mask] = recoded.loc[mask, "d17_ny"] + 1
    LO_ijobb_mask = (recoded["d17_ny"] == 1) & (recoded["D_ny1_ny_II"] == 1)
    temp[LO_ijobb_mask] = 1
    recoded["d17_ny_jobb"] = temp
    value_labels["d17_ny_jobb"] = D17_NY_JOBB_LABELS

    return recoded, value_labels


def get_variable_rename(df):
    # Rydder opp i noen inkonsekvente variabelnavn fra rådataeksporten:
    # - Gxny2_1, Gxny2_2, ... -> Gxny2_01, Gxny2_02, ... (nullpadding, slik at
    #   alfabetisk sortering matcher tallrekkefølgen for spørsmål 1-22)
    # - Q14b_x -> q14b_x (liten forbokstav, konsistent med resten av q-variablene)
    # - C15/C16/D16/Region -> c15/c16/d16/region (samme grunn)
    gx = df.filter(regex=r"^Gxny2_\d{1,2}$").columns.to_series()
    q14b = df.filter(regex="Q14b").columns.to_series().str.lower()
    if len(gx) > 0:
        gx = gx.str.split("_", expand=True)
        gx[1] = gx[1].str.zfill(2)
        gx = gx.apply("_".join, axis=1)
    var_rename = pd.concat([gx, q14b])
    var_rename["C15"] = "c15"
    var_rename["C16"] = "c16"
    var_rename["D16"] = "d16"
    var_rename["Region"] = "region"
    return var_rename


def save_augmented_to_file(df, column_labels, value_labels, filename_stem, initial_dir):
    # Filnavn: <opprinnelig navn>_PREP_KOMPLETT_<datamåned>_<lagredato>.sav
    data_month = df["date_dt"].max().strftime("%b%Y").upper()
    yymmdd = dt.datetime.now().strftime("%y%m%d")
    output_file = f"{filename_stem}_PREP_KOMPLETT_{data_month}_{yymmdd}.sav"
    output_file = asksaveasfilename(initialdir=initial_dir, initialfile=output_file)
    if output_file != "":
        print(f"Lagrer komplett datasett til {output_file}...")
        pyreadstat.write_sav(df, output_file, column_labels=column_labels, variable_value_labels=value_labels)
        print(f"Lagret til {output_file}")
    return output_file


def augment_spss_CCI_LO(spss_file=""):
    if spss_file == "":
        spss_file = askopenfilename(initialdir=PATH_DATA_MAANED, filetypes=[("SAV", "*.sav")])
    spss_file = Path(spss_file)
    print(spss_file)

    print("\nLeser rådata...")
    df0, meta = pyreadstat.read_sav(spss_file)
    df0 = df0.set_index("record")
    value_labels = pd.Series(meta.variable_value_labels)
    column_labels = pd.Series(meta.column_names_to_labels)
    print(f"Lest {len(df0)} rader, {len(df0.columns)} variabler.")

    print("\nBeregner CCI- og kjøpsindeks-score per respondent...")
    cci_scores = calculate_respondent_CCI_scores(df0)

    print("\nRekoder bakgrunnsvariabler...")
    recoded, value_labels_recoded_vars = code_background_variables(df0, meta.variable_value_labels)

    print("\nBeregner trackervariabler (dato, måned, kvartal, unik_id)...")
    tracker = tracker_variables(df0["date"])

    print("\nBeregner normalisert vekt...")
    df0["weight_normalized"] = df0["weight"] * 1000 / df0["weight"].sum()

    df1 = pd.concat([tracker, df0, recoded, cci_scores], axis=1)

    value_labels = pd.concat([value_labels, pd.Series(value_labels_recoded_vars)])
    value_labels["yymm"] = YYMM_LABELS
    value_labels["yyq"] = YYQ_LABELS
    column_labels = pd.concat([column_labels, pd.Series(COL_LABELS_RECODED_VARS), pd.Series(SCORE_LABELS)])
    column_labels = pd.Series(COL_LABELS_UPDATE).combine_first(column_labels)
    # pyreadstat krever at alle labels er strenger; fjern variabler uten label (NaN)
    column_labels = column_labels.dropna()

    print("\nOmdøper variabler...")
    var_rename = get_variable_rename(df1)
    df1 = df1.rename(columns=var_rename)
    value_labels = value_labels.rename(var_rename)
    column_labels = column_labels.rename(var_rename)

    value_labels["Kvartal"] = QUARTERS_LO
    value_labels["Måned"] = MONTHS_LO

    df1 = df1.reset_index()

    duplicated = df1.columns.str.lower().duplicated(keep=False)
    if duplicated.sum() > 0:
        print("\nADVARSEL: Dupliserte variabelnavn:", list(df1.columns[duplicated]))
        input("Press Enter for å fortsette...")

    print(f"\nBerikelse ferdig. {len(df1)} rader, {len(df1.columns)} variabler.")
    inp = input("\nLagre komplett datasett til fil? [y/n]: ")
    output_file = ""
    if inp.upper() != "N":
        output_file = save_augmented_to_file(df1, column_labels.to_dict(), value_labels.to_dict(), spss_file.stem, spss_file.parent)

    return output_file, df1


# --------------------------------------------------------------------------
# STEG 2: SPLIT OG LAGRE (CCI / LO / Mobilitetsbarometeret)
# --------------------------------------------------------------------------

def keep_cols(df, cols):
    # Filtrerer en ønsket variabelliste ned til de som faktisk finnes i df,
    # og varsler om noen mangler (i stedet for å feile på KeyError ved utvalg)
    cols_in_df = [c for c in cols if c in df.columns]
    missing = [c for c in cols if c not in df.columns]
    if missing:
        print("NB: variabler mangler i datasett:", missing)
        input("Press Enter for å fortsette...")
    return cols_in_df


def split_and_save_files(file=""):
    if file == "":
        file = askopenfilename(initialdir=PATH_DATA_MAANED, title="Velg kodet månedlig spss-fil", filetypes=[("SAV", "*.sav")])

    print(f"\nLeser {file}...")
    df, meta = pyreadstat.read_sav(file)
    column_labels = meta.column_names_to_labels
    value_labels = meta.variable_value_labels
    print(f"Lest {len(df)} rader, {len(df.columns)} variabler.")

    input_dir = Path(file).parent
    # "*_KOMPLETT_..." -> "*_*_..."; "*" erstattes med CCI/LO/MOBI under, så
    # utfilene får samme navnemønster som komplettfilen, bare med formålet i stedet
    file_stem = Path(file).stem.replace("KOMPLETT", "*")
    files = {}

    # For hvert delformål: fast variabelliste (foran/bak) + spørsmålsvariabler
    # plukket ut med regex på prefiks (G=LO sine politikkspørsmål, H=Mobilitetsbarometerets
    # spørsmål), pluss hvilken mappe filvalgdialogen skal foreslå
    targets = [
        ("CCI", CCI_VARIABLES, input_dir),
        ("LO", LO_BAKGRUNN["foran"] + list(df.filter(regex=r"^(G|QG|noanswerG|noanswerQG)").columns) + LO_BAKGRUNN["bak"], PATH_LO),
        ("Mobi", MOBI_BAKGRUNN["foran"] + list(df.filter(regex="^H|^hid_H|^T").columns) + MOBI_BAKGRUNN["bak"], PATH_MOBI),
    ]

    for label, cols, initial_dir in targets:
        inp = input(f"\nLagre fil til {label}? [y/n]: ")
        if inp.upper() != "Y":
            continue
        default_name = file_stem.replace("*", label.upper()) + ".sav"
        output_file = asksaveasfilename(initialdir=initial_dir, initialfile=default_name)
        if output_file == "":
            continue
        vars_out = keep_cols(df, cols)
        print(f"Lagrer {label}-fil ({len(vars_out)} variabler) til {output_file}...")
        pyreadstat.write_sav(df[vars_out], output_file, column_labels=column_labels, variable_value_labels=value_labels)
        print(f"Lagret til {output_file}")
        files[label] = output_file

    return files


# --------------------------------------------------------------------------
# HOVEDPROGRAM
# --------------------------------------------------------------------------

def main():
    # Steg 1 (valgfritt): les rå månedlig SPSS-fil og berik den (tracker-variabler,
    # CCI-score, rekodede bakgrunnsvariabler) - eller hopp over og bruk en fil som
    # allerede er beriket fra et tidligere kjøring.
    # Steg 2: splitt den berikede/komplette filen i egne filer for CCI, LO og
    # Mobilitetsbarometeret, med bare de variablene hvert formål trenger.
    root = tkinter.Tk()
    root.withdraw()

    inp = input("Les inn og berike rådata? y/n: ")
    if inp.upper() == "Y":
        print("\nVELG FIL MED RÅDATA:\n")
        raadata_file = askopenfilename(title="Åpne månedlig SPSS-fil", initialdir=PATH_DATA_MAANED, filetypes=[("SAV", "*.sav")])
        print(raadata_file)
        print("\n=== STEG 1: BERIKER RÅDATA ===")
        augmented_file, df = augment_spss_CCI_LO(raadata_file)
    else:
        print("\nVELG FIL MED FERDIG BERIKET MÅNEDLIG DATA:\n")
        augmented_file = askopenfilename(title="Åpne prosessert månedlig fil", initialdir=PATH_DATA_MAANED, filetypes=[("SAV", "*.sav")])

    print("\n=== STEG 2: SPLIT OG LAGRE ===")
    split_and_save_files(augmented_file)
    print("\nFerdig.")


if __name__ == "__main__":
    main()
