"""
Standalone versjon av merge-delen av CCI_LO_augment_split_merge.py.

Slår sammen en beriket/komplett månedlig SPSS-fil (se CCI_LO_Mobi_prepare_files.py)
med CCI-masterfilen, uten avhengighet til CCI_merge_with_master.py i CCI_modules.
Gjenbruker paths fra CCI_modules.CCI_utils fremfor å duplisere dem.
"""

import datetime as dt
from pathlib import Path

import pandas as pd
import pyreadstat
import tkinter
from tkinter.filedialog import askopenfilename, asksaveasfilename

from CCI_modules.CCI_utils import PATH_DATA_MAANED, PATH_DATA_MASTER


def stack_value_labels(value_labels_dict):
    # Gjør {variabel: {verdi: label}} om til en flat Series med
    # MultiIndex (variabel, verdi) -> label, slik at den kan sammenlignes/reindekses
    # på tvers av to datasett som ikke nødvendigvis har samme variabler/verdier.
    return pd.Series(value_labels_dict).apply(pd.Series).stack()


def compare_value_labels(labels, master_labels, ignore_vars=None):
    # Sammenligner value labels for nye data mot masterfilen, kun for variabler
    # som finnes med labels i begge (ellers ville alt i nye data vist som avvik).
    ignore_vars = ignore_vars or []
    labels = stack_value_labels(labels)
    master_labels = stack_value_labels(master_labels)
    keep_vars = [v for v in labels.index.levels[0] if v in master_labels.index.levels[0]]
    master_labels = master_labels.loc[keep_vars]
    labels = labels.reindex_like(master_labels)
    comparison = labels.compare(master_labels).drop(ignore_vars, errors="ignore")
    if len(comparison) > 0:
        print("\nADVARSEL: Avvikende value labels (self=nye data, other=master):")
        print(comparison)
        input("Press Enter for å fortsette...")
    return comparison


def compare_column_labels(labels, master_labels, ignore_vars=None):
    # Samme som over, men for variabel-/kolonnelabels (case-insensitivt for å
    # unngå falske avvik pga. store/små bokstaver)
    ignore_vars = ignore_vars or []
    labels = pd.Series(labels)
    master_labels = pd.Series(master_labels).drop(ignore_vars, errors="ignore")
    labels = labels.str.lower()
    master_labels = master_labels.str.lower()
    labels = labels.reindex_like(master_labels)
    comparison = labels.compare(master_labels)
    if len(comparison) > 0:
        print("\nADVARSEL: Avvikende variabellabels (self=nye data, other=master):")
        print(comparison)
        input("Press Enter for å fortsette...")
    return comparison


def check_months(new_data, master_data, month_labels=None):
    month_labels = month_labels or {}
    new_data_months = new_data["yymm"].value_counts().rename(month_labels)
    master_months = master_data["yymm"].value_counts().sort_index().rename(month_labels)
    print("\nMaster data, antall per måned:")
    print(master_months)
    print("\nNye data, antall per måned:")
    print(new_data_months)

    if new_data_months.index.size > 1:
        print("\nADVARSEL: Mer enn én måned i nye data")
        input("Press Enter for å fortsette...")

    already_in_master = [m for m in new_data_months.index if m in master_months.index]
    if already_in_master:
        print(f"\nADVARSEL: Måned finnes allerede i masterdata: {already_in_master}")
        input("Press Enter for å fortsette...")


