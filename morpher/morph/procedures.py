# coding=utf-8
"""
The functions used in the the morphing procedure. These are following Belcher et al.
"""

# imports
import math
from meteocalc import dew_point as calcdewpt
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


def morph_dbt(df, fut_tas, hist_tas, fut_tmax, hist_tmax, fut_tmin, hist_tmin):
    months = list(range(1, 12 + 1, 1))
    dbt_max_mean, dbt_min_mean, dbt_mean = means(df['drybulb_C'])
    tas_change, tmax_change, tmin_change = change(fut_tas, hist_tas,
                                                  fut_tmax, hist_tmax,
                                                  fut_tmin, hist_tmin)
    tas_change = dict(zip(months, tas_change))
    dbt_scale = dict(zip(months, (tmax_change - tmin_change) / (dbt_max_mean - dbt_min_mean)))
    dbt_mean = dict(zip(months, dbt_mean))
    return round(df.apply(lambda x: x['drybulb_C'] + tas_change[x['month']] + dbt_scale[x['month']] * (
                x['drybulb_C'] - dbt_mean[x['month']]), axis=1).astype(float), 1).rename("drybulb_C")


def morph_relhum(df, fut_relhum, hist_relhum):
    # requires fut_ and hist_ inputs to be monthly climatologies
    months = list(range(1, 12 + 1, 1))
    relhum_change = dict(zip(months, fut_relhum - hist_relhum))
    return df.apply(lambda x: x['relhum_percent'] + relhum_change[x['month']], axis=1).rename("relhum_percent")


def morph_pr(df, fut_pr, hist_pr):
    # requires fut_ and hist_ inputs to be monthly climatologies
    months = list(range(1, 12 + 1, 1))
    pr_change = dict(zip(months, fut_pr - hist_pr))
    return df.apply(lambda x: x['atmos_Pa'] + pr_change[x['month']], axis=1).rename("atmos_Pa")


def morph_dewpt(fut_dbt, fut_rh):
    df = pd.concat([fut_dbt, fut_rh], axis=1)
    return round(df.apply(lambda x: calcdewpt(x[0], x[1]), axis=1).astype(float), 1)


def morph_glohor(df, hist_glohor, fut_glohor):
    df['single'] = 1
    months = list(range(1, 12 + 1, 1))

    month_hours = dict(zip(months, df['single'].resample('M').sum().tolist()))  # hours
    month_glohor = dict(zip(months, df['glohorrad_Whm2'].resample('M').sum().tolist()))  # watt-hours per m2
    month_glohor_mean_list = []
    for key in month_hours:
        mean = (month_glohor[key]) / month_hours[key]
        month_glohor_mean_list.append(mean)
    month_glohor_mean_list = dict(zip(months, month_glohor_mean_list))  # watt per m2

    glohor_change = dict(zip(months, fut_glohor - hist_glohor))
    glohor_scale_list = []
    for key in month_glohor_mean_list:
        glohor_scale = 1 + (glohor_change[key] / month_glohor_mean_list[key])
        glohor_scale_list.append(glohor_scale)
    glohor_scale_list = dict(zip(months, glohor_scale_list))

    return df.apply(lambda x: x['glohorrad_Whm2'] * glohor_scale_list[x['month']], axis=1).rename(
        "glohorrad_Whm2").astype(int)

def calc_diffhor(df):
    return df.apply(lambda x: x['glohorrad_Whm2'] * (1 / (1 + math.exp(
        -5.38 + 6.63 * x['hourly_clearness'] + 0.006 * x['local_solar_time'] - 0.007 * x['solar_alt'] + 1.75 * x[
            'daily_clearness'] + 1.31 * x['persisted_index']))), axis=1).astype(int)


def calc_dirnor(df):
    return df.apply(lambda x: (x['glohorrad_Whm2'] - x['difhorrad_Whm2']) / np.sin(np.deg2rad(x['solar_alt'])),
                    axis=1).astype(int)


def calc_tsc(df, hist_clt, fut_clt):
    months = list(range(1, 12 + 1, 1))
    cc_change = dict(zip(months, ((fut_clt - hist_clt) / 10).astype(int)))
    return np.clip(df.apply(lambda x: x['totskycvr_tenths'] + cc_change[x['month']], axis=1).rename("totskycvr_tenths"),
                   0, 10).astype(int)


def calc_osc(df):
    def calc(present_tsc, totskycvr_tenths, present_osc):
        if present_tsc == 0:
            return 0
        else:
            return (totskycvr_tenths * present_osc) / present_tsc

    return df.apply(lambda x: calc(x['present_tsc'],
                                   x['totskycvr_tenths'],
                                   x['present_osc']), axis=1).astype(int)
