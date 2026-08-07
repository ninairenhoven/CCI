import pandas as pd
import numpy as np
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.dates  as mdates
from types import SimpleNamespace
import os
from pathlib import Path

import tkinter
from tkinter.filedialog import askopenfilename

from CCI_modules.CCI_utils import PATH_PLOTS, QUESTION_TITLES
from CCI_modules.CCI_utils import read_norway_historical_data, read_combined_historical_data

#from CCI_utils import PATH_PLOTS, QUESTION_TITLES
#from CCI_utils import read_norway_historical_data, read_combined_historical_data


#from CCI_excelrapporter import read_norway_akk_data


#######################################################################
#  PLOTTING
###################################################################33

OCOLORS = SimpleNamespace(**{
    'orange':'#F26649',
    'aqua':'#71c3b4',
    'aqua4': '#45A290',
    'blue':'#1C7CA1',
    'blue3':"#5BBDE2",
    'darkblue':'#155D79',
    'yellow': '#FCE164',
    'yellow4':'#FAD00E',
    'red':'#f15f5b',
    'red4':'#E51914',
    'darkred':'#99110D',
    'darkgrey': '#515350',
    'grey': '#969995',
    'grey1': '#DCDDDC',
    'grey2': '#B9BBB8',
    'backgroundyellow':'#fffef7'
    }
)
#print(OCOLORS)

NORGE_PLOTS = {
    'Egen økonomi.png': ['EU01_Egen_oko_naa', 'EU02_Egen_oko_12mnd'],
    'Landets økonomi.png': ['EU03_Landets_oko_naa', 'EU04_Landets_oko_12mnd'],
    'CCI.png': ['CCI', None]
}

LINEPLOTS = [
    'Kjopsindeksen',
    'EU09_Store_kjop_12mnd',
    'EU13_Bilkjop_12mnd',
    'EU14_Boligkjop_12mnd',
    'EU15_Oppussing_12mnd'
]

UTLAND_PLOTS = {
    'CCI_norden_og_eu_siste_aar.png' : {
        'Nordic.COF': 'Norden',
        'SE.COF.B.M': 'Sverige',
        'DK.COF.B.M': 'Danmark',
        'NO.COF.B.M': 'Norge',
        'FI.COF.B.M': 'Finland',
        'EA.COF.B.M': 'Euro-landene'
        },
    'CCI_eu_land_siste_aar.png' : {
        'PT.COF.B.M': 'Portugal',
        'IT.COF.B.M': 'Italia',
        'EL.COF.B.M': 'Hellas',
        'ES.COF.B.M': 'Spania',
        'DE.COF.B.M': 'Tyskland',
        'FR.COF.B.M': 'Frankrike'
        }  
    }


PLT_SIZE = (5.1, 2.3) 
DPI=320

def line_chart(df, start_date=dt.date(2007,5,1), end_date=dt.date.today(), colors=[]):
    colors = colors + [OCOLORS.darkgrey, OCOLORS.yellow4, OCOLORS.aqua4,
        OCOLORS.darkred, OCOLORS.blue3, OCOLORS.orange]
    data = df.loc[start_date:end_date]
    data.index = data.index.to_period('M').start_time 
    # Sort columns by last row
    data = data.sort_values(data.last_valid_index(), axis=1, ascending=False)
    fig, ax = plt.subplots(1,1,dpi=DPI) #figsize=(5.25,3.4), 
    ax.set_prop_cycle(color=colors)
    ax.plot(data, label=data.columns, linewidth=0.7, alpha=0.9)
    #daterange = data.index.max().date()-start_date
    ax.set_xlim(left = data.index.min().date(), right = data.index.max().date())
    #ax.legend(loc='lower center', bbox_to_anchor=(0.5, -0.5), fontsize=5, ncol=len(data.columns))
    ax.legend(loc='center left', bbox_to_anchor=(1.01, 0.5), fontsize=5, ncol=1, frameon=False)
    #ax.legend(loc='lower center', fontsize=5, ncol=len(data.columns))
    format_chart(fig, ax)
    return fig, ax    


def bar_and_line_with_dateindex(df, bar_variable=None, line_variable=None):
    # Get data, remove nan
    vars = [bar_variable, line_variable]
    vars = [var for var in vars if var is not None]
    data = df[vars].dropna(how='all')
    # Set index
    data.index = data.index.to_period('M').start_time
    # Prepare plot
    fig, ax = plt.subplots(1,1,dpi=DPI) #, figsize=PLT_SIZE, 
    ax.xaxis_date()
    x_values = data.index.map(lambda x:mdates.date2num(x))
    bar_width = x_values.to_series().diff().min()*0.75
    xrange = (x_values.min()-1.5*bar_width, x_values.max()+1.5*bar_width)
    # Plot data
    if bar_variable:
        ax.bar(x_values, data[bar_variable], label=QUESTION_TITLES[bar_variable],
            color=OCOLORS.blue3, align='center', width=bar_width) #cci_blue
    if line_variable:
        ax.plot(x_values, data[line_variable], label=QUESTION_TITLES[line_variable],
                color=OCOLORS.orange, alpha=0.8, linewidth=0.8) #red
    ax.set_xlim(xrange)
    return fig, ax


