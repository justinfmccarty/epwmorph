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
import geopandas as gpd
import metpy
import requests
import json
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime as dt
from morpher.utilities.util import haversine
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

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


def closest():
    latitude = float(parse('latitude'))
    longitude = float(parse('longitude'))
    baselinestart = int(parse('baselinestart'))
    baselineend = int(parse('baselineend'))
    stations_list = stationlist()
    ds = pd.DataFrame()
    ds['station'] = stations_list['STATION NAME']
    ds['begin'] = pd.to_datetime(stations_list['BEGIN'], format='%Y%m%d')
    ds['end'] = pd.to_datetime(stations_list['END'], format='%Y%m%d')
    ds['latitude'] = stations_list['LAT']
    ds['longitude'] = stations_list['LON']
    start = pd.Timestamp(baselinestart-1, 12, 31)
    end = pd.Timestamp(baselineend, 12, 31)
    ds = ds[ds['begin'] < start]
    ds = ds[ds['end'] > end]
    gdf = gpd.GeoDataFrame(
        ds, geometry=gpd.points_from_xy(
            ds.longitude, ds.latitude)).set_crs(epsg=3857)
    gdf['distance'] = gdf['geometry'].apply(lambda x: haversine(x.x,
                                                                x.y,
                                                                longitude,
                                                                latitude))
    match = stations_list[stations_list.index ==
                          gdf[gdf['distance'] == gdf['distance'].min()]['station'].index.values[0]]
    usaf = match['USAF'].values[0]
    wban = match['WBAN'].values[0]
    ext = str(usaf) + str(wban)
    print(gdf[gdf['distance'] == gdf['distance'].min()]['station'].values[0])
    print(ext)
    return ext

def noaabylocation():
    baselinestart = int(parse('baselinestart'))
    baselineend = int(parse('baselineend'))
    allweather = pd.DataFrame()
    missingyears = []
    yearrange = range(baselinestart - 3, baselineend + 3, 1)
    ext = closest()
    for year in yearrange:
        print(year)
        url = 'https://www.ncei.noaa.gov/data/global-hourly/access/{y}/{e}.csv'.format(y=year, e=ext)
        req = Request(url)
        try:
            response = urlopen(req)
        except HTTPError as e:
            print('For ' + str(year) + ' the server couldn\'t fulfill the request.')
            # print('Error code: ', e.code)
            missingyears.append(year)
        except URLError as e:
            print('For ' + str(year) + ' the server couldn\'t fulfill the request.')
            # print('Reason: ', e.reason)
            missingyears.append(year)
            continue
        else:
            df = pd.read_csv(url)
            allweather = allweather.append(df, ignore_index=True)
            print('Website is working fine. Adding data to the dataframe.')
    return allweather, missingyears

def noaabyinput():
    baselinestart = int(parse('baselinestart'))
    baselineend = int(parse('baselineend'))
    usaf = parse('usaf')
    wban = parse('wban')
    allweather = pd.DataFrame()
    missingyears = []
    yearrange = range(baselinestart - 3, baselineend + 3, 1)
    ext = str(usaf)+str(wban)
    for year in yearrange:
        print(year)
        url = 'https://www.ncei.noaa.gov/data/global-hourly/access/{y}/{e}.csv'.format(y=year, e=ext)
        req = Request(url)
        try:
            response = urlopen(req)
        except HTTPError as e:
            print('For ' + str(year) + ' the server couldn\'t fulfill the request.')
            # print('Error code: ', e.code)
            missingyears.append(year)
        except URLError as e:
            print('For ' + str(year) + ' the server couldn\'t fulfill the request.')
            # print('Reason: ', e.reason)
            missingyears.append(year)
            continue
        else:
            df = pd.read_csv(url)
            allweather = allweather.append(df, ignore_index=True)
            print('Website is working fine. Adding data to the dataframe.')
    return allweather, missingyears


def processnoaa():
    if 'none' in parse('usaf'):
        weatherdata, missingyears = noaabylocation()
    else:
        weatherdata, missingyears = noaabyinput()
    df = weatherdata
    # clean up the output of the query and reformat it for comparing to the model data
    wind = df['WND'].str.split(pat=',', expand=True).set_index(df.DATE).rename(columns={0: 'wind_dir',
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

    # need to check some units and orient the strings to positives and negatives
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
    #  magnus approximation for calculating relative humidty
    def rhcalc(temp, dew):
        return 100 * (np.exp((17.625 * dew) / (243.04 + dew)) / np.exp((17.625 * temp) / (243.04 + temp)))

    dfobs['hurs'] = dfobs.apply(lambda x: rhcalc(x['temp_cels'], x['dew_temp']), axis=1)
    dfobs = dfobs.round(1)
    return dfobs

if __name__ == '__main__':
    processnoaa()