def merge_with_master_data_main(new_file="", master_file=""):
    if new_file == "":
        new_file = askopenfilename(initialdir=PATH_DATA_MAANED, title="Velg kodet månedlig spss-fil", filetypes=[("SAV", "*.sav")])
    new_file = Path(new_file)
    print(new_file)

    if master_file == "":
        master_file = askopenfilename(initialdir=PATH_DATA_MASTER, title="Velg masterfil", filetypes=[("SAV", "*.sav")])
    master_file = Path(master_file)
    print(master_file)

    print("\nLeser nye data...")
    new_data, new_meta = pyreadstat.read_sav(new_file)
    print(f"Lest {len(new_data)} rader, {len(new_data.columns)} variabler.")

    print("\nLeser masterfil...")
    master_data, master_meta = pyreadstat.read_sav(master_file)
    print(f"Lest {len(master_data)} rader, {len(master_data.columns)} variabler.")

    missing_columns = [c for c in master_data.columns if c not in new_data.columns]
    if missing_columns:
        print("\nADVARSEL: Variabler i masterfil mangler i nye data:", missing_columns)
        input("Press Enter for å fortsette...")

    new_value_labels = new_meta.variable_value_labels
    master_value_labels = master_meta.variable_value_labels
    print("\nSammenligner value labels mellom nye data og master...")
    compare_value_labels(new_value_labels, master_value_labels, ignore_vars=missing_columns)

    new_column_labels = new_meta.column_names_to_labels
    master_column_labels = master_meta.column_names_to_labels
    print("\nSammenligner variabellabels mellom nye data og master...")
    compare_column_labels(new_column_labels, master_column_labels, ignore_vars=missing_columns)

    # yymm/yyq får nye verdier hver måned (f.eks. ny yymm=2508 for august 2025);
    # disse labelene finnes ikke i master ennå og legges til før sammenslåing.
    for c in ("yymm", "yyq"):
        add_labels = {k: v for k, v in new_value_labels.get(c, {}).items() if k not in master_value_labels.get(c, {})}
        if add_labels:
            print(f"\n{c}: Legger til labels i master: {add_labels}")
            input("Press Enter for å fortsette...")
        master_value_labels[c] = master_value_labels.get(c, {}) | add_labels

    print("\nSjekker måneder...")
    check_months(new_data, master_data, master_value_labels.get("yymm"))

    print("\nSlår sammen nye data med masterfil...")
    new_data = new_data.reindex(columns=master_data.columns)
    accumulated_data = pd.concat([master_data, new_data], axis=0)
    print(f"Master hadde {len(master_data)} rader, ny fil har {len(accumulated_data)} rader etter sammenslåing.")

    today = dt.datetime.now().strftime("%y%m%d")
    output_file = f"CCI_MASTER_{today}.sav"
    output_file = asksaveasfilename(initialdir=master_file.parent, initialfile=output_file)
    if output_file != "":
        print(f"Lagrer oppdatert masterfil til {output_file}...")
        pyreadstat.write_sav(accumulated_data, output_file, column_labels=master_column_labels, variable_value_labels=master_value_labels)
        print(f"Lagret til {output_file}")

    # Crunch-append: kun radene fra denne månedens fil (identifisert via unik_id),
    # slik at de kan lastes opp separat til Crunch uten å sende inn hele masterfilen.
    if input("\nLagre siste måneds data for Crunch-append? [y/n]: ").upper() == "Y":
        wave_rows = new_data["unik_id"]
        wave_data = accumulated_data.set_index("unik_id").loc[wave_rows].reset_index()
        wave_file = new_file.stem + "_CRUNCH_APPEND.sav"
        wave_file = asksaveasfilename(initialdir=new_file.parent, initialfile=wave_file)
        if wave_file != "":
            print(f"Lagrer Crunch-append-fil til {wave_file}...")
            pyreadstat.write_sav(wave_data, wave_file, column_labels=master_column_labels, variable_value_labels=master_value_labels)
            print(f"Lagret til {wave_file}")


def main():
    root = tkinter.Tk()
    root.withdraw()

    print("VELG FIL MED KODET MÅNEDLIG DATA:\n")
    new_file = askopenfilename(title="Åpne kodet månedlig SPSS-fil", initialdir=PATH_DATA_MAANED, filetypes=[("SAV", "*.sav")])
    print("\nVELG CCI MASTERFIL:\n")
    master_file = askopenfilename(title="Åpne CCI Masterfil", initialdir=PATH_DATA_MASTER, filetypes=[("SAV", "*.sav")])

    merge_with_master_data_main(new_file, master_file)
    print("\nFerdig.")


if __name__ == "__main__":
    main()