def format_chart(fig,ax, title='', time_ticks='', labelrotation=0, figsize=PLT_SIZE):
    fig.set_size_inches(figsize[0], figsize[1])
    ax.xaxis.label.set_visible(False)
    if time_ticks == 'year':
        ax.xaxis.set_major_locator(mdates.YearLocator())
    elif time_ticks == 'month':
        ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.tick_params(axis='x', labelrotation=labelrotation, labelsize=5)
    ax.tick_params(axis='y', length=0, labelsize=5)
    ax.tick_params(colors=OCOLORS.grey1, labelcolor=OCOLORS.darkgrey)
    ax.grid(color=OCOLORS.grey1, linewidth=0.5) #'#FFFFFF' OCOLORS.grey2
    #ax.spines['bottom'].set_color(OCOLORS.grey2)
    #ax.spines[['top','right','left']].set_visible(False)
    ax.spines[['top','bottom','right','left']].set_color(OCOLORS.grey1)
    ax.spines[['top','bottom','right','left']].set_linewidth(0.5)
    ax.set_axisbelow(True)
    if title != '':
        ax.set_title(title, fontsize=8)
    ax.set_facecolor(OCOLORS.backgroundyellow) #"#F0F0F0")
    fig.patch.set_facecolor(OCOLORS.backgroundyellow)
    fig.tight_layout()


def generate_plots(norge_data, utland_data):
    path_saveplots = PATH_PLOTS.joinpath('plots_' + dt.datetime.now().strftime('%Y-%m'))
    if os.path.isdir(path_saveplots):
        print('\nFolder exists, existing plots will be overwritten: {}'.format(path_saveplots))
        inp = input('Continue? Y/N: ')
        if inp.upper()=='N':
            return
    else:
        os.mkdir(path_saveplots)
        print('\nCreated folder: {}\n'.format(path_saveplots))
    #
    for plotname, vars in NORGE_PLOTS.items():
        fig, ax = bar_and_line_with_dateindex(norge_data, vars[0], vars[1])
        format_chart(fig, ax, time_ticks='year', labelrotation=45)
        filename = os.path.join(path_saveplots, plotname)
        plt.savefig(filename, bbox_inches='tight')
        print('Saved plot '+filename)
    #
    for var in LINEPLOTS:
        fig, ax = bar_and_line_with_dateindex(norge_data, None, var)
        format_chart(fig, ax, time_ticks='year', labelrotation=45)
        filename = os.path.join(path_saveplots, var+'_line.png')
        plt.savefig(filename, bbox_inches='tight')
        print('Saved plot '+filename)
    #
    for plotname, d in UTLAND_PLOTS.items():
        data = utland_data[d.keys()].rename(columns=d)
        # Behold rader med mer enn ett datapunkt (dvs fjerner siste måned med bare Norge fra Norden-plottet)
        count_valid = (~data.isna()).sum(axis=1)
        end_date = data.index[count_valid>1].max()
        #end_date = data.dropna(how='all').index.max()
        start_date = end_date-dt.timedelta(days=(365.25+31))
        fig, ax = line_chart(data, start_date=start_date, end_date=end_date)
        format_chart(fig, ax, time_ticks='month', labelrotation=45, figsize=(5.1,1.8))
        filename = os.path.join(path_saveplots, plotname)
        plt.savefig(filename, bbox_inches='tight')
        print('Saved plot '+filename)  



def cci_plotting_main():
    norge_data = read_norway_historical_data(detailed=False)
    #norge_data.index = pd.to_datetime(norge_data.index, format='%d/%m/%Y')

    #filename_utland = askopenfilename(title="Åpne samlet historisk fil for EU inkl. Norge", initialdir=PATH_HISTORISKE_DATA, filetypes=[('CSV','*.csv')])
    #utland_data = pd.read_csv(filename_utland, index_col=0)
    #utland_data.index = pd.to_datetime(utland_data.index, format='%m/%d/%Y')
    utland_data = read_combined_historical_data()

    generate_plots(norge_data, utland_data)



################################################################3
# Test ny/gammel norge-fil

#filename_norge_gml = "C:/Users/NinaIrenHoven/Opinion AS/Opinion SharePoint - ForbrukerMeteret/DATA AKKUMULERT/historiske data eu og norge/arkiv/CCI_Norge_historisk.csv"
#norge_data = pd.read_csv(filename_norge_gml, index_col=0)
#norge_data.index = pd.to_datetime(norge_data.index, format='%d/%m/%Y')

#norge_akk_data = read_norway_akk_data()
#testdata = norge_akk_data.xs('net', level=1, axis=1)
#testdata.columns = testdata.columns.str.replace(r'^(EU|NO)\d{2}_', '', regex=True)
#testdata.index = pd.to_datetime(testdata.index, dayfirst=True)

#diff = testdata-norge_data


