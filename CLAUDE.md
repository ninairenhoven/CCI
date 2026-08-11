# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A set of Norwegian-language, interactive Python scripts that process monthly survey data for Opinion's CCI
(Consumer Confidence Index / Forbrukermeteret) and the LO tracker survey ("Befolkningsundersøkelse"), and
produce reports/plots for subscribers and Norges Bank. There is no application, API, or test suite — this is
a toolset run by hand, one script at a time, once a month.

## Running the scripts

There is no build, lint, or test tooling in this repo — install dependencies with `pip install -r requirements.txt`
and run scripts directly. All scripts are interactive: they open Tkinter file-picker dialogs, print progress/data
to the console, and block on `input()` prompts (both for y/n decisions and for warnings the operator must
acknowledge before continuing). They are meant to be run from a terminal on Windows, not imported as a library or
run headlessly — e.g. `py -i CCI_LO_Mobi_prepare_files.py`, or via the existing `python_augment_spss_CCI_LO.bat`
launcher (currently points at the legacy `CCI_LO_augment_split_merge.py`, not the standalone scripts below).

Because everything depends on OneDrive/SharePoint-mounted folders under `Path.home()` (see `PATH_*` constants in
`CCI_modules/CCI_utils.py`) and on real monthly `.sav`/`.csv` data files that aren't in this repo, these scripts
can't be run or meaningfully tested outside the intended user's machine.

## Monthly workflow (entry-point scripts, run in order)

1. **`CCI_LO_Mobi_prepare_files.py`** — reads a raw monthly SPSS file, computes CCI/Kjøpsindeks scores per
   respondent, recodes background variables, adds tracker variables (`yymm`, `yyq`, `unik_id`, LO's `Måned`/`Kvartal`
   counters), then splits the result into separate `.sav` files for CCI, LO, and Mobilitetsbarometeret.
2. **`CCI_master_merge.py`** — merges that month's CCI file into the accumulated CCI master `.sav`
   file, after comparing value/column labels between the new data and the master and checking for already-present
   months.
3. **`CCI_prosess.py`** — the downstream reporting pipeline: computes Norway's monthly index (`CCI_Norge.py`),
   downloads and combines EU CCI data (`CCI_europe.py`), writes Excel reports for subscribers and a Norges Bank CSV
   (`CCI_excelrapporter.py`), and generates PNG charts (`CCI_plotting.py`).

`CCI_LO_augment_split_merge.py` (repo root) is the original, pre-split version of steps 1–2, kept for reference;
new work on augment/split/merge should go in `CCI_LO_Mobi_prepare_files.py` / `CCI_master_merge.py`, not
this file or the `CCI_modules/CCI_LO_augment_spss.py` / `CCI_LO_split_save_spss.py` / `CCI_merge_with_master.py`
modules it wraps.

## Architecture

- **`CCI_modules/CCI_utils.py`** is the shared foundation almost every other file imports from: filesystem paths
  (all under the user's OneDrive/SharePoint sync folders), the SPSS raw-variable-name ↔ index-name mapping
  (`SPSS_VARIABLE_MAPPING`), the CCI/Kjøpsindeksen question-set definitions (`CCI_DEFINISJON`,
  `KJOPSINDEKS_DEFINISJON`), scale-coding constants (`SCALE_SELECTION`/`SCALE_DEFINITION`/`SCALE_SCORES`), and
  generic readers for the accumulated historical CSVs (`read_norway_historical_data`, `read_combined_historical_data`).
  `CCI_LO_Mobi_prepare_files.py` and `CCI_master_merge.py` at the repo root deliberately import shared
  paths/constants from here rather than duplicating them, while keeping their own processing logic self-contained
  (no dependency on the other `CCI_modules` files).

- **Two distinct scoring methodologies exist for the same survey questions** — don't conflate them:
  - *Per-respondent linear score* (`-100..100`, averaged): used in `CCI_LO_Mobi_prepare_files.py`'s
    `VALUE_SCORE_MAP`/`calculate_respondent_CCI_scores`, applied at the individual-respondent level before saving
    to SPSS.
  - *Aggregate net score* (`% top-box − % bottom-box`, i.e. `up`/`down`/`net`): used in `CCI_modules/CCI_Norge.py`'s
    `compute_scores`/`calculate_question_scores` and consumed throughout `CCI_excelrapporter.py`/`CCI_plotting.py`.
    This path depends on `CCI_modules.CCI_utils.select_and_apply_scale`, which maps raw answer codes to categorical
    labels (`PP`/`P`/`.`/`M`/`MM`) rather than numeric scores — that categorical step is load-bearing for the
    weighted-percentage calculation in `CCI_Norge.calculate_question_scores`, so it can't be collapsed into a
    direct numeric mapping without breaking that consumer.

- **Data hand-off is entirely file-based**: SPSS `.sav` files for survey data, CSV for accumulated historical
  index data (`CCI_og_delindekser_Norge_akkumulert.csv`, `read_combined_historical_data`'s target), and Excel for
  subscriber reports (built from a template in `PATH_GENERERTE_FILER/TEMPLAT/`, see `CCI_excelrapporter.py`). There
  is no database.

- **Warnings block on purpose.** Throughout the augment/merge scripts, `ADVARSEL`/`NB` conditions (unmapped recode
  values, missing variables, duplicate variable names, months already present in the master file, mismatched value
  labels, etc.) print and then call `input("Press Enter for å fortsette...")` rather than raising or silently
  continuing — this is intentional so the operator reviews unexpected data before the run proceeds, not a bug to
  "fix" by removing the prompt.

- **`unik_id`** encodes `yymm * 100_000 + row_index`, so it assumes fewer than 100,000 respondents per month.
  **`Måned`/`Kvartal`** in the LO output count from January 2021 (`Måned` 1), the tracker's start date.

## Language

All user-facing strings (prompts, warnings, sheet/column names, comments) are Norwegian, matching the source data
and its consumers. Keep new code consistent with this.
