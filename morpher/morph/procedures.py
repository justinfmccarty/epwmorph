# coding=utf-8
"""
The functions used in the the morphing procedure. These are following Belcher et al.
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
from xclim import ensembles
from morpher.utilities.util import calc_sat_pr, calc_partial_water_pr

__author__ = "Justin McCarty"
__copyright__ = "Copyright 2020, justinmccarty"
__credits__ = ["Justin McCarty"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Justin McCarty"
__email__ = "mccarty.justin.f@gmail.com"
__status__ = "Production"

def morph_dbt(month, epw_dbt, fut_tas, fut_tmax, fut_tmin, hist_tas, hist_tmax, hist_tmin):
    # requires fut_ and hist_ inputs to be monthly climatologies
    months = list(range(1, 12 + 1, 1))
    # dict(zip(months, var))[month]
    tmax_change = fut_tmax-hist_tmax
    tmin_change = fut_tmin-hist_tmin
    dbt_max_mean = epw_dbt.resample('D').max().resample('M').mean()
    dbt_min_mean = epw_dbt.resample('D').min().resample('M').mean()
    dbt_scale = (tmax_change - tmin_change) / (dbt_max_mean - dbt_min_mean)
    tas_change = fut_tas - hist_tas
    dbt_mean = epw_dbt.resample('D').mean().resample('M').mean()
    dbt_fut = epw_dbt + tas_change + dbt_scale * (epw_dbt - dbt_mean)
    return dbt_fut

def morph_relhum(month, epw_rh, fut_relhum, hist_relhum):
    # requires fut_ and hist_ inputs to be monthly climatologies and as plain lists
    months = list(range(1,12+1,1))
    relhum_change = dict(zip(months, fut_relhum))[month] - dict(zip(months, hist_relhum))[month]
    epw_relhum_fut = epw_rh + relhum_change
    return epw_relhum_fut

def morph_dewpt(month, epw_dewpt):
    months = list(range(1, 12 + 1, 1))
    pw = calc_partial_water_pr(dict(zip(months, epw_pressure))[month],
                               dict(zip(months, epw_dbt))[month],
                               dict(zip(months, epw_rh))[month])
    if epw_dewpt>=0:
        epw_dewpt_fut = 6.54 + 14.526 + np.log(pw) + 0.7389 * np.log(pw)**2 + 0.09486 * np.log(pw)**3 + 0.4569 * pw**0.1984
    else:
        epw_dewpt_fut = 6.09 + 12.608 * np.log(pw) + 0.4959 * np.log(pw)**2
    return epw_dewpt_fut