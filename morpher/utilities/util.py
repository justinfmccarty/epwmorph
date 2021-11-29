# coding=utf-8
"""
General utility functions, solar geometry calculations, and meteorological calculations.
"""

# imports
from math import radians, cos, sin, asin, sqrt
import metpy.calc as mpcalc
from metpy.units import units
import math
import os
from datetime import timedelta
import datetime as dt
from morpher.config import parse
from morpher.config import parse_set
from skyfield import api, almanac
import numpy as np
import pandas as pd

__author__ = "Justin McCarty"
__copyright__ = "Copyright 2020, justinmccarty"
__credits__ = ["Justin McCarty"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Justin McCarty"
__email__ = "mccarty.justin.f@gmail.com"
__status__ = "Production"


# TODO build in an input locator to set the root directory and spawn file paths based on that


def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    r = 3956  # Radius of earth in miles. Use 6371 for kilometers
    return c * r


def means(series):
    series_max = series.resample('D').max().resample('M').mean().reset_index(drop=True)
    series_min = series.resample('D').min().resample('M').mean().reset_index(drop=True)
    series_mean = series.resample('D').mean().resample('M').mean().reset_index(drop=True)
    return series_max, series_min, series_mean


def change(fut_tas, hist_tas, fut_tmax, hist_tmax, fut_tmin, hist_tmin):
    tas = fut_tas - hist_tas
    tmax = fut_tmax - hist_tmax
    tmin = fut_tmin - hist_tmin
    return tas, tmax, tmin


def calc_sat_pr(pressure, dbt, rel_hum):
    # pressure units in in Pa
    # pressure units out in kPa
    # temp units in C
    mixing = mpcalc.mixing_ratio_from_relative_humidity(pressure,
                                                        dbt,
                                                        rel_hum)
    return mpcalc.vapor_pressure(pressure * units.Pa, mixing)


def calc_partial_water_pr(pressure, dbt, rel_hum):
    # pressure units in in Pa
    # pressure units out in kPa
    # temp units in C
    # rel hum in %
    return (rel_hum * calc_sat_pr(pressure, dbt, rel_hum)) / 1000


def calc_dewpt(present_dewpt, pressure, dbt, rh):
    pw = calc_partial_water_pr(pressure, dbt, rh)
    if present_dewpt >= 0:
        epw_dewpt_fut = 6.54 + 14.526 + np.log(pw) + 0.7389 * np.log(pw) ** 2 + 0.09486 * np.log(
            pw) ** 3 + 0.4569 * pw ** 0.1984
    else:
        epw_dewpt_fut = 6.09 + 12.608 * np.log(pw) + 0.4959 * np.log(pw) ** 2
    return epw_dewpt_fut


# def calc_simple_day_angle(dayofyear):
#   return 2 * np.pi * (dayofyear-1) / 365

def calc_bday(dayofyear):
    return (360 / 365) * (dayofyear - 81)


def calc_equation_of_time(bday):
    return 9.87 * np.sin(np.deg2rad(2 * bday)) - 7.53 * np.cos(np.deg2rad(bday)) - 1.5 * np.sin(np.deg2rad(bday))


def calc_local_time_meridian(utc_offset):
    # requires the utc offset for local time zone
    # https://en.wikipedia.org/wiki/List_of_UTC_time_offsets
    return 15 * utc_offset


def calc_time_correction(longitude, local_time_meridian, equation_of_time):
    return 4 * (longitude - local_time_meridian) + equation_of_time


def calc_local_solar_time(local_time, time_correction):
    return local_time + (time_correction / 60)


def calc_hour_angle(solar_time):
    return (360 / 24) * (solar_time - 12)


def calc_declination(dayofyear):
    return 23.45 * np.sin(np.deg2rad((360 / 365) * dayofyear - 81))


def _calc_simple_day_angle(dayofyear, offset=1):
    return (2. * np.pi / 365.) * (dayofyear - offset)


def declination_spencer71(dayofyear):
    day_angle = _calc_simple_day_angle(dayofyear)
    d = (
            0.006918 -
            0.399912 * np.cos(day_angle) + 0.070257 * np.sin(day_angle) -
            0.006758 * np.cos(2. * day_angle) + 0.000907 * np.sin(2. * day_angle) -
            0.002697 * np.cos(3. * day_angle) + 0.00148 * np.sin(3. * day_angle)
    )
    return np.degrees(d)


def solar_zenith_analytical(latitude, hourangle, declination):
    latitude = np.radians(latitude)
    hourangle = np.radians(hourangle)
    declination = np.radians(declination)
    z = np.arccos(
        np.cos(declination) * np.cos(latitude) * np.cos(hourangle) +
        np.sin(declination) * np.sin(latitude))
    return np.degrees(z)


def calc_zenith(longitude, latitude, utc_offset, dayofyear, local_time):
    dayangle = _calc_simple_day_angle(dayofyear, offset=1)
    bday = calc_bday(dayangle)
    local_time_meridian = calc_local_time_meridian(utc_offset)
    equation_of_time = calc_equation_of_time(bday)
    time_correction = calc_time_correction(longitude, local_time_meridian, equation_of_time)
    solar_time = calc_local_solar_time(local_time, time_correction)
    hour_angle = calc_hour_angle(solar_time)
    declination = declination_spencer71(dayofyear)
    return solar_zenith_analytical(latitude, hour_angle, declination)


def calc_solar_alt(zenith):
    return 90 - zenith


def calc_rel_air_mass(zenith):
    z = np.where(zenith > 90, np.nan, zenith)
    zenith_rad = np.radians(z)
    return np.cos(zenith_rad) + 0.50572 * ((6.07995 + (90 - z)) ** - 1.6364)


def calc_atmos_precip_water(dewpt):
    return math.exp(0.07 * dewpt - 0.075)


def calc_exnor(dayofyear):
    corr_factor = 1 + 0.03344 * np.cos(360 * dayofyear / 365)
    return corr_factor * 1367


def calc_atmos_brightness(fut_dfhor, rel_air_mass, extr_norrad):
    return fut_dfhor * (rel_air_mass / extr_norrad)


def calc_atmos_clearness(fut_dfhor, fut_dnor, zenith):
    z = np.where(zenith > 90, np.nan, zenith)
    zenith_rad = np.radians(z)
    return ((fut_dfhor + fut_dnor) / (fut_dfhor + 1.041 * zenith_rad ** 3)) / (1 + 1.041 * zenith_rad ** 3)


def uas_vas_2_sfcwind(uas, vas, calm_wind_thresh=0.5, out='SPD'):
    # taken from https://xclim.readthedocs.io/en/stable/_modules/xclim/indices/_conversion.html#uas_vas_2_sfcwind
    # adapted for no xarray

    # Wind speed is the hypotenuse of "uas" and "vas"
    wind = np.hypot(uas, vas)

    # Calculate the angle
    windfromdir_math = np.degrees(np.arctan2(vas, uas))

    # Convert the angle from the mathematical standard to the meteorological standard
    windfromdir = (270 - windfromdir_math) % 360.0

    # According to the meteorological standard, calm winds must have a direction of 0°
    # while northerly winds have a direction of 360°
    # On the Beaufort scale, calm winds are defined as < 0.5 m/s
    windfromdir = np.where(windfromdir.round() == 0, 360, windfromdir)
    windfromdir = np.where(wind < calm_wind_thresh, 0, windfromdir)
    if out == 'SPD':
        return wind
    elif out == 'DIR':
        return windfromdir


def prep_wind(uas, vas):
    return uas_vas_2_sfcwind(uas, vas, out='SPD')


def persistence(hourly_clearness, rise_set, row_number):
    if row_number == 8759:
        return hourly_clearness[row_number]
    elif rise_set == 'Sunrise':
        return hourly_clearness[row_number + 1]
    elif rise_set == 'Sunset':
        return hourly_clearness[row_number - 1]
    elif row_number == 0:
        return hourly_clearness[row_number]
    elif row_number == 8759:
        return hourly_clearness[row_number]
    else:
        return (hourly_clearness[row_number - 1] + hourly_clearness[row_number + 1]) / 2


def solar_geometry(df, longitude, latitude):
    utc = int(float(parse('utcoffset')))
    longitude = float(longitude)
    latitude = float(latitude)
    df['simple_day_angle'] = df.apply(lambda x: _calc_simple_day_angle(x['dayofyear']), axis=1)
    df['bday'] = df.apply(lambda x: calc_bday(x['simple_day_angle']), axis=1)
    df['equation_of_time'] = df.apply(lambda x: calc_equation_of_time(x['bday']), axis=1)
    df['local_time_meridian'] = df.apply(lambda x: calc_local_time_meridian(utc), axis=1)
    df['time_correction'] = df.apply(lambda x: calc_time_correction(longitude,
                                                                    x['local_time_meridian'],
                                                                    x['equation_of_time']), axis=1)
    df['local_solar_time'] = df.apply(lambda x: calc_local_solar_time(x['hour'],
                                                                      x['time_correction']), axis=1)
    df['hour_angle'] = df.apply(lambda x: calc_hour_angle(x['local_solar_time']), axis=1)
    df['declination'] = df.apply(lambda x: declination_spencer71(x['dayofyear']), axis=1)
    df['zenith'] = df.apply(lambda x: calc_zenith(longitude,
                                                  latitude,
                                                  utc,
                                                  x['dayofyear'],
                                                  x['hour']), axis=1)
    # df['solar_alt'] = df.apply(lambda x: calc_solar_alt(x['zenith']),axis=1)
    print(df['time_correction'].max())
    return df


def calc_clearness(new_glohor, exthor):
    days = list(range(1, 365 + 1, 1))

    df = pd.DataFrame()
    df['exthor'] = exthor
    df['glohor'] = new_glohor.values

    def divide_clearness(x, y):
        if y == 0:
            return 0
        else:
            return np.divide(x, y)

    def calc_clearness_hourly(df):
        clearness = df.apply(lambda x: divide_clearness(x['glohor'], x['exthor']), axis=1)
        return clearness.values

    def calc_clearness_daily(df):
        daily = df.resample('D').sum()
        clearness_daily = daily.apply(lambda x: divide_clearness(x['glohor'], x['exthor']), axis=1)
        return clearness_daily.values

    clearness = calc_clearness_hourly(df)
    clearness_daily = calc_clearness_daily(df)

    clearness_day_list = dict(zip(days, clearness_daily.tolist()))
    return clearness, clearness_day_list


def calc_rise_set(df, latitude, longitude):
    ts = api.load.timescale()
    eph = api.load('de421.bsp')

    location = api.Topos(latitude, longitude)

    year = int(df['year'][0:1].values)

    t0 = ts.utc(year - 1, 12, 31, 0)
    t1 = ts.utc(year + 1, 1, 2, 0)

    t, y = almanac.find_discrete(t0, t1, almanac.sunrise_sunset(eph, location))
    times = pd.Series(t.utc_datetime()).rename('datetimes')
    times = times + timedelta(hours=-8)
    keys = pd.Series(y).rename('Rise_Set')
    keys = pd.Series(np.where(keys == 0, 'Sunset', 'Sunrise')).rename('Rise_Set')
    join = pd.concat([times, keys], axis=1)
    join.set_index(join['datetimes'], inplace=True)
    join['year'] = join['datetimes'].dt.year
    join['month'] = join['datetimes'].dt.month
    join['day'] = join['datetimes'].dt.day
    join['hour'] = join['datetimes'].dt.hour
    join['minute'] = 0
    join = join[join['year'] == year]
    join['Timestamp'] = join.apply(lambda row: dt.datetime(row.year, row.month, row.day, row.hour), axis=1)
    join.set_index('Timestamp', inplace=True)
    join_sub = pd.DataFrame(join['Rise_Set'])
    join_sub['dtime'] = join.index
    df['dtime'] = df.index
    df = df.merge(join_sub, how='left', left_on='dtime', right_on='dtime')
    df['Rise_Set'] = df['Rise_Set'].fillna('Neither')
    df.set_index(df['dtime'], inplace=True)

    return pd.Series(df['Rise_Set'].values)


def query_epw_period(epw_orig_path):
    record = pd.read_csv(epw_orig_path, skiprows=3).iloc[1, 1]
    record_years_start = record.split('=')[2].split(';')[0].split('-')[0]
    record_years_end = record.split('=')[2].split(';')[0].split('-')[1]
    return record_years_start, record_years_end


def set_config_loop(row):
    settings_df = pd.DataFrame(pd.read_csv(os.path.join(parse('epwdir'), 'epwlist.csv'))).astype(str)
    parse_set('epw', settings_df['epw_file'][row])
    start, end = query_epw_period(parse('epw'))
    parse_set('baselinestart', start)
    parse_set('baselineend', end)
    parse_set('project-name', settings_df['location'][row])
    parse_set('elevation', settings_df['elevation'][row])
    parse_set('latitude', settings_df['latitude'][row])
    parse_set('longitude', settings_df['longitude'][row])
    parse_set('utcoffset', settings_df['utc'][row])
    return print('Configuration file set for this loop.')


def build_epw_list():
    df = pd.DataFrame()
    epwdir = parse('epwdir')
    epw_files = [f for f in os.listdir(epwdir) if f.endswith('.epw')]
    for filepath in epw_files:
        # print(os.path.join(epwdir,filepath))
        data = pd.read_csv(os.path.join(epwdir, filepath), header=None, nrows=1, usecols=[1, 2, 3, 4, 5, 6, 7, 8, 9])
        data = data.rename(columns={1: 'location',
                                    2: 'province',
                                    3: 'country',
                                    4: 'type',
                                    5: 'usaf',
                                    6: 'longitude',
                                    7: 'latitude',
                                    8: 'utc',
                                    9: 'elevation'})
        data['epw_file'] = os.path.join(epwdir, filepath)
        data['utc'] = data['utc'].astype(float).astype(int)
        df = df.append(data, ignore_index=True)
    df.to_csv(os.path.join(epwdir, 'epwlist.csv'))
    return df


def dni(ghi, dhi, zenith, clearsky_dni=None,
        clearsky_tolerance=1.1,
        zenith_threshold_for_zero_dni=88.0,
        zenith_threshold_for_clearsky_limit=80.0):
    # https://pvlib-python.readthedocs.io/en/stable/_modules/pvlib/irradiance.html#dirint

    # calculate DNI
    dni = (ghi - dhi) / np.cos(np.radians(zenith))

    # cutoff negative values
    if dni < 0:
        dni = 0
    else:
        dni = dni

    # set non-zero DNI values for zenith angles >=
    # zenith_threshold_for_zero_dni to NaN
    if zenith >= zenith_threshold_for_zero_dni and dni != 0:
        dni = 0
    else:
        dni = dni

    # correct DNI values for zenith angles greater or equal to the
    # zenith_threshold_for_clearsky_limit and smaller than the
    # upper_cutoff_zenith that are greater than the clearsky DNI (times
    # clearsky_tolerance)
    if clearsky_dni is not None:
        max_dni = clearsky_dni * clearsky_tolerance
        dni[(zenith >= zenith_threshold_for_clearsky_limit) &
            (zenith < zenith_threshold_for_zero_dni) &
            (dni > max_dni)] = max_dni
    return dni


