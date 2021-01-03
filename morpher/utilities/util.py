# coding=utf-8
"""
General utility functions, solar geometry calculations, and meteorological calculations.
"""

# imports
from math import radians, cos, sin, asin, sqrt
import metpy.calc as mpcalc
from metpy.units import units
import math
from datetime import timedelta
import datetime as dt
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
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 3956 # Radius of earth in miles. Use 6371 for kilometers
    return c * r

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
    if present_dewpt>=0:
        epw_dewpt_fut = 6.54 + 14.526 + np.log(pw) + 0.7389 * np.log(pw)**2 + 0.09486 * np.log(pw)**3 + 0.4569 * pw**0.1984
    else:
        epw_dewpt_fut = 6.09 + 12.608 * np.log(pw) + 0.4959 * np.log(pw)**2
    return epw_dewpt_fut

def calc_simple_day_angle(dayofyear):
  return 2 * np.pi * (dayofyear-1) / 365

def calc_bday(dayofyear):
  return (360/365)*(dayofyear-81)

def calc_equation_of_time(bday):
  return 9.87*np.sin(np.deg2rad(2*bday))-7.53*np.cos(np.deg2rad(bday))-1.5*np.sin(np.deg2rad(bday))

def calc_local_time_meridian(utc_offset):
  # requires the utc offset for local time zone
  # https://en.wikipedia.org/wiki/List_of_UTC_time_offsets
  return 15*utc_offset

def calc_time_correction(longitude, local_time_meridian, equation_of_time):
  return 4 * (longitude - local_time_meridian) + equation_of_time

def calc_local_solar_time(local_time, time_correction):
  return local_time + (time_correction / 60)

def calc_hour_angle(solar_time):
  return (360/24) * (solar_time-12)

def calc_declination(dayofyear):
  return 23.45*np.sin(np.deg2rad((360/365)*dayofyear-81))

def calc_solar_altitude(longitude, latitude, utc_offset, dayofyear, local_time):
  dayangle = calc_simple_day_angle(dayofyear)
  bday = calc_bday(dayangle)
  local_time_meridian = calc_local_time_meridian(utc_offset)
  equation_of_time = calc_equation_of_time(bday)
  time_correction = calc_time_correction(longitude, local_time_meridian, equation_of_time)
  solar_time = calc_local_solar_time(local_time, time_correction)
  hour_angle = calc_hour_angle(solar_time)
  declination = calc_declination(dayofyear)
  return np.rad2deg(np.arcsin(np.sin(np.deg2rad(latitude))*np.sin(np.deg2rad(declination)) \
                   +np.cos(np.deg2rad(latitude))*np.cos(np.deg2rad(declination)) \
                   *np.cos(np.deg2rad(hour_angle))))

def calc_zenith(solar_altitude):
  return 90 - solar_altitude

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
  return ((fut_dfhor + fut_dnor) / (fut_dfhor + 1.041 * zenith_rad**3)) / (1 + 1.041 * zenith_rad**3)

def uas_vas_2_sfcwind(uas,vas,calm_wind_thresh=0.5,out='SPD'):
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
  if out=='SPD':
    return wind
  elif out=='DIR':
    return windfromdir

def prep_wind(uas, vas):
  return uas_vas_2_sfcwind(uas,vas,out='SPD'

def persistence(hourly_clearness, rise_set, row_number):
    if rise_set == 'Sunrise':
        return hourly_clearness[row_number + 1]
    elif rise_set == 'Sunset':
        return hourly_clearness[row_number - 1]
    else:
        clearness = np.where(row_number < 8759,
                             hourly_clearness[row_number - 1] + hourly_clearness[row_number] / 2,
                             0)
        return clearness

def solar_geometry(df, longitude, latitude):
    df['simple_day_angle'] = df.apply(lambda x: calc_simple_day_angle(x['dayofyear']), axis=1)
    df['bday'] = df.apply(lambda x: calc_bday(x['simple_day_angle']), axis=1)
    df['equation_of_time'] = df.apply(lambda x: calc_equation_of_time(x['bday']), axis=1)
    df['local_time_meridian'] = df.apply(lambda x: calc_local_time_meridian(-8), axis=1)
    df['time_correction'] = df.apply(lambda x: calc_time_correction(longitude,
                                                                         x['local_time_meridian'],
                                                                         x['equation_of_time']), axis=1)
    df['local_solar_time'] = df.apply(lambda x: calc_local_solar_time(x['hour'],
                                                                           x['time_correction']), axis=1)
    df['hour_angle'] = df.apply(lambda x: calc_hour_angle(x['local_solar_time']), axis=1)
    df['declination'] = df.apply(lambda x: calc_declination(x['dayofyear']), axis=1)
    df['solar_alt'] = df.apply(lambda x: calc_solar_altitude(longitude,
                                                              latitude,
                                                              -8,
                                                              x['dayofyear'],
                                                              x['hour']), axis=1)
    return df

def calc_clearness(new_glohor, exthor):
    days = list(range(1, 365 + 1, 1))

    def calc_clearness_hourly(new_glohor, exthor):
        return pd.Series(new_glohor / exthor).rename("clearness").fillna(0)

    def calc_clearness_daily(new_glohor, exthor):
        daily = pd.Series(new_glohor.resample('D').sum() / exthor.resample('D').sum())
        return daily.rename("clearness").fillna(0)

    clearness = calc_clearness_hourly(new_glohor, exthor)
    clearness_daily = calc_clearness_daily(new_glohor, exthor)

    clearness_day_list = dict(zip(days, clearness_daily.tolist()))
    return clearness, clearness_day_list

def calc_rise_set(df, latitude, longitude):
    ts = api.load.timescale()
    eph = api.load('de421.bsp')

    location = api.Topos(latitude, longitude)

    t0 = ts.utc(2011 - 1, 12, 31, 0)
    t1 = ts.utc(2011 + 1, 1, 2, 0)

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
    join = join[join['year'] == 2011]
    join['Timestamp'] = join.apply(lambda row: dt.datetime(row.year, row.month, row.day, row.hour), axis=1)
    join.set_index('Timestamp', inplace=True)

    join_sub = pd.DataFrame(join['Rise_Set'])
    join_sub['dtime'] = join.index
    df['dtime'] = df.index
    df = df.merge(join_sub, how='left', left_on='dtime', right_on='dtime')
    df['Rise_Set'] = df['Rise_Set'].fillna('Neither')
    df.set_index(df['dtime'], inplace=True)
    return df['Rise_Set']