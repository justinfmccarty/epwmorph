# coding=utf-8
"""
Read and write epw with pandas.
"""

# imports
from morpher.config import parse
import pandas as pd
from epw import epw  # https://github.com/building-energy/epw

__author__ = "Justin McCarty"
__copyright__ = "Copyright 2020, justinmccarty"
__credits__ = ["Justin McCarty"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Justin McCarty"
__email__ = "mccarty.justin.f@gmail.com"
__status__ = "Production"


def epw_to_dataframe(weather_path, urban=False):
    epw_labels = ['year', 'month', 'day', 'hour', 'minute', 'datasource', 'drybulb_C', 'dewpoint_C', 'relhum_percent',
                  'atmos_Pa', 'exthorrad_Whm2', 'extdirrad_Whm2', 'horirsky_Whm2', 'glohorrad_Whm2', 'dirnorrad_Whm2',
                  'difhorrad_Whm2', 'glohorillum_lux', 'dirnorillum_lux', 'difhorillum_lux', 'zenlum_lux',
                  'winddir_deg',
                  'windspd_ms', 'totskycvr_tenths', 'opaqskycvr_tenths', 'visibility_km', 'ceiling_hgt_m',
                  'presweathobs', 'presweathcodes', 'precip_wtr_mm', 'aerosol_opt_thousandths', 'snowdepth_cm',
                  'days_last_snow', 'Albedo', 'liq_precip_depth_mm', 'liq_precip_rate_Hour']
    if urban == False:
        df = pd.read_csv(weather_path, skiprows=8, header=None, names=epw_labels).drop('datasource', axis=1)
    else:
        df = pd.read_csv(weather_path, skiprows=8, header=None, index_col=False, usecols=list(range(0, 35)),
                         names=epw_labels).drop('datasource', axis=1)

    df['hour'] = df['hour'].astype(int)
    if df['hour'][0] == 1:
        print('EPW file hours reduced from 1-24h to 0-23h')
        df['hour'] = df['hour'] - 1
    else:
        print('EPW file hours maintained at 0-23hr')
    df['minute'] = 0
    return df


def edit_epw(new_df, year=None):
    base_epw = parse('epw')
    a = epw()
    a.read(base_epw)
    new_epw = a.dataframe
    if year == None:
        pass
    else:
        new_epw['Year'] = year
    new_epw['Dry Bulb Temperature'] = new_df['drybulb_C']
    new_epw['Relative Humidity'] = new_df['relhum_percent']
    new_epw['Dew Point Temperature'] = new_df['dewpoint_C']
    new_epw['Atmospheric Station Pressure'] = new_df['atmos_Pa']
    new_epw['Global Horizontal Radiation'] = new_df['glohorrad_Whm2']
    new_epw['Direct Normal Radiation'] = new_df['dirnorrad_Whm2']
    new_epw['Diffuse Horizontal Radiation'] = new_df['difhorrad_Whm2']
    new_epw['Wind Speed'] = new_df['windspd_ms']
    new_epw['Total Sky Cover'] = new_df['totskycvr_tenths']
    new_epw['Opaque Sky Cover (used if Horizontal IR Intensity missing)'] = new_df['opaqskycvr_tenths']
    # new_epw['Horizontal Infrared Radiation Intensity'] = new_df['horirsky_Whm2']
    # new_epw['Precipitable Water'] = new_df['precip_wtr_mm']
    # new_epw['Extraterrestrial Horizontal Radiation'] = new_df['exthorrad_Whm2']
    # new_epw['Extraterrestrial Direct Normal Radiation'] = new_df['extdirrad_Whm2']
    # new_epw['Global Horizontal Illuminance'] = new_df['glohorillum_lux']
    # new_epw['Direct Normal Illuminance'] = new_df['dirnorillum_lux']
    # new_epw['Diffuse Horizontal Illuminance'] = new_df['difhorillum_lux']
    # new_epw['Zenith Luminance'] = new_df['zenlum_lux']
    return a


def out_epw(percentile, new_df, outputpath, pathway, year=None):
    edit_epw(new_df, year).write(outputpath)
    return print(f'Morphed {percentile}th percentile {year} EPW saved to {outputpath} for {pathway}.')
