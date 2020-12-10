# coding=utf-8
"""
Query the NOAA API for hourly records of weather data in preparation for bias correction.
"""

# imports
from morpher.config import parse
import os
from tqdm import tqdm
import xarray as xr
import gcsfs
import tqdm
import intake
import dask
from dask.diagnostics import progress
import fsspec
import pandas as pd
import metpy
import requests
import json
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime as dt

__author__ = "Justin McCarty"
__copyright__ = "Copyright 2020, justinmccarty"
__credits__ = ["Justin McCarty"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Justin McCarty"
__email__ = "mccarty.justin.f@gmail.com"
__status__ = "Production"

# set universal variables
config_file = os.path.join(os.path.dirname(__file__), 'default.config')

def stationlist():
    stationlist = pd.read_csv('https://www1.ncdc.noaa.gov/pub/data/noaa/isd-history.csv', dtype='str')
    return stationlist


def closest(stationlist):
    latitude = parse('latitude')
    longitude = parse('longitude')
    station_df = stationlist
    station_df[]
    station_df['BEGIN'] = pd.to_datetime(station_df['BEGIN'], format='%y%m%d')



def processnoaa():
    usaf = parse('usaf')
    wban = parse('wban')
    if 'none' in usaf:
        print()
    else:
        USAF = usaf
        WBAN = wban

        print()

    df = pd.read_csv('https://www.ncei.noaa.gov/data/global-hourly/access/{YEAR}/{USAF}{WBAN}.csv'.format(YEAR=1999,USAF=USAF,WBAN=WBAN),
                     dtype=object)
    wind = df.WND.str.split(pat=',', expand=True).set_index(df.DATE).rename(columns={0: 'wind_dir',
                                                                                     1: 'wind_dirqc',
                                                                                     2: 'wind_type',
                                                                                     3: 'wind_spd',
                                                                                     4: 'wind_spdqc'})

    sky = df.CIG.str.split(pat=',', expand=True).set_index(df.DATE).rename(columns={0: 'sky_clg',
                                                                                    1: 'sky_clgqc',
                                                                                    2: 'sky_clgmethod',
                                                                                    3: 'sky_cavok'})

    vis = df.VIS.str.split(pat=',', expand=True).set_index(df.DATE).rename(columns={0: 'vis_dist',
                                                                                    1: 'vis_distqc',
                                                                                    2: 'vis_variable',
                                                                                    3: 'vis_variableqc'})

    temp = df.TMP.str.split(pat=',', expand=True).set_index(df.DATE).rename(columns={0: 'temp_cels',
                                                                                     1: 'temp_cels_qc'})

    dew = df.DEW.str.split(pat=',', expand=True).set_index(df.DATE).rename(columns={0: 'dew_temp',
                                                                                    1: 'dew_tempqc'})

    psl = df.SLP.str.split(pat=',', expand=True).set_index(df.DATE).rename(columns={0: 'psl_hpscal',
                                                                                    1: 'psl_hpscalqc'})

    dfall = pd.concat([wind, sky, vis, temp, dew, psl], axis=1)
    dfall = dfall.replace(['999', '9', '9999', '99999', '999999'], np.nan)
    dfall.index = pd.to_datetime(dfall.index)
    del dfall['wind_type']
    del dfall['sky_clgmethod']
    del dfall['sky_cavok']
    del dfall['vis_variable']

    def check(x):
        if '+' in x:
            x.replace('+', '')
            x = float(x) / 10
        elif '-' in x:
            x.replace('-', '')
            x = float(x) * -1
            x = x / 10
        else:
            x = x / 10
        if x > 100 or x < -100:
            x = np.nan
        else:
            x = x
        return x

    dfall['temp_cels'] = dfall.apply(lambda x: check(x['temp_cels']), axis=1)
    dfall['dew_temp'] = dfall.apply(lambda x: check(x['dew_temp']), axis=1)

    dfall = dfall.fillna(method='bfill').fillna(method='ffill').astype(float)
    dfall['wind_spd'] = dfall['wind_spd'] / 10
    dfall['psl_hpscal'] = dfall['psl_hpscal'] / 10
    dfobs = dfall[['wind_dir', 'wind_spd', 'sky_clg',
                   'temp_cels', 'dew_temp', 'psl_hpscal']].resample('1H').mean()

    def rhcalc(temp, dew):  # magnus approximation
        return 100 * (np.exp((17.625 * dew) / (243.04 + dew)) / np.exp((17.625 * temp) / (243.04 + temp)))

    dfobs['hurs'] = dfobs.apply(lambda x: rhcalc(x['temp_cels'], x['dew_temp']), axis=1)
    dfobs = dfobs.round(1)
    return print(dfobs.head())

if __name__ == '__main__':
    processnoaa()