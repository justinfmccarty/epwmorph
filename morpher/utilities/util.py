# coding=utf-8
"""
General utilities
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
from math import radians, cos, sin, asin, sqrt
import metpy.calc as mpcalc
from metpy.units import units

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
    return (rh * calc_sat_pr(pressure, dbt, rel_hum)) / 1000



